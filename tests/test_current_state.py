"""Persistence controls using disposable fixtures only; no Minecraft or real A."""
from contextlib import closing
from copy import deepcopy
from dataclasses import replace, asdict
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from individual.core import ACore
from individual.current_state import current_row, session_mode, audit_gaps
from individual.events import EventStore, encode
from individual.startup_validation import preflight_current_caps as preflight
from individual.formal_l0 import FormalLimits
from individual.inspect import verify
from individual.lifetime import history_summary
from individual.runtime_monitor import MonitorReader
from individual.startup_validation import verify_startup_boundary
from individual.storage import create_lifetime, lifetime_entry
from integration.froi import preflight as froi_preflight, load_caps
from tests.test_core import FakeBridge
from tests.test_structure import observation


class CurrentStateTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.config = self.root/'selection.json'
        self.fixture = create_lifetime(self.root/'individuals', self.config, 'TEST_ONLY persistence')
        self.database = Path(self.fixture['database'])
        self.identity = self.fixture['individual_id']

    def store(self, enabled=True):
        store = EventStore(self.database, full_history_enabled=enabled)
        self.addCleanup(store.close)
        return store

    def history(self):
        with closing(sqlite3.connect(self.database)) as db:
            return tuple(tuple(db.execute('SELECT * FROM '+table+' ORDER BY rowid'))
                         for table in ('states','events','state_sessions','snapshots'))

    def legacy(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('DROP TABLE current_state')
            db.execute('DROP TRIGGER contiguous_states')
            db.execute("CREATE TRIGGER contiguous_states BEFORE INSERT ON states WHEN NEW.state_version != COALESCE((SELECT MAX(state_version)+1 FROM states),0) BEGIN SELECT RAISE(ABORT,'state_version must increase by one'); END")

    def advance(self, store, state, payload=None):
        new = replace(state, state_version=state.state_version+1)
        store.transition(state, new, 'TEST_ONLY', payload or {}, [('TEST_ONLY_DETAIL', {'unchanged': True})])
        return new

    def test_legacy_adoption_exact_and_old_rows_untouched(self):
        original = self.history()
        self.legacy()
        with closing(sqlite3.connect(self.database)) as db:
            raw = db.execute('SELECT snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()[0]
        store = self.store()
        self.assertEqual(current_row(store.connection)[3], raw)
        self.assertEqual(store.latest_state().to_dict(), json.loads(raw))
        self.assertEqual(self.history(), original)

    def test_readonly_legacy_startup_does_not_migrate(self):
        self.legacy()
        before = self.database.read_bytes()
        result = verify_startup_boundary(self.database, self.identity)
        self.assertEqual(result['restore_source'], 'LEGACY_LATEST_SNAPSHOT')
        self.assertEqual(self.database.read_bytes(), before)

    def test_bad_legacy_latest_commit_is_not_adopted(self):
        self.legacy()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('DROP TRIGGER immutable_events_UPDATE')
            db.execute("UPDATE events SET payload=json_set(payload,'$.to_version',99) WHERE event_type='STATE_UPDATED'")
        with self.assertRaisesRegex(ValueError, 'commit mismatch'):
            EventStore(self.database)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertFalse(db.execute("SELECT 1 FROM sqlite_master WHERE name='current_state'").fetchone())

    def test_off_multiple_transitions_current_only_and_exact_contents(self):
        store = self.store(False)
        history = self.history()
        state = store.open_session()
        for _ in range(12):
            state = self.advance(store, state, {'large_audit': 'x'*10000})
            self.assertEqual(store.latest_state(), state)
        self.assertEqual(self.history(), history)
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM current_state').fetchone()[0], 1)
        self.assertEqual(state.individual_id, self.identity)
        self.assertEqual(state.state_version, 13)
        self.assertEqual(audit_gaps(store.connection), [(1,13)])
        self.assertFalse(session_mode(store.connection, state.session_id))

    def test_on_preserves_full_history_and_state_updated(self):
        store = self.store()
        state = store.open_session()
        for _ in range(3):
            state = self.advance(store, state)
        self.assertTrue(session_mode(store.connection, state.session_id))
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM states').fetchone()[0], 5)
        raw = store.connection.execute("SELECT payload FROM events WHERE state_version=? AND event_type='STATE_UPDATED'",(state.state_version,)).fetchone()[0]
        self.assertEqual(json.loads(raw)['state'], state.to_dict())
        self.assertEqual(store.latest_state(), state)
        self.assertTrue(verify(self.database)['valid_state_chain'])

    def test_off_resume_same_a_after_controlled_end(self):
        store = self.store(False)
        state = store.open_session()
        for _ in range(3):
            state = self.advance(store, state)
        ended = store.end_session(state, 'TEST_ONLY controlled stop', True)
        store.close()
        store.close = lambda: None
        reopened = self.store(False)
        self.assertEqual(reopened.latest_state(), ended)
        resumed = reopened.open_session()
        self.assertEqual(resumed.individual_id, self.identity)
        self.assertEqual(resumed.state_version, ended.state_version+1)
        self.assertEqual(resumed.internal_state, ended.internal_state)
        self.assertTrue(resumed.continuity_required)

    def test_off_unclean_stop_records_interruption_and_continues(self):
        store = self.store(False)
        state = self.advance(store, store.open_session())
        store.close()
        store.close = lambda: None
        resumed = self.store(False)
        state2 = resumed.open_session()
        end = resumed.connection.execute('SELECT end_version,interrupted FROM session_lifecycle_ends WHERE session_id=?',(state.session_id,)).fetchone()
        self.assertEqual(end, (state.state_version+1,1))
        self.assertEqual(state2.state_version,state.state_version+2)
        self.assertEqual(state2.individual_id,self.identity)

    def test_off_then_on_keeps_declared_gap_and_new_full_history(self):
        store = self.store(False)
        state = self.advance(store, store.open_session())
        ended = store.end_session(state, 'TEST_ONLY')
        store.close()
        store.close = lambda: None
        store = self.store(True)
        state = store.open_session()
        state = self.advance(store, state)
        store.end_session(state, 'TEST_ONLY ON')
        report = verify(self.database)
        self.assertFalse(report['valid_state_chain'])
        self.assertFalse(report['audit_history_complete'])
        self.assertTrue(report['recorded_segments_verified'])
        self.assertEqual(report['audit_gaps'], [{'start_version':1,'end_version':ended.state_version,'reason':'FULL_HISTORY_OFF'}])
        self.assertEqual(store.connection.execute('SELECT state_version FROM states ORDER BY state_version').fetchall(), [(0,),(4,),(5,),(6,)])

    def test_off_audit_report_distinguishes_current_from_coverage(self):
        store = self.store(False)
        state = self.advance(store, store.open_session())
        report = verify(self.database)
        self.assertEqual(report['current_state_version'], state.state_version)
        self.assertEqual(report['audit_coverage_end'], 0)
        self.assertFalse(report['audit_history_complete'])
        self.assertTrue(report['recorded_segments_verified'])
        summary = history_summary(self.database)
        self.assertFalse(summary['Experiment_session_history'][-1]['full_history_enabled'])
        self.assertIsNone(summary['Experiment_session_history'][-1]['event_counts'])

    def test_undeclared_gap_or_corrupted_recorded_history_is_rejected(self):
        store = self.store(False)
        self.advance(store, store.open_session())
        with store.connection:
            store.connection.execute('DROP TRIGGER gap_no_delete')
            store.connection.execute('DELETE FROM audit_gaps')
        with self.assertRaisesRegex(ValueError, 'without declared audit gap'):
            verify(self.database)

    def test_snapshot_export_still_works_for_on(self):
        store = self.store()
        state = store.open_session()
        snap = store.save_snapshot()
        raw = store.connection.execute('SELECT snapshot FROM snapshots WHERE snapshot_id=?',(snap,)).fetchone()[0]
        self.assertEqual(json.loads(raw), state.to_dict())

    def test_full_history_preserves_generator_event_inputs(self):
        store = self.store()
        previous = store.open_session()
        state = replace(previous, state_version=previous.state_version+1)
        extra = ((kind, {'n': n}) for n, kind in enumerate(('TEST_ONLY_ONE', 'TEST_ONLY_TWO')))
        store.transition(previous, state, 'TEST_ONLY', {}, extra)
        recorded = store.connection.execute(
            'SELECT event_type FROM events WHERE state_version=? ORDER BY event_sequence',
            (state.state_version,)).fetchall()
        self.assertEqual(recorded, [('TEST_ONLY',), ('TEST_ONLY_ONE',), ('TEST_ONLY_TWO',), ('STATE_UPDATED',)])

    def test_audit_gap_requires_actual_off_session_metadata(self):
        store = self.store(False)
        state = self.advance(store, store.open_session())
        with store.connection:
            store.connection.execute('DROP TRIGGER immutable_session_recording_modes_UPDATE')
            store.connection.execute('UPDATE session_recording_modes SET full_history_enabled=1 WHERE session_id=?',
                                     (state.session_id,))
        with self.assertRaisesRegex(ValueError, 'not covered by Full History OFF'):
            verify(self.database)

    def test_on_rollback_current_and_history_together(self):
        store = self.store()
        state = store.open_session()
        old_history = self.history()
        with patch.object(store, '_insert_event', side_effect=RuntimeError('TEST_ONLY write failure')):
            with self.assertRaisesRegex(RuntimeError, 'write failure'):
                self.advance(store, state)
        self.assertEqual(store.latest_state(), state)
        self.assertEqual(self.history(), old_history)

    def test_off_rollback_current_and_gap_together(self):
        store = self.store(False)
        state = store.open_session()
        before = audit_gaps(store.connection)
        store.connection.execute("CREATE TRIGGER test_abort_gap BEFORE UPDATE ON audit_gaps BEGIN SELECT RAISE(ABORT,'TEST_ONLY gap write failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.advance(store, state)
        self.assertEqual(store.latest_state(), state)
        self.assertEqual(audit_gaps(store.connection), before)

    def test_process_death_mid_transaction_leaves_previous_complete_state(self):
        store = self.store(False)
        state = store.open_session()
        later = replace(state, state_version=state.state_version+1)
        code = "import sqlite3,os,sys,json; raw=sys.stdin.read(); state=json.loads(raw); db=sqlite3.connect(sys.argv[1]); db.execute('BEGIN IMMEDIATE'); db.execute('UPDATE current_state SET state_version=?,timestamp=?,snapshot=? WHERE singleton=1',(state['state_version'],state['last_update_at'],raw)); os._exit(23)"
        result = subprocess.run([sys.executable,'-c',code,str(self.database)],input=encode(later.to_dict()).encode('utf8'),capture_output=True)
        self.assertEqual(result.returncode,23,result.stderr.decode())
        self.assertEqual(store.latest_state(),state)

    def test_stale_discontinuous_identity_and_caps_changes_rejected(self):
        store = self.store(False)
        state = store.open_session(formal_caps=FormalLimits())
        for candidate in (replace(state,state_version=state.state_version+2),
                          replace(state,state_version=state.state_version+1,individual_id='A-wrong')):
            with self.assertRaises(ValueError):
                store.transition(state,candidate,'TEST_ONLY',{})
        internal=deepcopy(state.internal_state)
        internal['l0_state']['locked_caps']['units']+=1
        with self.assertRaisesRegex(sqlite3.IntegrityError,'locked formal capacities'):
            store.transition(state,replace(state,state_version=state.state_version+1,internal_state=internal),'TEST_ONLY',{})
        self.assertEqual(store.latest_state(),state)

    def test_recording_mode_cannot_change_mid_session(self):
        store = self.store(False)
        state = store.open_session()
        with store.connection:
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute('UPDATE session_recording_modes SET full_history_enabled=1 WHERE session_id=?',(state.session_id,))
        store._requested_history_mode = True  # Only affects a NEXT session, not this one.
        state = self.advance(store,state)
        self.assertFalse(session_mode(store.connection,state.session_id))
        self.assertEqual(store.connection.execute('SELECT MAX(state_version) FROM states').fetchone()[0],0)

    def test_caps_preflights_use_current_not_old_history(self):
        store = self.store(False)
        state = store.open_session(formal_caps=FormalLimits())
        preflight(self.database,FormalLimits(),{})
        with self.assertRaisesRegex(ValueError,'locked_caps'):
            preflight(self.database,replace(FormalLimits(),units=FormalLimits().units+1),{})
        internal=deepcopy(state.internal_state)
        internal['l0_state']['froi_boundary']={'version':'FROI-1','caps':asdict(load_caps())}
        store.transition(state,replace(state,state_version=state.state_version+1,internal_state=internal),'TEST_ONLY',{})
        with self.assertRaisesRegex(ValueError,'locked FROI'):
            froi_preflight(self.database,False,load_caps())

    def test_startup_and_monitor_read_current_without_history(self):
        store = self.store(False)
        state = self.advance(store,store.open_session())
        with patch('individual.inspect.verify',side_effect=AssertionError('full audit forbidden')):
            entry = lifetime_entry(self.fixture['directory'])
        self.assertEqual(entry['state_version'],state.state_version)
        reader = MonitorReader(self.config)
        view=reader.poll()
        self.assertEqual(view.version,state.state_version)
        self.assertIn('FULL HISTORY: OFF',view.message)
        self.assertEqual(view.counts['Observations'],'未记录')
        store.end_session(state,'TEST_ONLY stop')
        self.assertEqual(reader.poll().state,'ENDED')

    def test_missing_authoritative_row_never_falls_back_to_stale_history(self):
        store = self.store(False)
        state = store.open_session()
        store.connection.execute('DROP TRIGGER current_no_delete')
        with store.connection:
            store.connection.execute('DELETE FROM current_state')
        with self.assertRaisesRegex(ValueError,'missing'):
            store.latest_state()
        with self.assertRaises(ValueError):
            verify_startup_boundary(self.database,self.identity)

    def test_core_off_restores_retained_structures_and_same_identity(self):
        core = ACore(self.database,FakeBridge(),froi=True,full_history_enabled=False)
        try:
            for i in range(3):
                core.accept_observation(observation(i))
            before=core.state
        finally:
            core.shutdown()
        resumed = ACore(self.database,FakeBridge(),froi=True,full_history_enabled=False)
        try:
            self.assertEqual(resumed.state.individual_id,before.individual_id)
            self.assertGreater(resumed.state.state_version,before.state_version)
            self.assertEqual(resumed.state.internal_state,before.internal_state)
            self.assertTrue(resumed.state.continuity_required)
        finally:
            resumed.shutdown()
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT MAX(state_version) FROM states').fetchone()[0],0)

    def test_on_process_death_rolls_back_both_current_and_full_history(self):
        store = self.store(True)
        state = store.open_session()
        before = self.history()
        later = replace(state,state_version=state.state_version+1)
        code = "import os,sys,json; from individual.events import EventStore; from individual.state import AState; store=EventStore(sys.argv[1]); previous=store.latest_state(); new=AState(**json.loads(sys.stdin.read())); store.connection.execute('BEGIN IMMEDIATE'); store._append_transition(previous,new,'TEST_ONLY',{}); os._exit(24)"
        result = subprocess.run([sys.executable,'-c',code,str(self.database)],input=encode(later.to_dict()).encode('utf8'),capture_output=True)
        self.assertEqual(result.returncode,24,result.stderr.decode())
        self.assertEqual(store.latest_state(),state)
        self.assertEqual(self.history(),before)

    def test_supervisor_exit_context_uses_current_version(self):
        from supervisor.supervisor import Supervisor, DEFAULT_LIMITS
        store = self.store(False)
        state = self.advance(store,store.open_session())
        supervisor = Supervisor(self.database,DEFAULT_LIMITS,log=lambda *args:None)
        try:
            context=supervisor._exit_context()
            self.assertEqual(context['state_version'],state.state_version)
            self.assertEqual(context['individual_id'],state.individual_id)
            self.assertEqual(context['session_id'],state.session_id)
        finally:
            supervisor.close()

    def test_off_invalid_payload_rejected_and_no_current_advance(self):
        store = self.store(False)
        state = store.open_session()
        for bad in ({'invalid': float('nan')},{'invalid': object()}):
            with self.assertRaises((ValueError,TypeError)):
                self.advance(store,state,bad)
            self.assertEqual(store.latest_state(),state)


if __name__ == '__main__':
    unittest.main()
