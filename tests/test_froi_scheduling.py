"""Engineering isolation controls; not FROI-1 live T1--T5."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import psutil

from experimental.gsc0.engine import Caps
from individual.core import ACore
from individual.formal_l0 import FormalLimits
from integration.froi import consume, produce
from integration.froi_worker import JobSpec, Worker, execute, validate_result
from supervisor.supervisor import Supervisor, DEFAULT_LIMITS
from tests.test_core import FakeBridge
from tests.test_structure import observation


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(self.temp.cleanup)
        self.cores = []
        self.addCleanup(lambda: [c.shutdown() for c in self.cores])

    def core(self, mode=None, caps=None):
        factory = None if mode is None else lambda job: Worker(job,
            [sys.executable, '-m', 'tests.fixtures.froi_worker_hook', str(mode)])
        core = ACore(Path(self.temp.name)/f'{len(self.cores)}.db', FakeBridge(),
            initialize_lifetime=True, froi=True, froi_async=True, worker_factory=factory,
            froi_caps=caps, physical_caps=FormalLimits(history=100, evidence_window=100))
        self.cores.append(core)
        core._bridge.launch()
        core.accept_observation(observation())
        core.accept_observation(observation())
        core.accept_observation(observation())
        self.assertIsNotNone(core._computation)
        return core

    def finish(self, core):
        deadline = time.monotonic()+10
        while core._computation and time.monotonic()<deadline:
            core.tick()
            time.sleep(.01)
        self.assertIsNone(core._computation)

    def events(self, core, kind):
        return [json.loads(x[0]) for x in core._store.connection.execute(
            'select payload from events where event_type=? order by event_sequence', (kind,))]

    def test_one_inflight_and_raw_observation_freeze(self):
        core = self.core(2)
        before = core.state
        with self.assertRaisesRegex(RuntimeError, 'ONE_IN_FLIGHT'):
            core.accept_observation(observation(50))
        for _ in range(5):
            core.accept_resources({'test': True})
            core.tick()
        self.assertEqual(core.state, before)
        self.assertEqual(len(self.events(core, 'WORLD_OBSERVATION')), 2)

    def test_no_action_while_waiting_and_pause(self):
        core = self.core(2)
        calls = deepcopy(core._bridge.calls)
        before = core.state
        core.pause()
        core.tick()
        self.assertTrue(core._paused)
        with self.assertRaisesRegex(RuntimeError, 'No actions'):
            core.execute_discrete_action(1, {})
        self.assertEqual(core._bridge.calls, calls)
        self.assertEqual(core.state, before)
        core.resume()

    def test_complete_same_shared_portbind_consumer(self):
        core = self.core()
        job = core._computation['job']
        direct = execute(job)
        self.assertTrue(direct.handle.complete)
        expected = consume(direct.handle, direct.handle.request)
        self.finish(core)
        actual = self.events(core, 'FROI_ORGANIZATION_CONSUMED')[-1]
        self.assertEqual(actual['status'], expected.status)
        self.assertEqual(json.dumps(actual['consumed_keys']), json.dumps(expected.consumed_keys))
        self.assertEqual({k[0] for k in actual['consumed_keys']}, {'Shared', 'PortBind'})

    def test_resource_limit_returns_without_killing_core_and_reenters(self):
        core = self.core(caps=Caps(operations=1))
        self.finish(core)
        self.assertEqual(self.events(core,'FROI_ORGANIZATION_FORMED')[-1]['status'], 'RESOURCE_LIMIT')
        self.assertTrue(core._bridge.alive)
        self.assertTrue(core.state.internal_state['l0_state']['pending_consequences'])
        core.accept_observation(observation())
        self.finish(core)
        self.assertTrue(self.events(core, 'LIMIT_FEEDBACK_REENTERED_RECURSION'))

    def test_completed_pre_action_checkpoint_resumes_original_action_stage(self):
        core = self.core()
        core._bridge_status = {'connected': True, 'state': 'ready'}
        self.finish(core)
        order = []
        with patch.object(core, 'execute_discrete_action', side_effect=lambda: order.append('action')), \
             patch.object(core, '_observe', side_effect=lambda: order.append('observe')):
            core.tick()
        self.assertEqual(order, ['action', 'observe'])

    def test_invalid_has_no_legacy_fallback(self):
        core = self.core(2)
        core._cancel_computation('TEST_ONLY preparation')
        internal = deepcopy(core.state.internal_state)
        internal['l0_state']['feedback']['next_relation_ref'] = 'TEST_ONLY missing actual reference'
        core._transition('TEST_ONLY_INPUT_CORRUPTION', {}, internal_state=internal)
        core.accept_observation(observation())
        self.finish(core)
        formed = self.events(core, 'FROI_ORGANIZATION_FORMED')[-1]
        self.assertEqual(formed['status'], 'INVALID')
        consumed = self.events(core, 'FROI_ORGANIZATION_CONSUMED')[-1]
        self.assertEqual(consumed['status'], 'INVALID')
        self.assertFalse(consumed['consumed_keys'])
        self.assertTrue(core.state.internal_state['relations'])
        self.assertTrue(core.state.internal_state['l0_state']['pending_consequences'])

    def test_identity_every_field_and_handle_boundary(self):
        core = self.core(2)
        job = core._computation['job']
        result = execute(job)
        mutations = dict(individual_id='another',session_id='another',source_state_version=999,
            history=replace(job.history,event_cutoff=999),frame_json='{}',feedback_json='{}',
            caps_json='{}',origin_json='{}',codec_version='different',froi_version='different')
        for key,value in mutations.items():
            with self.subTest(field=key):
                self.assertEqual(validate_result(replace(job,**{key:value}),result),'STALE_RESULT')
        forged = replace(result, handle=replace(result.handle, history_cutoff=999))
        self.assertEqual(validate_result(job,forged),'STALE_RESULT')
        forged = replace(result, handle=replace(result.handle,
            condition=replace(result.handle.condition, nodes=())))
        self.assertEqual(validate_result(job,forged),'STALE_RESULT')

    def test_stale_result_never_consumed(self):
        core = self.core(.1)
        core._state = replace(core._state,state_version=core.state.state_version+1)
        # Corrupt detached checkpoint only, restore before audit persistence.
        original = core._state
        deadline=time.monotonic()+5
        while core._computation['worker'].poll() is None and time.monotonic()<deadline:
            time.sleep(.02)
        with patch.object(core, '_transition') as audit:
            with self.assertRaisesRegex(RuntimeError,'STALE_RESULT'):
                core.tick()
            self.assertEqual(audit.call_args.args[1]['execution_status'],'STALE_RESULT')
        core._state=replace(original,state_version=original.state_version-1)
        self.assertFalse(self.events(core,'FROI_ORGANIZATION_CONSUMED'))

    def test_worker_crash_is_not_gsc_resource_limit(self):
        core=self.core('crash')
        with self.assertRaisesRegex(RuntimeError,'WORKER_EXITED'):
            self.finish(core)
        self.assertEqual(self.events(core,'FROI_JOB_EXECUTION')[-1]['execution_status'],'WORKER_EXITED')
        self.assertFalse(self.events(core,'FROI_ORGANIZATION_FORMED'))

    def test_malformed_transport_is_worker_failed(self):
        core=self.core('malformed')
        with self.assertRaisesRegex(RuntimeError,'WORKER_FAILED'):
            self.finish(core)
        self.assertFalse(self.events(core,'FROI_ORGANIZATION_FORMED'))

    def test_cancel_kills_worker_no_partial(self):
        core=self.core(20)
        pid=core._computation['worker'].process.pid
        time.sleep(.3)
        children=psutil.Process(pid).children(recursive=True)
        core.shutdown('manual_terminate')
        self.assertFalse(psutil.pid_exists(pid))
        self.assertTrue(all(not c.is_running() for c in children))
        self.assertFalse(core._bridge.alive)
        db=sqlite3.connect(Path(self.temp.name)/'0.db')
        self.addCleanup(db.close)
        data=[json.loads(p) for p, in db.execute("select payload from events where event_type='FROI_JOB_EXECUTION'")]
        self.assertEqual(data[-1]['execution_status'],'CANCELLED')
        self.assertFalse(db.execute("select 1 from events where event_type='FROI_ORGANIZATION_FORMED'").fetchone())

    def test_actual_core_main_heartbeat_pause_termination_separate_accounting(self):
        # Same production Core.main loop and Supervisor, isolated fixture DB/body.
        core=self.core(20)
        database=core._store.path
        core.shutdown('TEST_ONLY seed preparation')
        limits={**DEFAULT_LIMITS,'sample_interval_seconds':.05,'heartbeat_timeout_seconds':3,
                'shutdown_grace_seconds':3}
        sup=Supervisor(database,limits,log=lambda _:None)
        self.addCleanup(sup.close)
        caps_path=Path(self.temp.name)/'caps.json'
        from dataclasses import asdict
        caps_path.write_text(json.dumps(asdict(core._engine.caps)),encoding='utf8')
        sup.start(command=[sys.executable,'-u','-m','tests.fixtures.froi_scheduling_core',
            '--db',str(database),'--froi','--physical-caps',str(caps_path.resolve())])
        errors=[]
        def control():
            try:
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    hb=sup.status()['heartbeat'] or {}
                    if hb.get('structure',{}).get('computation_wait'):
                        break
                    time.sleep(.02)
                else:
                    raise AssertionError('No frozen compute heartbeat')
                before = sup.status()['heartbeat']
                sup.control('pause')
                time.sleep(3.4)  # Exceeds heartbeat ceiling, far below slow worker delay.
                self.assertIsNone(sup._stop_reason)
                after = sup.status()['heartbeat']
                self.assertEqual(before['state_version'], after['state_version'])
                self.assertEqual(before['environment_sequence'], after['environment_sequence'])
                self.assertTrue(sup.status()['heartbeat']['structure']['manual_paused'])
                self.assertTrue(sup._sample['computation_worker']['alive'])
                self.assertTrue(sup._sample['core']['alive'])
                self.assertTrue(sup._sample['bridge']['alive'])
            except BaseException as error:
                errors.append(error)
            finally:
                sup.control('terminate')
        thread=threading.Thread(target=control,daemon=True);thread.start()
        self.assertEqual(sup.run(duration=12),0)
        thread.join(timeout=1)
        self.assertFalse(errors,errors)
        self.assertEqual(sup._stop_reason,'manual_terminate')
        self.assertTrue(all(not psutil.pid_exists(pid) for pid in sup._workers))
        db=sqlite3.connect(database)
        self.addCleanup(db.close)
        row=db.execute("select payload from events where event_type='FROI_JOB_EXECUTION' order by event_sequence desc limit 1").fetchone()
        self.assertEqual(json.loads(row[0])['execution_status'],'CANCELLED')
        audit=sqlite3.connect(sup._audit_path)
        self.addCleanup(audit.close)
        beats=[json.loads(p) for p, in audit.execute("select payload from supervisor_events where event_type='HEARTBEAT'")]
        waiting=[b for b in beats if b.get('structure',{}).get('computation_wait')]
        self.assertGreaterEqual(len(waiting),3)
        self.assertEqual(len({b['state_version'] for b in waiting}),1)

    def test_supervisor_host_budget_not_increased(self):
        sup=Supervisor(Path(self.temp.name)/'audit.db',dict(DEFAULT_LIMITS),log=lambda _:None)
        self.addCleanup(sup.close)
        with patch.object(sup,'_request_termination') as stop:
            sup._enforce({'core':{'ram_mb':400,'cpu_percent':0},
                'bridge':{'ram_mb':0,'cpu_percent':0,'alive':True},
                'computation_worker':{'ram_mb':150,'cpu_percent':0}})
            stop.assert_called_once_with('worker_host_ram_limit')
        self.assertEqual(sup.limits,DEFAULT_LIMITS)
