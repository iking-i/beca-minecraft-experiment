from copy import deepcopy
from contextlib import closing
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

from individual.bridge import BridgeError, MinecraftBridge, ROOT
from individual.core import ACore
from individual.identity import ExperimentInUse
from individual.inspect import verify
from individual.policy import DeterministicPolicy
from individual.state import utc_now


class FakeBridge:
    def __init__(self):
        self.alive = False
        self.pid = 1234
        self.position = {'x': 0.0, 'y': 64.0, 'z': 0.0}
        self.events = []
        self.calls = []
        self.failure = None

    def launch(self):
        self.alive = True

    def call(self, method, args=None):
        self.calls.append((method, deepcopy(args)))
        if method == 'start':
            self.events.append({'kind': 'lifecycle', 'status': {'state': 'ready', 'connected': True, 'attempt': 1, 'lastError': None}})
            return {'state': 'ready'}
        if method == 'observe':
            return {'timestamp': utc_now(), 'position': deepcopy(self.position), 'health': 20,
                    'hunger': 18, 'inventory': [{'name': 'dirt', 'count': 3}, {'name': 'dirt', 'count': 2}]}
        if self.failure:
            raise self.failure
        if method == 'move' and args['direction'] == 'forward':
            self.position['x'] += 0.25
        return {'position': deepcopy(self.position)}

    def drain_events(self):
        result, self.events = self.events, []
        return result

    def close(self):
        self.alive = False


class CoreTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / 'beca.db'
        self.bridge = FakeBridge()
        self.core = ACore(self.database, self.bridge, DeterministicPolicy(wait_seconds=100), initialize_lifetime=True)
        self.addCleanup(self.core.shutdown)

    def rows(self, sql, values=()):
        with closing(sqlite3.connect(self.database)) as connection:
            return connection.execute(sql, values).fetchall()

    def connect(self):
        self.core.start()
        self.core.tick(time.monotonic())

    def test_one_individual_and_cross_process_experiment_lock(self):
        initial_id = self.core.state.individual_id
        with self.assertRaises(ExperimentInUse):
            ACore(self.database, FakeBridge())
        command = ['-c', 'from individual.identity import ExperimentLease; import sys; ExperimentLease(sys.argv[1]).acquire()', str(self.database)]
        result = subprocess.run([sys.executable, *command], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ExperimentInUse', result.stderr)
        self.connect()
        self.assertEqual(self.core.state.individual_id, initial_id)
        self.assertEqual(len(self.rows('SELECT * FROM experiment')), 1)

    def test_observation_enters_state_and_every_input_increments_environment_sequence(self):
        self.connect()
        before = self.core.state
        self.core.accept_observation(self.bridge.call('observe'))
        after = self.core.state
        self.assertEqual(after.state_version, before.state_version + 1)
        self.assertEqual(after.environment_sequence, before.environment_sequence + 1)
        self.assertEqual(after.inventory_summary, [{'name': 'dirt', 'count': 5}])
        self.assertEqual(after.health, 20)
        self.assertEqual(after.hunger, 18)

    def test_action_bridge_world_observation_forms_a_closed_loop(self):
        self.connect()
        before = self.core.state
        self.assertTrue(self.core.execute_action({'method': 'move', 'args': {'direction': 'forward', 'durationMs': 200}}))
        self.assertIn(('move', {'direction': 'forward', 'durationMs': 200}), self.bridge.calls)
        self.core.accept_observation(self.bridge.call('observe'))
        after = self.core.state
        self.assertEqual(after.individual_id, before.individual_id)
        self.assertGreater(after.state_version, before.state_version)
        self.assertGreater(after.position['x'], before.position['x'])
        self.assertGreater(after.environment_sequence, before.environment_sequence)
        self.assertEqual(after.latest_action['status'], 'executed')

    def test_state_versions_are_contiguous_and_all_changes_have_atomic_events(self):
        self.connect()
        self.core.accept_observation(self.bridge.call('observe'))
        states = self.rows('SELECT state_version FROM states ORDER BY state_version')
        self.assertEqual([version for (version,) in states], list(range(len(states))))
        count = self.rows("SELECT COUNT(*) FROM events WHERE event_type='STATE_UPDATED'")[0][0]
        self.assertEqual(count, len(states))
        self.assertTrue(verify(self.database)['valid_state_chain'])
        state = self.core.state
        with self.assertRaises(ValueError):
            self.core._store.transition(state, replace(state, state_version=state.state_version), 'BAD', {})

    def test_database_rejects_history_update_and_delete(self):
        for table in ('states', 'events', 'experiment'):
            with self.subTest(table=table), closing(sqlite3.connect(self.database)) as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(f'DELETE FROM {table}')
        with closing(sqlite3.connect(self.database)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute('UPDATE states SET state_version=100')

    def test_failed_event_serialization_rolls_back_before_any_action(self):
        self.connect()
        before = self.core.state
        calls = len(self.bridge.calls)
        with self.assertRaises(ValueError):
            self.core.execute_action({'method': 'move', 'args': {'durationMs': float('nan')}})
        self.assertEqual(self.core.state, before)
        self.assertEqual(len(self.bridge.calls), calls)
        self.assertTrue(verify(self.database)['valid_state_chain'])

    def test_death_and_respawn_keep_individual_id(self):
        self.connect()
        individual_id = self.core.state.individual_id
        self.core.accept_bridge_status({'state': 'dead', 'connected': False, 'attempt': 1})
        self.core.accept_bridge_status({'state': 'spawning', 'connected': False, 'attempt': 1})
        self.core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 1})
        self.assertEqual(self.core.state.individual_id, individual_id)
        types = {kind for (kind,) in self.rows('SELECT event_type FROM events')}
        self.assertTrue({'BODY_DIED', 'BODY_RESPAWNED'} <= types)

    def test_bridge_disconnect_reconnect_keep_individual_id(self):
        self.connect()
        individual_id = self.core.state.individual_id
        self.core.accept_bridge_status({'state': 'reconnecting', 'connected': False, 'attempt': 1})
        self.core.accept_bridge_status({'state': 'connecting', 'connected': False, 'attempt': 2})
        self.core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 2})
        self.assertEqual(self.core.state.individual_id, individual_id)
        types = {kind for (kind,) in self.rows('SELECT event_type FROM events')}
        self.assertTrue({'BRIDGE_DISCONNECTED', 'BRIDGE_RECONNECTED'} <= types)

    def test_core_public_actions_cannot_modify_supervisor(self):
        before = self.core.state
        for method in ('set_limits', 'write_file', 'modify_supervisor', 'close', 'constructor'):
            with self.assertRaises(ValueError):
                self.core.execute_action({'method': method, 'args': {}})
        self.assertEqual(self.core.state, before)
        self.assertFalse(hasattr(self.core, 'supervisor'))
        self.assertFalse(hasattr(self.core, 'set_limits'))

    def test_detached_state_and_invalid_observation_cannot_mutate_core(self):
        self.connect()
        snapshot = self.core.state
        snapshot.latest_observation['position']['x'] = 999
        self.assertEqual(self.core.state.position['x'], 0)
        before = self.core.state
        with self.assertRaises(ValueError):
            self.core.accept_observation({'position': {'x': float('inf')}})
        self.assertEqual(self.core.state, before)

    def test_pause_prevents_new_policy_actions_but_preserves_observation_chain(self):
        self.connect()
        individual_id = self.core.state.individual_id
        self.core.pause()
        before = self.core.state.environment_sequence
        self.core.accept_observation(self.bridge.call('observe'))
        self.assertEqual(self.core.state.status, 'paused')
        self.assertGreater(self.core.state.environment_sequence, before)
        with self.assertRaises(RuntimeError):
            self.core.execute_action({'method': 'move', 'args': {'direction': 'forward'}})
        self.core.resume()
        self.assertEqual(self.core.state.individual_id, individual_id)
        self.assertEqual(self.core.state.status, 'running')

    def test_failed_action_is_recorded_and_never_automatically_replayed(self):
        self.core._policy = DeterministicPolicy(wait_seconds=0)
        self.bridge.failure = BridgeError('DISCONNECTED', 'test disconnect')
        self.connect()
        for _ in range(3):
            self.core.tick(time.monotonic())
        self.assertEqual(self.core.state.latest_action['status'], 'failed')
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE event_type='ACTION_FAILED'")[0][0], 1)
        self.assertEqual(len([call for call in self.bridge.calls if call[0] == 'move']), 1)

    def test_existing_lifetime_is_resumed_after_session_stop(self):
        original_id = self.core.state.individual_id
        self.core.shutdown()
        last_version = self.core.state.state_version
        resumed = ACore(self.database, FakeBridge())
        try:
            self.assertEqual(resumed.state.individual_id, original_id)
            self.assertEqual(resumed.state.state_version, last_version + 1)
        finally:
            resumed.shutdown()
        self.assertEqual(verify(self.database)['individual_id'], original_id)
        final = json.loads(self.rows('SELECT snapshot FROM states ORDER BY state_version DESC LIMIT 1')[0][0])
        self.assertEqual(final['status'], 'dormant')

    def test_bridge_process_exit_terminates_instead_of_recreating_a(self):
        self.connect()
        self.bridge.alive = False
        self.bridge.events.append({'kind': 'exited'})
        with self.assertRaises(BridgeError):
            self.core.tick()
        self.assertIn(('BRIDGE_DISCONNECTED',), self.rows('SELECT event_type FROM events'))


class NodeProcessIntegrationTests(unittest.TestCase):
    def test_python_core_uses_real_node_adapter_and_records_world_feedback(self):
        parent = ROOT / '.test-tmp'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            database = Path(directory) / 'beca.db'
            bridge = MinecraftBridge(ROOT / 'minecraft/config.json', adapter=ROOT / 'tests/fixtures/body.js', timeout=5)
            core = ACore(database, bridge, DeterministicPolicy(wait_seconds=0), initialize_lifetime=True)
            try:
                core.start()
                deadline = time.monotonic() + 5
                while core.state.environment_sequence < 3:
                    self.assertLess(time.monotonic(), deadline)
                    core.tick()
                    time.sleep(0.05)
                self.assertEqual(core.state.position['x'], 0.25)
                self.assertEqual(core.state.latest_action['args']['direction'], 'stop')
                with self.assertRaises(BridgeError):
                    bridge.call('set_limits', {'value': 999})
                self.assertTrue(verify(database)['valid_state_chain'])
            finally:
                core.shutdown()
            self.assertIsNotNone(bridge.process.poll())

