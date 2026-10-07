"""Experimenter recording controls; disposable databases and mocked GUI/body only."""
from contextlib import closing, redirect_stdout
from copy import deepcopy
import io
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

import main
from launcher import LaunchConfig, LauncherService, show_launcher
from individual.core import ACore
from individual.current_state import audit_gaps, session_mode
from individual.inspect import verify
from individual.runtime_monitor import MonitorReader
from individual.storage import create_lifetime
from tests.test_core import FakeBridge
from tests.test_structure import observation


class ImmediateThread:
    """Run the empty-input console reader deterministically; no live processes."""
    def __init__(self, target, **kwargs):
        self.target = target

    def start(self):
        self.target()


class RecordingOptionTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.config = self.root/'selection.json'
        self.fixture = create_lifetime(self.root/'individuals', self.config, 'TEST_ONLY recording option')
        self.database = Path(self.fixture['database'])

    def test_launch_config_default_on_and_explicit_off(self):
        self.assertTrue(LaunchConfig(25565, True).full_history_enabled)
        self.assertEqual(LaunchConfig(25565, True).arguments(), ['--port', '25565', '--froi'])
        self.assertEqual(LaunchConfig(25565, False, False).arguments(), ['--port', '25565', '--no-full-history'])

    def test_prepare_passes_recording_option_without_changing_database(self):
        service = LauncherService(self.root/'individuals', self.config)
        before = self.database.read_bytes()
        for enabled in (True, False):
            result = service.prepare(self.fixture['directory'], '25565', True, enabled)
            self.assertIs(result.full_history_enabled, enabled)
            self.assertEqual('--no-full-history' in result.arguments(), not enabled)
        self.assertEqual(self.database.read_bytes(), before)
        with self.assertRaises(ValueError):
            service.prepare(self.fixture['directory'], '25565', True, 'false')

    def test_launcher_checkbox_defaults_on_and_transmits_off(self):
        variables, buttons, checkboxes, labels = [], {}, {}, []
        class Variable:
            def __init__(self, value=None):
                self.value = value
            def get(self):
                return self.value
            def set(self, value):
                self.value = value
        def boolean(value=None):
            var = Variable(value)
            variables.append(var)
            return var
        def button(*args, **kwargs):
            buttons[kwargs['text']] = kwargs['command']
            return MagicMock()
        def checkbox(*args, **kwargs):
            checkboxes[kwargs['text']] = kwargs['variable']
            return MagicMock()
        def label(*args, **kwargs):
            labels.append(kwargs.get('text', ''))
            return MagicMock()
        window, table = MagicMock(), MagicMock()
        table.selection.return_value = ['TEST_ONLY_ID']
        ttk = SimpleNamespace(Frame=MagicMock(), Label=label, Treeview=Mock(return_value=table),
                              Scrollbar=MagicMock(), Entry=MagicMock(), Checkbutton=checkbox, Button=button)
        tk = ModuleType('tkinter')
        tk.Tk, tk.StringVar, tk.BooleanVar, tk.TclError = lambda: window, Variable, boolean, RuntimeError
        tk.ttk, tk.messagebox, tk.simpledialog = ttk, MagicMock(), MagicMock()
        service = Mock()
        service.entries.return_value = ([{'individual_id':'TEST_ONLY_ID', 'directory':'fixture',
            'database':'fixture.db', 'selected':True, 'role':'mainline', 'state_version':0, 'session_count':0}], [])
        service.missing_selection.return_value = False
        service.default_port.return_value = '25565'
        service.prepare.return_value = LaunchConfig(25565, True, False)
        def click_start():
            self.assertTrue(checkboxes['保存完整历史'].get())
            checkboxes['保存完整历史'].set(False)
            buttons['启动实验']()
        window.mainloop.side_effect = click_start
        with patch.dict(sys.modules, {'tkinter':tk}):
            result = show_launcher(service)
        service.prepare.assert_called_once_with('fixture', '25565', True, False)
        self.assertFalse(result.full_history_enabled)
        self.assertTrue(any('关闭后仍保存 A 的当前状态' in text for text in labels))
        tk.messagebox.showerror.assert_not_called()

    def supervisor_arguments(self, extra):
        from supervisor import supervisor as module
        supervisor = MagicMock()
        supervisor.run.return_value = 0
        with patch.object(sys, 'argv', ['main.py', '--port', '25565', *extra]), \
             patch.object(sys, 'stdin', io.StringIO()), redirect_stdout(io.StringIO()), \
             patch('individual.lifetime.resolve_runtime_database', return_value=self.database), \
             patch.object(module, 'Supervisor', return_value=supervisor):
            self.assertEqual(module.cli(), 0)
        return supervisor.start.call_args.args[0]

    def test_supervisor_cli_defaults_on_and_forwards_explicit_off(self):
        self.assertNotIn('--no-full-history', self.supervisor_arguments([]))
        self.assertIn('--no-full-history', self.supervisor_arguments(['--no-full-history']))

    def test_main_preserves_gui_recording_option(self):
        with patch('launcher.show_launcher', return_value=LaunchConfig(25565, True, False)), \
             patch('main.cli', side_effect=lambda: list(sys.argv[1:])):
            self.assertEqual(main.run([]), ['--port', '25565', '--froi', '--no-full-history'])

    def test_core_cli_receives_mode_without_adding_recursive_context_field(self):
        from individual import core as module
        for enabled, extra in ((True, []), (False, ['--no-full-history'])):
            core = MagicMock()
            core.state = SimpleNamespace(individual_id='TEST_ONLY', state_version=1, session_id='TEST_ONLY_S')
            with patch.object(sys, 'argv', ['core', '--minecraft-port', '25565', *extra]), \
                 patch.object(sys, 'stdin', io.StringIO()), redirect_stdout(io.StringIO()), \
                 patch('individual.lifetime.resolve_runtime_database', return_value=self.database), \
                 patch.object(module, 'MinecraftBridge', return_value=FakeBridge()), \
                 patch.object(module, 'ACore', return_value=core) as constructor, \
                 patch.object(module.threading, 'Thread', ImmediateThread), patch.object(module.signal, 'signal'):
                self.assertEqual(module.main(), 0)
            self.assertIs(constructor.call_args.kwargs['full_history_enabled'], enabled)
            self.assertNotIn('full_history_enabled', constructor.call_args.args[4])
            self.assertNotIn('no_full_history', constructor.call_args.args[4])

    def test_on_off_on_retains_identity_caps_continuity_and_declared_gap(self):
        original_rows = None
        saved, previous_version, expected_caps, expected_froi = None, None, None, None
        for enabled in (True, False, True):
            core = ACore(self.database, FakeBridge(), froi=True, full_history_enabled=enabled)
            try:
                self.assertEqual(core.state.individual_id, self.fixture['individual_id'])
                if saved:
                    self.assertEqual(core.state.state_version, previous_version+1)
                    self.assertEqual(core.state.internal_state, saved)
                local = core.state.internal_state['l0_state']
                capacities = {key: deepcopy(local[key]) for key in ('locked_caps','locked_resource_caps')}
                if expected_caps is None:
                    expected_caps = capacities
                self.assertEqual(capacities, expected_caps)
                with closing(sqlite3.connect(self.database)) as db:
                    self.assertIs(session_mode(db, core.state.session_id), enabled)
                    rows_before = db.execute('SELECT * FROM states ORDER BY state_version').fetchall()
                    if original_rows is not None:
                        self.assertEqual(rows_before[:len(original_rows)], original_rows)
                core.accept_observation(observation(1))
                core.accept_observation(observation(2))
                # FROI seals its boundary on the first actual relation read.
                froi_boundary = core.state.internal_state['l0_state']['froi_boundary']
                if expected_froi is None:
                    expected_froi = deepcopy(froi_boundary)
                self.assertEqual(froi_boundary, expected_froi)
                self.assertTrue(core.state.continuity_required)
                self.assertNotIn('full_history_enabled', core.state.to_dict())
                self.assertNotIn('full_history_enabled', core.state.internal_state)
                view = MonitorReader(self.config).poll()
                self.assertEqual(view.version, core.state.state_version)
                self.assertIn('FULL HISTORY: '+('ON' if enabled else 'OFF'), view.message)
                if not enabled:
                    self.assertEqual(view.counts['Observations'], '未记录')
                    with closing(sqlite3.connect(self.database)) as db:
                        self.assertEqual(db.execute('SELECT * FROM states ORDER BY state_version').fetchall(), rows_before)
            finally:
                core.shutdown('TEST_ONLY recording run')
            saved = deepcopy(core.state.internal_state)
            previous_version = core.state.state_version
            if enabled and original_rows is None:
                with closing(sqlite3.connect(self.database)) as db:
                    original_rows = db.execute('SELECT * FROM states ORDER BY state_version').fetchall()
        report = verify(self.database)
        self.assertTrue(report['recorded_segments_verified'])
        self.assertFalse(report['audit_history_complete'])
        self.assertEqual(len(report['audit_gaps']), 1)
        with closing(sqlite3.connect(self.database)) as db:
            first, last = audit_gaps(db)[0]
            self.assertFalse(db.execute('SELECT 1 FROM states WHERE state_version BETWEEN ? AND ?', (first,last)).fetchone())
            self.assertEqual(db.execute('SELECT MAX(state_version) FROM states').fetchone()[0], previous_version)


if __name__ == '__main__':
    unittest.main()
