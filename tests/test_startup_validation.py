"""Startup infrastructure controls; all writable databases are isolated fixtures."""
from dataclasses import replace
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from individual.events import EventStore
from individual.identity import ExperimentInUse, ExperimentLease
from individual.inspect import verify
from individual.startup_validation import verify_startup_boundary
from individual.storage import create_lifetime, lifetime_entry, select_existing_lifetime
from launcher import LauncherService


class StartupValidationTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.storage, self.config = self.root/'individuals', self.root/'selected.json'
        self.fixture = create_lifetime(self.storage, self.config, 'TEST_ONLY startup')
        self.database = Path(self.fixture['database'])
        self.identity = self.fixture['individual_id']
        self.service = LauncherService(self.storage, self.config)

    def corrupt(self, sql, parameters=()):
        # Deliberately corrupt only this disposable fixture, never canonical history.
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('PRAGMA ignore_check_constraints=ON')
            for name, in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
                db.execute('DROP TRIGGER "' + name + '"')
            db.execute(sql, parameters)

    def test_list_never_calls_full_verify_or_history_summary(self):
        before = self.database.read_bytes()
        with patch('individual.inspect.verify', side_effect=AssertionError('Full audit forbidden')), \
             patch('individual.lifetime.history_summary', side_effect=AssertionError('History forbidden')):
            entries, rejected = self.service.entries()
        self.assertFalse(rejected)
        self.assertEqual(entries[0]['state_version'], 0)
        self.assertEqual(entries[0]['full_history_verification'], 'NOT_RUN')
        self.assertEqual(self.database.read_bytes(), before)

    def test_prepare_validates_current_boundary_once_and_never_full_history(self):
        before = self.database.read_bytes()
        with patch('individual.inspect.verify', side_effect=AssertionError('Full audit forbidden')), \
             patch('individual.startup_validation.verify_startup_boundary', wraps=verify_startup_boundary) as boundary:
            self.service.prepare(self.fixture['directory'], '12345', True)
        # One external invocation; the second is its read-only connection scope.
        self.assertEqual(sum(call.kwargs.get('connection') is None and len(call.args) == 2
                             for call in boundary.call_args_list), 1)
        self.assertEqual(self.database.read_bytes(), before)

    def test_identity_mismatch_blocks_prepare_without_switching_pin(self):
        self.corrupt('UPDATE experiment SET individual_id=?', ('A-wrong',))
        self.assert_prepare_rejected()

    def test_illegal_database_role_blocks_prepare(self):
        self.corrupt("UPDATE individual_lifetime SET role='snapshot_branch'")
        self.assert_prepare_rejected()

    def test_snapshot_of_another_individual_blocks_prepare(self):
        self.corrupt("UPDATE current_state SET snapshot=json_set(snapshot,'$.individual_id','A-wrong')")
        self.assert_prepare_rejected()

    def test_unparseable_snapshot_blocks_prepare(self):
        self.corrupt("UPDATE current_state SET snapshot='not JSON'")
        self.assert_prepare_rejected()

    def test_missing_required_current_metadata_blocks_prepare(self):
        self.corrupt("UPDATE current_state SET snapshot=json_remove(snapshot,'$.started_at')")
        self.assert_prepare_rejected()

    def test_continuity_metadata_blocks_prepare(self):
        self.corrupt("UPDATE current_state SET snapshot=json_set(snapshot,'$.continuity_required',json('false'))")
        self.assert_prepare_rejected()

    def test_latest_session_association_blocks_prepare(self):
        self.corrupt("UPDATE current_state SET snapshot=json_set(snapshot,'$.session_id','S-missing')")
        self.assert_prepare_rejected()

    def test_current_commit_metadata_blocks_prepare(self):
        self.corrupt("UPDATE current_state SET state_version=99")
        self.assert_prepare_rejected()

    def test_body_epoch_can_advance_inside_same_session(self):
        store = EventStore(self.database)
        try:
            state = store.open_session()
            later = replace(state, state_version=state.state_version + 1,
                            carrier_epoch=state.carrier_epoch + 1)
            store.transition(state, later, 'TEST_ONLY', {})
        finally:
            store.close()
        boundary = verify_startup_boundary(self.database, self.identity)
        self.assertEqual(boundary['session_id'], state.session_id)
        self.assertEqual(boundary['state_version'], later.state_version)

    def test_bad_current_pin_not_silently_repaired(self):
        pin = json.loads(self.config.read_text())
        pin['individual_id'] = 'A-wrong'
        self.config.write_text(json.dumps(pin))
        self.assert_prepare_rejected()

    def assert_prepare_rejected(self):
        before = self.config.read_bytes()
        with self.assertRaises(ValueError):
            self.service.prepare(self.fixture['directory'], '12345', True)
        self.assertEqual(self.config.read_bytes(), before)

    def test_caps_rejection_precedes_pointer_write(self):
        before = self.config.read_bytes()
        with patch('individual.startup_validation.preflight_current_caps', side_effect=ValueError('locked_caps')):
            with self.assertRaisesRegex(ValueError, 'locked_caps'):
                self.service.prepare(self.fixture['directory'], '12345', True)
        self.assertEqual(self.config.read_bytes(), before)

    def test_protected_selection_lock_blocks_start(self):
        before = self.config.read_bytes()
        lease = ExperimentLease(self.config).acquire()
        try:
            with self.assertRaises(ExperimentInUse):
                self.service.prepare(self.fixture['directory'], '12345', True)
        finally:
            lease.release()
        self.assertEqual(self.config.read_bytes(), before)

    def test_post_lease_validation_sees_changed_latest_boundary(self):
        original = ExperimentLease.acquire
        def acquire(lease):
            result = original(lease)
            if lease.path == Path(str(self.database) + '.lock'):
                self.corrupt("UPDATE current_state SET snapshot=json_set(snapshot,'$.individual_id','A-changed')")
            return result
        with patch.object(ExperimentLease, 'acquire', acquire):
            self.assert_prepare_rejected()

    def extend(self, count):
        store = EventStore(self.database)
        try:
            state = store.latest_state()
            for _ in range(count):
                current = replace(state, state_version=state.state_version + 1)
                store.transition(state, current, 'TEST_ONLY', {})
                state = current
        finally:
            store.close()

    def traced_boundary(self):
        with closing(sqlite3.connect(self.database.as_uri() + '?mode=ro', uri=True)) as db:
            queries, steps = [], [0]
            db.set_trace_callback(queries.append)
            def progress():
                steps[0] += 1
                return 0
            db.set_progress_handler(progress, 1)
            result = verify_startup_boundary(self.database, self.identity, db)
        return result, queries, steps[0]

    def test_history_size_does_not_increase_current_boundary_work(self):
        self.extend(10)
        small, small_queries, small_steps = self.traced_boundary()
        self.extend(1000)
        large, large_queries, large_steps = self.traced_boundary()
        self.assertEqual((small['state_version'], large['state_version']), (10, 1010))
        self.assertEqual(len(small_queries), len(large_queries))
        self.assertLessEqual(large_steps, small_steps + 20)
        for query in large_queries:
            lower = query.lower()
            if 'from events' in lower:
                self.assertIn('where state_version=', lower)
                self.assertIn("event_type='state_updated' limit 2", lower)
            if 'from states' in lower:
                self.assertIn('order by state_version desc limit 1', lower)
            if 'from state_sessions' in lower:
                self.assertIn('where state_version=', lower)

    def test_old_corruption_is_full_audit_responsibility(self):
        self.extend(3)
        self.assertTrue(verify(self.database)['valid_state_chain'])
        self.corrupt("UPDATE states SET snapshot=json_set(snapshot,'$.individual_id','A-old-corrupt') WHERE state_version=1")
        self.assertEqual(lifetime_entry(self.fixture['directory'])['state_version'], 3)
        with self.assertRaisesRegex(ValueError, 'Broken state chain at A1'):
            verify(self.database)


if __name__ == '__main__':
    unittest.main()
