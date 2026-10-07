"""Non-A subprocess controls. No Minecraft, body RPC or experimental DB writes."""
from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import psutil

from supervisor.process_evidence import StreamCapture
from supervisor.supervisor import Supervisor, DEFAULT_LIMITS


HEADER = """
import json,sys,time
print(json.dumps({'kind':'CORE_STARTED','individual_id':'NON_A_FIXTURE','session_id':'FIXTURE_SESSION','state_version':17}),flush=True)
print(json.dumps({'kind':'HEARTBEAT','individual_id':'NON_A_FIXTURE','session_id':'FIXTURE_SESSION','state_version':17,'status':'running'}),flush=True)
"""


class ProcessEvidenceTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(self.temp.cleanup)

    def start(self, script):
        sup = Supervisor(Path(self.temp.name) / 'non-A.db', {**DEFAULT_LIMITS,
            'sample_interval_seconds': .02, 'shutdown_grace_seconds': .2,
            'heartbeat_timeout_seconds': 5}, log=lambda _: None)
        self.addCleanup(sup.close)
        sup.start(command=[sys.executable, '-u', '-c', HEADER + script])
        return sup

    def records(self, sup, kind):
        with closing(sqlite3.connect(sup._audit_path)) as db:
            return [json.loads(r[0]) for r in db.execute(
                'SELECT payload FROM supervisor_events WHERE event_type=? ORDER BY sequence', (kind,))]

    def test_normal_core_exit_identity_code_time_and_final_context(self):
        sup = self.start('time.sleep(.1)')
        self.assertEqual(sup.run(), 0)
        record = next(x for x in self.records(sup, 'PROCESS_EXIT_OBSERVED') if x['pid'] == sup.process.pid)
        self.assertEqual((record['role'], record['exit_code'], record['exit_class']), ('Core', 0, 'NORMAL_EXIT'))
        self.assertTrue(record['observed_at'])
        self.assertFalse(record['supervisor_termination_requested'])
        final = self.records(sup, 'OUTPUT_CAPTURE_FINAL')[-1]
        self.assertEqual((final['individual_id'], final['session_id'], final['state_version']),
                         ('NON_A_FIXTURE', 'FIXTURE_SESSION', 17))
        self.assertTrue(final['last_heartbeat'])
        self.assertTrue(final['last_resource_sample'])
        self.assertFalse(sup.database.exists())  # No fake SESSION_ENDED / EventStore.

    def test_nonzero_core_exit_full_stderr_traceback_and_bounded_tail(self):
        sup = self.start("time.sleep(.1); raise RuntimeError('non-A crash witness')")
        self.assertNotEqual(sup.run(), 0)
        record = next(x for x in self.records(sup, 'PROCESS_EXIT_OBSERVED') if x['pid'] == sup.process.pid)
        self.assertEqual(record['exit_code'], 1)
        self.assertEqual(record['termination_origin'], 'SPONTANEOUS_PROCESS_EXIT')
        final = self.records(sup, 'OUTPUT_CAPTURE_FINAL')[-1]
        self.assertIn('Traceback', Path(final['stderr']['path']).read_text(encoding='utf8'))
        self.assertIn('non-A crash witness', final['stderr']['tail'])
        self.assertLessEqual(len(final['stderr']['tail']), 8192)

    def test_bridge_exit_is_distinct_and_keeps_forwarded_stderr(self):
        sup = self.start("""
import subprocess,threading
p=subprocess.Popen(['node','-e',"setTimeout(()=>{console.error('bridge crash witness');process.exit(7)},500);setInterval(()=>{},1000)"],stderr=subprocess.PIPE,text=True)
print(json.dumps({'kind':'BRIDGE_STARTED','pid':p.pid}),flush=True)
def forward():
 for line in p.stderr: print(line,end='',file=sys.stderr,flush=True)
threading.Thread(target=forward,daemon=True).start()
for line in sys.stdin:
 if json.loads(line)['command']=='terminate': break
p.wait(timeout=3)
""")
        sup.run(duration=4)
        exits = self.records(sup, 'PROCESS_EXIT_OBSERVED')
        bridge = next(x for x in exits if x['role'] == 'Bridge')
        core = next(x for x in exits if x['pid'] == sup.process.pid)
        self.assertNotEqual(bridge['pid'], core['pid'])
        self.assertEqual(bridge['termination_origin'], 'SPONTANEOUS_PROCESS_EXIT')
        if os.name == 'nt':
            self.assertEqual(bridge['exit_code'], 7)
            self.assertEqual(bridge['exit_time_kind'], 'kernel')
        self.assertEqual(bridge['first_observed_exit']['pid'], bridge['pid'])
        self.assertEqual(sup._stop_reason, 'bridge_process_exited')
        final = self.records(sup, 'OUTPUT_CAPTURE_FINAL')[-1]
        self.assertIn('bridge crash witness', Path(final['stderr']['path']).read_text(encoding='utf8'))

    def test_disappeared_child_cpu_probe_does_not_abort_monitor(self):
        sup = self.start('time.sleep(.25)')
        fake = SimpleNamespace(pid=2000000000, is_running=lambda: False,
            cpu_percent=lambda **_: (_ for _ in ()).throw(psutil.NoSuchProcess(2000000000)),
            cmdline=lambda: (_ for _ in ()).throw(psutil.NoSuchProcess(2000000000)),
            wait=lambda **_: None)
        with patch.object(sup._core, 'children', return_value=[fake]):
            self.assertEqual(sup.run(), 0)
        self.assertTrue(self.records(sup, 'PROCESS_QUERY_DISAPPEARED'))
        unknown = next(x for x in self.records(sup, 'PROCESS_EXIT_OBSERVED') if x['pid'] == fake.pid)
        self.assertIsNone(unknown['exit_code'])
        self.assertEqual(unknown['exit_class'], 'EXIT_REASON_UNKNOWN')
        self.assertFalse(self.records(sup, 'MONITOR_EXCEPTION'))
        self.assertTrue(self.records(sup, 'SUPERVISOR_STOPPED'))

    def test_supervisor_kill_is_not_spontaneous(self):
        sup = self.start('time.sleep(20)')
        sup.run(duration=.1)
        record = next(x for x in self.records(sup, 'PROCESS_EXIT_OBSERVED') if x['pid'] == sup.process.pid)
        self.assertEqual(record['termination_origin'], 'SUPERVISOR_INITIATED')
        self.assertEqual(record['supervisor_reason'], 'runtime_limit')
        self.assertTrue(record['supervisor_kill_request'])
        self.assertTrue(self.records(sup, 'PROCESS_KILL_REQUESTED'))

    def test_monitor_exception_persists_before_existing_cleanup(self):
        sup = self.start('time.sleep(20)')
        with patch.object(sup, '_collect', side_effect=RuntimeError('monitor fixture exception')):
            with self.assertRaisesRegex(RuntimeError, 'monitor fixture exception'):
                sup.run()
            sup.close()
        errors = self.records(sup, 'MONITOR_EXCEPTION')
        self.assertTrue(errors)
        self.assertIn('monitor fixture exception', Path(errors[0]['traceback_path']).read_text(encoding='utf8'))
        self.assertTrue(self.records(sup, 'SUPERVISOR_CLOSED'))
        self.assertTrue(self.records(sup, 'PROCESS_EXIT_OBSERVED'))
        self.assertFalse(sup.database.exists())

    def test_stream_capture_memory_is_bounded_full_file_is_preserved(self):
        capture = StreamCapture(Path(self.temp.name) / 'stream.log')
        try:
            for _ in range(100):
                capture.append('x' * 10000)
            self.assertEqual(len(capture.snapshot()['tail']), 8192)
            self.assertEqual(capture.path.stat().st_size, 1000000)
        finally:
            capture.close()

    def test_access_denied_does_not_fabricate_exit(self):
        from supervisor.process_evidence import ProcessProbe
        fake = SimpleNamespace(pid=2000000000,
            is_running=lambda: (_ for _ in ()).throw(psutil.AccessDenied(2000000000)))
        probe = ProcessProbe(fake, 'worker')
        try:
            self.assertIsNone(probe.poll())
            self.assertFalse(probe.recorded)
        finally:
            probe.close()

    def test_worker_exit_role_and_nonchild_code_capture(self):
        sup = self.start("""
import subprocess
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(.4);raise RuntimeError("worker fixture")','integration.froi_worker'],stderr=subprocess.PIPE)
p.wait(timeout=3)
time.sleep(.1)
""")
        self.assertEqual(sup.run(), 0)
        worker = next(x for x in self.records(sup, 'PROCESS_EXIT_OBSERVED') if x['role'] == 'worker')
        if os.name == 'nt':
            self.assertEqual(worker['exit_code'], 1)
        self.assertEqual(worker['stderr_scope'], 'parent_private_pipe_not_available_to_external_supervisor')

    def test_committed_state_context_read_is_external_and_read_only(self):
        sup = self.start('time.sleep(.25)')
        with closing(sqlite3.connect(sup.database)) as db:
            db.execute('CREATE TABLE states(state_version INTEGER,snapshot TEXT)')
            db.execute('INSERT INTO states VALUES(73,?)', (json.dumps({
                'individual_id': 'NON_A_SNAPSHOT', 'session_id': 'SNAPSHOT_SESSION'}),))
            db.commit()
        before = sha256(sup.database.read_bytes()).hexdigest()
        self.assertEqual(sup.run(), 0)
        final = self.records(sup, 'OUTPUT_CAPTURE_FINAL')[-1]
        self.assertEqual((final['individual_id'], final['session_id'], final['state_version']),
                         ('NON_A_SNAPSHOT', 'SNAPSHOT_SESSION', 73))
        self.assertFalse(final['recursive_input'])
        self.assertEqual(before, sha256(sup.database.read_bytes()).hexdigest())
