"""Instrument-only fixtures: no A, bridge, Minecraft or canonical database writes."""
from hashlib import sha256
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from individual.runtime_monitor import Event, LoopEvidence, MonitorReader, MonitorWorker, MonitorWindow
from individual.state import utc_now
from launcher import launch_runtime_monitor, show_launcher


class MonitorTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = self.root / 'selection.json'
        self.reader = MonitorReader(self.config, self.root, batch_size=8)
        self.database = self.root / 'instrument-fixture.db'

    def fixture(self, identity='fixture-identity', path=None):
        path = path or self.database
        db = sqlite3.connect(path)
        db.executescript('''
            CREATE TABLE experiment(singleton INTEGER PRIMARY KEY,individual_id TEXT);
            CREATE TABLE states(state_version INTEGER PRIMARY KEY,timestamp TEXT);
            CREATE TABLE sessions(session_id TEXT PRIMARY KEY,start_version INTEGER);
            CREATE TABLE session_ends(session_id TEXT PRIMARY KEY,ended_at TEXT,reason TEXT);
            CREATE TABLE state_sessions(state_version INTEGER PRIMARY KEY,session_id TEXT);
            CREATE TABLE events(event_sequence INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT,
                individual_id TEXT,state_version INTEGER,timestamp TEXT,event_type TEXT,payload TEXT);
        ''')
        db.execute('INSERT INTO experiment VALUES(1,?)', (identity,))
        db.execute('INSERT INTO states VALUES(0,?)', (utc_now(),))
        db.commit()
        db.close()
        self.select(path, identity)
        return path

    def select(self, path, identity):
        self.config.write_text(json.dumps({'database': str(path), 'individual_id': identity}), encoding='utf-8')

    def session(self, session='session-1', path=None):
        with closing(sqlite3.connect(path or self.database)) as db, db:
            start = db.execute('SELECT max(state_version) FROM states').fetchone()[0] + 1
            db.execute('INSERT INTO sessions VALUES(?,?)', (session, start))
        self.event('SESSION_STARTED', {'session_id': session}, session, path)

    def event(self, kind, payload=None, session='session-1', path=None, version=None):
        with closing(sqlite3.connect(path or self.database)) as db, db:
            owner = db.execute('SELECT individual_id FROM experiment').fetchone()[0]
            if version is None:
                version = db.execute('SELECT max(state_version) FROM states').fetchone()[0] + 1
                db.execute('INSERT INTO states VALUES(?,?)', (version, utc_now()))
                db.execute('INSERT INTO state_sessions VALUES(?,?)', (version, session))
            cursor = db.execute('INSERT INTO events(event_id,individual_id,state_version,timestamp,event_type,payload) VALUES(?,?,?,?,?,?)',
                ('fixture-event', owner, version, utc_now(), kind, json.dumps(payload or {})))
            return version, cursor.lastrowid

    def end(self, session='session-1'):
        self.event('SESSION_ENDED', {'reason': 'fixture finished'}, session)
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('INSERT INTO session_ends VALUES(?,?,?)', (session, utc_now(), 'fixture finished'))

    def input(self, frame, session='session-1'):
        version, _ = self.event('WORLD_OBSERVATION', {'frame_id': frame}, session)
        self.event('OBSERVATION_FRAME', {'frame_id': frame}, session, version=version)
        self.event('RECURSIVE_PARTIAL_OUTPUT', {'experience': {'frame_id': frame, 'action_ids': []}}, session, version=version)
        return version

    def request(self, action='action-1', frame='frame-1'):
        return self.event('ACTION_REQUESTED', {'action_id': action, 'action_code': 0,
            'provenance': {'frame_id': frame}})

    def test_missing_selection_and_registered_only_are_idle(self):
        self.assertEqual(self.reader.poll().state, 'IDLE')
        self.fixture()
        view = self.reader.poll()
        self.assertEqual(view.state, 'IDLE')
        self.assertEqual(view.version, 0)
        self.assertEqual(view.loop, 'IDLE')

    def test_session_detected_incremental_refresh_and_no_duplicate_counts(self):
        self.fixture()
        self.assertEqual(self.reader.poll().state, 'IDLE')
        self.session()
        self.assertEqual(self.reader.poll().session, 'session-1')
        self.input('frame-1')
        view = self.reader.poll()
        self.assertEqual(view.counts['Observations'], 1)
        self.assertEqual(view.counts['Recursive outputs'], 1)
        cursor = self.reader.cursor
        self.assertEqual(self.reader.poll().counts, view.counts)
        self.assertEqual(self.reader.cursor, cursor)

    def test_ended_preserved_then_next_session_resets_counters(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        self.reader.poll()
        self.end()
        view = self.reader.poll()
        self.assertEqual((view.state, view.loop), ('ENDED', 'ENDED'))
        self.assertEqual(self.reader.poll().events, view.events)
        self.session('session-2')
        view = self.reader.poll()
        self.assertEqual(view.session, 'session-2')
        self.assertEqual(view.counts['Observations'], 0)
        self.assertTrue(all(e.kind == 'SESSION_STARTED' for e in view.events))

    def test_selected_individual_changed_re_attaches_without_writing_selection(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        self.reader.poll()
        other = self.root / 'other.db'
        self.fixture('other-fixture', other)
        self.session('other-session', other)
        before = self.config.read_bytes()
        view = self.reader.poll()
        self.assertEqual((view.individual, view.session), ('other-fixture', 'other-session'))
        self.assertEqual(view.counts['Observations'], 0)
        self.assertEqual(before, self.config.read_bytes())

    def test_missing_initializing_corrupt_or_mismatched_database_retries(self):
        self.select(self.database, 'fixture-identity')
        self.assertEqual(self.reader.poll().state, 'UNKNOWN')
        self.database.write_bytes(b'initializing')
        self.assertEqual(self.reader.poll().state, 'UNKNOWN')
        self.database.unlink()
        self.fixture()
        self.select(self.database, 'wrong-identity')
        self.assertEqual(self.reader.poll().state, 'UNKNOWN')
        self.select(self.database, 'fixture-identity')
        self.session()
        self.assertEqual(self.reader.poll().state, 'RUNNING')

    def test_observation_is_not_complete_loop(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        view = self.reader.poll()
        self.assertEqual(view.loop, 'WAITING')
        self.assertEqual(view.stages[0][0], '●')
        self.assertEqual(view.stages[3][0], '○')

    def test_requested_is_not_executed_and_wrong_receipt_does_not_match(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        self.reader.poll()
        self.request()
        self.event('ACTION_EXECUTED', {'action_id': 'other-action'})
        view = self.reader.poll()
        self.assertEqual(view.loop, 'WAITING')
        self.assertEqual(view.stages[3][0], '○')
        self.assertIn('ACTION_EXECUTED', view.waiting)

    def test_executed_without_renewed_world_input_waits(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        self.reader.poll()
        self.request()
        self.event('ACTION_EXECUTED', {'action_id': 'action-1'})
        view = self.reader.poll()
        self.assertEqual(view.stages[3][0], '●')
        self.assertEqual(view.loop, 'WAITING')
        self.assertIn('WORLD_OBSERVATION', view.waiting)

    def test_complete_order_requires_matching_new_frame_and_action_processing(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        self.reader.poll()
        self.request()
        self.event('ACTION_EXECUTED', {'action_id': 'action-1'})
        self.reader.poll()
        version, _ = self.event('WORLD_OBSERVATION', {'frame_id': 'frame-2'})
        self.event('RECURSIVE_PARTIAL_OUTPUT', {'experience': {'frame_id': 'frame-2', 'action_ids': ['wrong']}}, version=version)
        self.assertEqual(self.reader.poll().loop, 'WAITING')
        self.event('RECURSIVE_PARTIAL_OUTPUT', {'experience': {'frame_id': 'frame-2', 'action_ids': ['action-1']}}, version=version)
        view = self.reader.poll()
        self.assertEqual(view.loop, 'RUNNING')
        self.assertTrue(all(marker == '●' for marker, _ in view.stages))

    def test_failure_not_success_and_unrelated_observations_do_not_complete(self):
        self.fixture()
        self.session()
        self.input('frame-1')
        self.reader.poll()
        self.request()
        self.event('ACTION_FAILED', {'action_id': 'action-1', 'error': {'code': 'TEST_ONLY'}})
        self.input('frame-2')
        view = self.reader.poll()
        self.assertEqual(view.stages[3][0], '×')
        self.assertEqual(view.counts['Actions executed'], 0)
        self.assertEqual(view.counts['Failures'], 1)
        self.assertNotEqual(view.loop, 'RUNNING')

    def test_wrong_order_or_missing_pre_request_processing_is_not_closed(self):
        loop = LoopEvidence()
        for seq, kind, data in [(1, 'ACTION_REQUESTED', {'action_id': 'x', 'frame_id': 'before'}),
            (2, 'WORLD_OBSERVATION', {'frame_id': 'after'}), (3, 'ACTION_EXECUTED', {'action_id': 'x'}),
            (4, 'RECURSIVE_PARTIAL_OUTPUT', {'frame_id': 'after', 'action_ids': ['x']})]:
            loop.accept(Event(seq, seq, utc_now(), kind, data))
        self.assertNotEqual(loop.status()[0], 'RUNNING')

    def test_missing_action_identity_cannot_count_as_matched_execution(self):
        loop = LoopEvidence()
        loop.accept(Event(1, 1, utc_now(), 'ACTION_REQUESTED'))
        loop.accept(Event(2, 2, utc_now(), 'ACTION_EXECUTED'))
        self.assertEqual(loop.stages[3][0], '○')

    def test_new_input_failure_does_not_keep_displaying_previous_cycle_as_running(self):
        loop = LoopEvidence()
        loop.complete = True
        loop.accept(Event(1, 1, utc_now(), 'OBSERVATION_FAILED'))
        self.assertEqual(loop.status()[0], 'WAITING')
        self.assertEqual(loop.stages[0][0], '×')

    def test_pages_are_incremental_and_list_bounded_without_reading_state_snapshot(self):
        self.fixture()
        self.session()
        self.reader.poll()
        for i in range(110):
            self.event('WORLD_OBSERVATION', {'frame_id': f'frame-{i}'})
        cursors = []
        while self.reader.poll().counts['Observations'] < 110:
            cursors.append(self.reader.cursor)
        self.assertEqual(cursors, sorted(set(cursors)))
        self.assertEqual(len(self.reader.events), 100)
        self.assertEqual(self.reader.poll().counts['Observations'], 110)

    def test_initial_attach_counts_entire_session_but_loads_only_tail_metadata(self):
        self.fixture()
        self.session()
        for i in range(25):
            self.event('WORLD_OBSERVATION', {'frame_id': f'frame-{i}', 'observation': {'large': 'x' * 10000}})
        view = self.reader.poll()
        self.assertEqual(view.counts['Observations'], 25)
        self.assertEqual(len(view.events), 8)
        self.assertNotIn('observation', view.events[-1].data)

    def test_read_only_queries_payload_and_close_cannot_modify_database(self):
        self.fixture()
        self.session()
        _, seq = self.event('ACTION_FAILED', {'action_id': 'x', 'full': {'nested': 'actual payload'}})
        before = sha256(self.database.read_bytes()).hexdigest()
        original = self.reader.connect
        writes = []
        def readonly(path):
            db = original(path)
            self.assertEqual(db.execute('PRAGMA query_only').fetchone()[0], 1)
            def authorize(operation, *args):
                if operation in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
                                 sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE):
                    writes.append(operation)
                    return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            db.set_authorizer(authorize)
            return db
        with patch.object(self.reader, 'connect', side_effect=readonly):
            view = self.reader.poll()
            raw = self.reader.payload(view.database, view.individual, view.session, seq)
            self.assertEqual(json.loads(raw)['full']['nested'], 'actual payload')
            worker = MonitorWorker(self.reader)
            worker.stop()
        self.assertFalse(writes)
        self.assertEqual(before, sha256(self.database.read_bytes()).hexdigest())
        with closing(self.reader.connect(self.database)) as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM events')
        self.event('WORLD_OBSERVATION', {'frame_id': 'still-writing-after-monitor-close'})
        self.assertEqual(self.reader.poll().counts['Observations'], 1)

    def test_payload_cannot_cross_session_or_individual_boundary(self):
        self.fixture()
        self.session()
        _, seq = self.event('ACTION_REQUESTED', {'action_id': 'x'})
        for owner, session in [('wrong', 'session-1'), ('fixture-identity', 'wrong')]:
            with self.assertRaises(ValueError):
                self.reader.payload(self.database, owner, session, seq)

    def test_readonly_wal_poll_sees_commits_without_reopening_monitor(self):
        self.fixture()
        writer = sqlite3.connect(self.database)
        self.addCleanup(writer.close)
        writer.execute('PRAGMA journal_mode=WAL')
        self.session()
        self.reader.poll()
        self.input('frame-1')
        self.assertEqual(self.reader.poll().counts['Observations'], 1)

    def test_launcher_starts_independent_monitor_only(self):
        with patch('launcher.subprocess.Popen') as process:
            result = launch_runtime_monitor(self.config)
            args, kwargs = process.call_args
            self.assertEqual(args[0][1:3], ['-m', 'individual.runtime_monitor'])
            self.assertIn(str(self.config), args[0])
            self.assertTrue('creationflags' in kwargs or kwargs.get('start_new_session'))
            self.assertIs(result, process.return_value)

    def test_actual_launcher_monitor_button_does_not_launch_experiment_or_change_selection(self):
        import tkinter as tk
        from tkinter import ttk
        class Service:
            config = self.config
            def entries(self):
                return [], []
            def default_port(self):
                return '12345'
            def missing_selection(self):
                return False
            def prepare(self, *args):
                raise AssertionError('Monitor button must not start an experiment')
        def click_button(window):
            def find(widget):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and child.cget('text') == '运行监视器':
                        return child
                    found = find(child)
                    if found is not None:
                        return found
            button = find(window)
            self.assertIsNotNone(button)
            button.invoke()
            window.destroy()
        with patch('launcher.launch_runtime_monitor') as monitor, patch.object(tk.Tk, 'mainloop', click_button):
            self.assertIsNone(show_launcher(Service()))
            monitor.assert_called_once_with(self.config)
        self.assertFalse(self.config.exists())

    def test_window_can_open_idle_and_close_without_experiment(self):
        import tkinter as tk
        window = tk.Tk()
        window.withdraw()
        ui = MonitorWindow(window, self.reader)
        window.update()
        self.assertEqual(ui.view.state, 'IDLE')
        self.assertEqual(window.title(), 'BECA 运行监视器')
        ui.close()
        ui.worker.thread.join(timeout=2)
        self.assertFalse(ui.worker.thread.is_alive())
        self.assertFalse(self.database.exists())


if __name__ == '__main__':
    unittest.main()
