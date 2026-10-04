from copy import deepcopy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

import psutil

from individual.bridge import ROOT
from supervisor.supervisor import DEFAULT_LIMITS, Supervisor, load_limits


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.limits = {**DEFAULT_LIMITS, 'sample_interval_seconds': 0.05,
                       'shutdown_grace_seconds': 0.3, 'heartbeat_timeout_seconds': 5}

    def supervisor(self, mode='normal', **limits):
        supervisor = Supervisor(Path(self.temp.name) / 'fixture.db', {**self.limits, **limits}, log=lambda _: None)
        self.addCleanup(supervisor.close)
        supervisor.start(command=[sys.executable, '-u', str(ROOT / 'tests/fixtures/core_child.py'), mode])
        return supervisor

    def audit_types(self, supervisor):
        with closing(sqlite3.connect(supervisor._audit_path)) as connection:
            return {kind for (kind,) in connection.execute('SELECT event_type FROM supervisor_events')}

    def test_supervisor_independently_pauses_resumes_and_terminates(self):
        supervisor = self.supervisor()
        errors = []
        def wait_status(status):
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if (supervisor.status()['heartbeat'] or {}).get('status') == status:
                    return
                time.sleep(0.02)
            raise AssertionError(f'Missing {status} acknowledgment')
        def control():
            try:
                wait_status('running')
                supervisor.control('pause')
                wait_status('paused')
                supervisor.control('resume')
                wait_status('running')
            except Exception as error:
                errors.append(error)
            finally:
                supervisor.control('terminate')
        worker = threading.Thread(target=control, daemon=True)
        worker.start()
        self.assertEqual(supervisor.run(duration=5), 0)
        worker.join(timeout=1)
        self.assertFalse(errors)
        self.assertIsNotNone(supervisor.status()['bridge_pid'])
        self.assertFalse(psutil.pid_exists(supervisor.status()['bridge_pid']))
        self.assertTrue({'MANUAL_CONTROL', 'RESOURCE_SAMPLE', 'CORE_STOPPED'} <= self.audit_types(supervisor))

    def test_supervisor_forces_termination_when_core_ignores_control(self):
        supervisor = self.supervisor('ignore')
        def stop():
            deadline = time.monotonic() + 3
            while not supervisor.status()['bridge_pid'] and time.monotonic() < deadline:
                time.sleep(0.02)
            supervisor.control('terminate')
        threading.Thread(target=stop, daemon=True).start()
        supervisor.run(duration=4)
        self.assertIsNotNone(supervisor.process.poll())
        self.assertIn('FORCED_TERMINATION', self.audit_types(supervisor))
        self.assertFalse(psutil.pid_exists(supervisor.status()['bridge_pid']))

    def test_external_ram_limit_is_enforced(self):
        supervisor = self.supervisor(max_core_ram_mb=0.001)
        self.assertNotEqual(supervisor.run(duration=3), 0)
        self.assertEqual(supervisor.status()['stop_reason'], 'core_ram_limit')

    def test_external_storage_limit_stops_without_pruning_or_expanding_capacity(self):
        supervisor = self.supervisor(max_lifetime_storage_mb=0.001)
        original = deepcopy(supervisor.limits)
        sentinel = supervisor.database
        sentinel.write_bytes(b'history remains')
        self.assertNotEqual(supervisor.run(duration=3), 0)
        self.assertEqual(supervisor.status()['stop_reason'], 'lifetime_storage_limit')
        self.assertEqual(supervisor.limits, original)
        self.assertEqual(sentinel.read_bytes(), b'history remains')

    def test_bridge_exit_is_detected_independently(self):
        supervisor = self.supervisor('bridge_exit')
        self.assertNotEqual(supervisor.run(duration=3), 0)
        self.assertEqual(supervisor.status()['stop_reason'], 'bridge_process_exited')

    def test_core_telemetry_cannot_change_external_limits(self):
        supervisor = self.supervisor()
        original = deepcopy(supervisor.limits)
        supervisor.run(duration=0.7)
        self.assertEqual(supervisor.limits, original)
        self.assertIn('IGNORED_CORE_OUTPUT', self.audit_types(supervisor))
        with self.assertRaises(ValueError):
            supervisor.control('set_limits')

    def test_invalid_limits_fail_before_a_starts(self):
        path = Path(self.temp.name) / 'limits.yaml'
        path.write_text('max_core_ram_mb: -1\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            load_limits(path)

