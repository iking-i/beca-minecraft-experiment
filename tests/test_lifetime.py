from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from individual.bridge import ROOT, MinecraftBridge
from individual.core import ACore
from individual.events import EventStore, SCHEMA, encode
from individual.experiment_audit import audit
from individual.identity import ExperimentInUse
from individual.inspect import verify
from individual.lifetime import fork_snapshot, history_summary, resolve_runtime_database, initialize_lifetime
from individual.state import AState, utc_now
from tests.test_core import FakeBridge
from tests.test_structure import observation


class LifetimeTests(unittest.TestCase):
    def setUp(self):
        directory = ROOT / '.test-tmp'
        directory.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'lifetime.db'
        self.cores = []
        self.addCleanup(self.close_cores)

    def close_cores(self):
        for core in reversed(self.cores):
            core.shutdown()

    def core(self):
        core = ACore(self.path, FakeBridge(), initialize_lifetime=True)
        self.cores.append(core)
        return core

    def rows(self, query, arguments=()):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute(query, arguments).fetchall()

    def form_structure(self, core):
        for x in (0, 1, 2, 3):
            core.accept_observation(observation(x))
        self.assertTrue(core.state.internal_state['active_processes'])

    def snapshot(self, core, version=None):
        return core._store.save_snapshot(version, 'test boundary')

    def test_restart_keeps_identity_global_versions_internal_state_and_provenance(self):
        core = self.core()
        self.form_structure(core)
        core.execute_discrete_action()
        core.shutdown('parameter_adjustment')
        old = core.state
        resumed = self.core()
        self.assertEqual(resumed.state.individual_id, old.individual_id)
        self.assertEqual(resumed.state.started_at, old.started_at)
        self.assertEqual(resumed.state.state_version, old.state_version + 1)
        self.assertEqual(resumed.state.environment_sequence, old.environment_sequence)
        self.assertEqual(encode(resumed.state.internal_state), encode(old.internal_state))
        self.assertNotEqual(resumed.state.session_id, old.session_id)
        with self.assertRaises(RuntimeError):
            resumed.execute_discrete_action()  # Old observation cannot select a new body's action.
        resumed.accept_observation(observation(100))
        self.assertEqual(resumed.state.individual_id, old.individual_id)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE event_type='INDIVIDUAL_STARTED'")[0][0], 1)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE event_type='POLICY_REGISTRY_INITIALIZED'")[0][0], 1)
        self.assertTrue(verify(self.path)['valid_state_chain'])

    def test_three_sessions_keep_one_lifetime_without_reinitializing_policy(self):
        core = self.core()
        self.form_structure(core)
        marker, started = core.state.individual_id, core.state.started_at
        pids = set(core.state.internal_state['active_processes'])
        versions = [core.state.state_version]
        for label in ('server restart', 'environment switch'):
            core.end_session(label)
            internal = deepcopy(core.state.internal_state)
            core.accept_resources({'pressure': .1})  # Lifetime continues between sessions.
            core.begin_session({'world': label}, label)
            self.assertEqual(core.state.individual_id, marker)
            self.assertEqual(core.state.started_at, started)
            self.assertEqual(set(core.state.internal_state['active_processes']), pids)
            self.assertEqual(core.state.internal_state['generation_parameters'], internal['generation_parameters'])
            versions.append(core.state.state_version)
        self.assertEqual(versions, sorted(set(versions)))
        result = history_summary(self.path)
        self.assertEqual(len(result['Experiment_session_history']), 3)
        self.assertEqual(result['A_lifetime_history']['individual_id'], marker)
        self.assertTrue(verify(self.path)['valid_state_chain'])

    def test_session_boundary_does_not_create_a_false_temporal_experience_or_delete_processes(self):
        core = self.core()
        self.form_structure(core)
        core.execute_discrete_action()
        pids = set(core.state.internal_state['active_processes'])
        before = self.rows("SELECT COUNT(*) FROM events WHERE event_type='EXPERIENCE_FORMED'")[0][0]
        core.end_session('world changed')
        with self.assertRaises(RuntimeError):
            core.accept_observation(observation(80))
        core.begin_session({'world': 'other'})
        core.accept_observation(observation(80))
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE event_type='EXPERIENCE_FORMED'")[0][0], before)
        self.assertEqual(set(core.state.internal_state['active_processes']), pids)
        self.assertTrue(all(p['status'] == 'PAUSED' for p in core.state.internal_state['active_processes'].values()))
        self.assertFalse(core.state.observation_frame['delta']['after_action_ids'])
        self.assertTrue(core.state.observation_frame['delta']['sample_gap'])

    def test_crash_recovery_records_interruption_without_new_identity_or_version_reset(self):
        core = self.core()
        self.form_structure(core)
        original = core.state
        # Simulate lost carrier after its last committed transaction, without graceful end.
        core._closed = True
        core._store.close()
        core._lease.release()
        resumed = self.core()
        self.assertEqual(resumed.state.individual_id, original.individual_id)
        self.assertEqual(resumed.state.state_version, original.state_version + 2)
        self.assertEqual(encode(resumed.state.internal_state), encode(original.internal_state))
        self.assertEqual(self.rows('SELECT interrupted FROM session_ends WHERE session_id=?', (original.session_id,)), [(1,)])
        payload = json.loads(self.rows("SELECT payload FROM events WHERE event_type='SESSION_INTERRUPTED'")[0][0])
        self.assertIs(payload['physical_continuity_proven'], False)
        self.assertTrue(verify(self.path)['valid_state_chain'])

    def test_second_runtime_cannot_interrupt_the_active_session(self):
        core = self.core()
        before = history_summary(self.path)
        with self.assertRaises(ExperimentInUse):
            self.core()
        self.assertEqual(before, history_summary(self.path))
        self.assertEqual(core.state.state_version, 0)

    def test_snapshot_is_exact_immutable_and_does_not_change_running_A(self):
        core = self.core()
        self.form_structure(core)
        before = core.state
        other_store = EventStore(self.path)
        try:
            sid = other_store.save_snapshot(before.state_version - 1)
        finally:
            other_store.close()
        digest, raw, version = self.rows('SELECT snapshot_hash,snapshot,state_version FROM snapshots WHERE snapshot_id=?', (sid,))[0]
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), digest)
        self.assertEqual(raw, self.rows('SELECT snapshot FROM states WHERE state_version=?', (version,))[0][0])
        self.assertEqual(core.state, before)
        core.end_session('immutability check')
        with closing(sqlite3.connect(self.path)) as db:
            for table in ('snapshots', 'sessions', 'session_ends', 'state_sessions', 'individual_lifetime'):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(f'DELETE FROM {table}')

    def test_snapshot_branch_has_distinct_identity_and_exact_accessible_parent_provenance(self):
        core = self.core()
        self.form_structure(core)
        parent = core.state
        snapshot_id = self.snapshot(core)
        branch = Path(self.temp.name) / 'branch.db'
        result = fork_snapshot(self.path, snapshot_id, branch)
        self.assertNotEqual(result['branch_individual_id'], parent.individual_id)
        self.assertIs(result['original_mainline'], False)
        with closing(sqlite3.connect(branch)) as db:
            state = json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=0').fetchone()[0])
            self.assertEqual(encode(state['internal_state']), encode(parent.internal_state))
            for event_id, raw in self.rows('SELECT event_id,payload FROM events WHERE state_version<=?', (parent.state_version,)):
                preserved = db.execute("SELECT record FROM origin_history WHERE kind='events' AND owner_id=? AND record_id=?", (parent.individual_id, event_id)).fetchone()[0]
                self.assertEqual(json.loads(preserved)['payload'], raw)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM origin_history')
        self.assertTrue(verify(branch)['valid_state_chain'])
        self.assertEqual(history_summary(branch)['A_lifetime_history']['role'], 'snapshot_branch')
        self.assertEqual(core.state, parent)
        forked = ACore(branch, FakeBridge())
        try:
            self.assertEqual(forked.state.state_version, 1)
            forked.accept_observation(observation(10))
            self.assertTrue(verify(branch)['valid_state_chain'])
        finally:
            forked.shutdown()
        self.assertEqual(core.state, parent)

    def test_nested_snapshot_branch_retains_ancestor_history(self):
        core = self.core()
        self.form_structure(core)
        sid = self.snapshot(core)
        branch = Path(self.temp.name) / 'branch.db'
        fork_snapshot(self.path, sid, branch)
        store = EventStore(branch)
        try:
            second_sid = store.save_snapshot(0)
        finally:
            store.close()
        nested = Path(self.temp.name) / 'nested.db'
        fork_snapshot(branch, second_sid, nested)
        with closing(sqlite3.connect(nested)) as db:
            owners = {row[0] for row in db.execute('SELECT DISTINCT owner_id FROM origin_history')}
        self.assertEqual(len(owners), 2)
        self.assertTrue(verify(nested)['valid_state_chain'])

    def test_branch_creation_never_overwrites_existing_source_or_destination(self):
        core = self.core()
        sid = self.snapshot(core)
        before = core.state
        for output in (self.path, Path(self.temp.name) / 'occupied.db'):
            if output != self.path:
                output.write_bytes(b'keep')
            with self.assertRaises(ValueError):
                fork_snapshot(self.path, sid, output)
        missing = Path(self.temp.name) / 'missing.db'
        with self.assertRaises(ValueError):
            fork_snapshot(self.path, 'not-a-snapshot', missing)
        self.assertFalse(missing.exists())
        self.assertEqual(core.state, before)

    def test_pinned_runtime_rejects_fresh_database_missing_history_and_identity_replacement(self):
        core = self.core()
        config = Path(self.temp.name) / 'registry.json'
        config.write_text(json.dumps({'database': str(self.path), 'individual_id': core.state.individual_id}), encoding='utf-8')
        self.assertEqual(resolve_runtime_database(config=config), self.path)
        fresh = Path(self.temp.name) / 'session002.db'
        with self.assertRaises(ValueError):
            resolve_runtime_database(fresh, config=config)
        self.assertFalse(fresh.exists())
        with self.assertRaises(ValueError):
            resolve_runtime_database(branch_database=self.path, config=config)
        sid = self.snapshot(core)
        branch = Path(self.temp.name) / 'branch.db'
        fork_snapshot(self.path, sid, branch)
        self.assertEqual(resolve_runtime_database(branch_database=branch, config=config), branch)
        config.write_text(json.dumps({'database': str(self.path), 'individual_id': 'A-other'}), encoding='utf-8')
        with self.assertRaises(ValueError):
            resolve_runtime_database(config=config)
        config.write_text(json.dumps({'database': str(fresh), 'individual_id': core.state.individual_id}), encoding='utf-8')
        with self.assertRaises(ValueError):
            resolve_runtime_database(config=config)
        self.assertFalse(fresh.exists())

    def test_new_session_audit_does_not_pass_using_old_lifetime_evidence(self):
        core = self.core()
        for x in (0, 0, 0, 0, 1, 0, 0, 1):
            core.accept_observation(observation(x))
        self.assertTrue(audit(self.path)['closed_loop_observed'])
        core.end_session('parameter adjustment')
        core.begin_session()
        result = audit(self.path, session_id='latest')
        self.assertEqual(result['audit_scope'], 'session')
        self.assertFalse(result['closed_loop_observed'])
        self.assertEqual(result['counts'], {})
        self.assertEqual(result['session_id'], core.state.session_id)
        self.assertTrue(audit(self.path)['closed_loop_observed'])

    def test_legacy_import_preserves_exact_state_and_event_bytes(self):
        now = utc_now()
        state = AState('A-legacy', 0, now, now, status='stopped')
        value = state.to_dict()
        value.pop('session_id'); value.pop('carrier_epoch')
        raw = encode(value)
        event = encode({'from_version': None, 'to_version': 0, 'state': value})
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(SCHEMA)
            db.execute('INSERT INTO experiment VALUES(1,?,?,1)', (state.individual_id, now))
            db.execute('INSERT INTO states VALUES(0,?,?,?)', (state.individual_id, now, raw))
            db.execute('INSERT INTO events VALUES(1,?,?,?,?,?,?)', ('event0', now, state.individual_id, 0, 'STATE_UPDATED', event))
            db.commit()
        store = EventStore(self.path)
        try:
            self.assertEqual(store.connection.execute('SELECT snapshot FROM states').fetchone()[0], raw)
            self.assertEqual(store.connection.execute('SELECT payload FROM events').fetchone()[0], event)
            state = store.open_session({'world': 'new'})
            self.assertEqual(state.individual_id, 'A-legacy')
            self.assertEqual(state.state_version, 1)
            self.assertEqual(len(history_summary(self.path)['Experiment_session_history']), 2)
        finally:
            store.close()
        self.assertTrue(verify(self.path)['valid_state_chain'])

    def test_real_node_transport_across_two_sessions_keeps_lifetime(self):
        previous = None
        for _ in range(2):
            bridge = MinecraftBridge(ROOT / 'minecraft/config.json', adapter=ROOT / 'tests/fixtures/body.js', timeout=5)
            core = ACore(self.path, bridge, session_context={'environment_type': 'node_body_fixture'}, initialize_lifetime=True)
            self.cores.append(core)
            if previous:
                self.assertEqual(core.state.individual_id, previous.individual_id)
                self.assertEqual(core.state.state_version, previous.state_version + 1)
                self.assertEqual(encode(core.state.internal_state), encode(previous.internal_state))
            core.start()
            deadline = time.monotonic() + 5
            start_sequence = core.state.environment_sequence
            while core.state.environment_sequence < start_sequence + 2:
                self.assertLess(time.monotonic(), deadline)
                core.tick()
                time.sleep(.02)
            core.shutdown('node_session_finished')
            previous = core.state
            self.assertIsNotNone(bridge.process.poll())
        summary = verify(self.path)
        self.assertTrue(summary['valid_state_chain'])
        self.assertEqual(len(summary['Experiment_session_history']), 2)

    def test_normal_core_cannot_create_a_replacement_lifetime(self):
        with self.assertRaises(ValueError):
            ACore(self.path, FakeBridge())
        self.assertFalse(self.path.exists())
        self.path.touch()
        with self.assertRaises(ValueError):
            ACore(self.path, FakeBridge())
        self.assertEqual(self.rows('SELECT COUNT(*) FROM experiment')[0][0], 0)

    def test_explicit_one_time_registration_is_separate_from_first_and_future_sessions(self):
        registration = initialize_lifetime(self.path)
        self.assertEqual(registration['state_version'], 0)
        self.assertFalse(registration['runtime_started'])
        self.assertEqual(history_summary(self.path)['Experiment_session_history'], [])
        with self.assertRaises(FileExistsError):
            initialize_lifetime(self.path)
        core = ACore(self.path, FakeBridge())
        self.cores.append(core)
        self.assertEqual(core.state.individual_id, registration['individual_id'])
        self.assertEqual(core.state.state_version, 1)
        payload = json.loads(self.rows("SELECT payload FROM events WHERE event_type='SESSION_STARTED'")[0][0])
        self.assertFalse(payload['carrier_restart'])
        core.shutdown()
        resumed = ACore(self.path, FakeBridge())
        self.cores.append(resumed)
        self.assertEqual(resumed.state.individual_id, registration['individual_id'])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE event_type='INDIVIDUAL_STARTED'")[0][0], 1)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE event_type='POLICY_REGISTRY_INITIALIZED'")[0][0], 1)
        self.assertTrue(verify(self.path)['valid_state_chain'])


if __name__ == '__main__':
    unittest.main()
