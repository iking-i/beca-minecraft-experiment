"""External launcher administration; isolated storage, never a real A."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from individual.identity import ExperimentInUse, ExperimentLease
from individual.storage import create_lifetime, list_lifetimes, select_existing_lifetime
from individual.lifetime import resolve_runtime_database
from integration.froi import preflight as froi_preflight, load_caps
from launcher import LauncherService, LaunchConfig
import main


class LauncherTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.storage, self.config = self.root/'individuals', self.root/'current.json'
        self.service = LauncherService(self.storage, self.config)

    def create(self, label='TEST_ONLY'):
        return create_lifetime(self.storage, self.config, label)

    def test_catalog_existing_mainlines_metadata_current_and_readonly(self):
        a, b = self.create('first'), self.create('second')
        before = {x['database']:Path(x['database']).read_bytes() for x in (a,b)}
        entries, rejected = self.service.entries()
        self.assertFalse(rejected)
        self.assertEqual({e['individual_id'] for e in entries},{a['individual_id'],b['individual_id']})
        current = next(e for e in entries if e['selected'])
        self.assertEqual(current['individual_id'],b['individual_id'])
        self.assertEqual(current['label'],'second')
        self.assertEqual(current['state_version'],0)
        self.assertEqual(current['session_count'],0)
        self.assertTrue(current['created_at'])
        for path, raw in before.items():
            self.assertEqual(Path(path).read_bytes(),raw)

    def test_corrupt_database_manifest_mismatch_and_branch_not_listed(self):
        a = self.create()
        directory = Path(a['directory'])
        manifest = directory/'lifetime.json'
        original = manifest.read_bytes()
        for bad in ({'individual_id':'A-wrong','role':'mainline','database':'individual.db'},
                    {'individual_id':a['individual_id'],'role':'snapshot_branch','database':'individual.db'},
                    {'individual_id':a['individual_id'],'role':'mainline','database':'../individual.db'}):
            manifest.write_text(json.dumps(bad),encoding='utf8')
            self.assertFalse(self.service.entries()[0])
        manifest.write_bytes(original)
        Path(a['database']).write_bytes(b'invalid SQLite')
        self.assertFalse(self.service.entries()[0])

    def test_selection_updates_pin_index_without_changing_db_or_version(self):
        a, b = self.create(), self.create()
        paths = [Path(x['database']) for x in (a,b)]
        before = {p:sha256(p.read_bytes()).hexdigest() for p in paths}
        selected = select_existing_lifetime(a['directory'],self.storage,self.config)
        self.assertEqual(selected['individual_id'],a['individual_id'])
        self.assertEqual(resolve_runtime_database(config=self.config),paths[0])
        self.assertEqual(json.loads(self.config.read_text())['role'],'mainline')
        self.assertEqual(selected['state_version'],0)
        self.assertEqual(len(json.loads((self.root/'index.json').read_text())['individuals']),2)
        self.assertEqual(before,{p:sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_active_target_lease_refuses_selection(self):
        a, b = self.create(), self.create()
        before=self.config.read_bytes()
        lease=ExperimentLease(a['database']).acquire()
        self.addCleanup(lease.release)
        with self.assertRaises(ExperimentInUse):
            select_existing_lifetime(a['directory'],self.storage,self.config)
        self.assertEqual(self.config.read_bytes(),before)

    def test_active_current_lease_refuses_switching_away(self):
        a, b = self.create(), self.create()
        lease=ExperimentLease(b['database']).acquire()
        self.addCleanup(lease.release)
        with self.assertRaises(ExperimentInUse):
            select_existing_lifetime(a['directory'],self.storage,self.config)
        self.assertEqual(json.loads(self.config.read_text())['individual_id'],b['individual_id'])

    def test_create_delegates_existing_initializer_keeps_previous_history(self):
        a=self.create()
        before=Path(a['database']).read_bytes()
        pin=self.config.read_bytes()
        with patch('launcher.create_lifetime',wraps=create_lifetime) as existing:
            b=self.service.create('GUI new')
            existing.assert_called_once_with(storage_root=self.storage,config=self.config,label='GUI new',
                                              replace_missing_selection=False)
        self.assertNotEqual(a['individual_id'],b['individual_id'])
        self.assertEqual(Path(a['database']).read_bytes(),before)
        self.assertEqual((Path(b['directory'])/'previous-selection.json').read_bytes(),pin)
        self.assertEqual(resolve_runtime_database(config=self.config),Path(b['database']))

    def test_missing_selection_requires_explicit_confirmation_and_preserves_old_pin(self):
        self.config.write_text(json.dumps({'database':str(self.root/'missing.db'),
            'individual_id':'A-missing','role':'mainline'}))
        before=self.config.read_bytes()
        with patch('launcher.create_lifetime',wraps=create_lifetime) as existing:
            with self.assertRaisesRegex(ValueError,'明确确认'):
                self.service.create('not confirmed')
            existing.assert_not_called()
            b=self.service.create('confirmed',True)
            self.assertTrue(existing.call_args.kwargs['replace_missing_selection'])
        self.assertEqual((Path(b['directory'])/'previous-selection.json').read_bytes(),before)

    def test_port_validation_precedes_switching(self):
        a,b=self.create(),self.create()
        before=self.config.read_bytes()
        for port in ('0','65536','hello','１２３','-3'):
            with self.assertRaises(ValueError):
                self.service.prepare(a['directory'],port,True)
        self.assertEqual(self.config.read_bytes(),before)

    def test_prepare_uses_existing_preflights_and_run_only_port_no_db(self):
        a=self.create()
        original=self.service.minecraft_config.read_bytes()
        with patch('individual.startup_validation.preflight_current_caps',wraps=__import__('individual.startup_validation',fromlist=['preflight_current_caps']).preflight_current_caps) as formal, \
             patch('integration.froi.preflight',wraps=froi_preflight) as froi:
            result=self.service.prepare(a['directory'],'51234',True)
            formal.assert_called_once()
            froi.assert_called_once()
        self.assertEqual(result.arguments(),['--port','51234','--froi'])
        self.assertEqual(original,self.service.minecraft_config.read_bytes())

    def test_explicit_cli_port_or_froi_never_opens_gui(self):
        for args in (['--port','12345'],['--froi'],['--froi','--port','12345'],['--help']):
            with patch('launcher.show_launcher') as gui,patch('main.cli',return_value=0) as cli:
                self.assertEqual(main.run(args),0)
                gui.assert_not_called()
                cli.assert_called_once()

    def test_no_arguments_opens_launcher_then_same_cli(self):
        with patch('launcher.show_launcher',return_value=LaunchConfig(12345,True)) as gui:
            seen=[]
            import sys
            with patch('main.cli',side_effect=lambda:seen.extend(sys.argv[1:]) or 0):
                self.assertEqual(main.run([]),0)
            gui.assert_called_once()
            self.assertEqual(seen,['--port','12345','--froi'])

    def test_cancel_never_launches_core(self):
        with patch('launcher.show_launcher',return_value=None),patch('main.cli') as cli:
            self.assertEqual(main.run([]),0)
            cli.assert_not_called()

    def test_headless_error_is_clear_and_never_launches(self):
        with patch('launcher.show_launcher',side_effect=RuntimeError('无法打开图形启动器')), \
             patch('main.cli') as cli,patch('sys.stderr'):
            self.assertEqual(main.run([]),1)
            cli.assert_not_called()

    def test_locked_froi_cannot_start_non_froi_and_pin_not_changed(self):
        from individual.core import ACore
        from tests.test_core import FakeBridge
        from tests.test_structure import observation
        a=self.create()
        core=ACore(a['database'],FakeBridge(),froi=True)
        core.accept_observation(observation())
        core.shutdown()
        self.create('current other A')
        before=self.config.read_bytes()
        # Formal conditions also differ between an unmonitored fixture and GUI.
        # Isolate the FROI guard, retaining its actual persisted database read.
        with patch('individual.startup_validation.preflight_current_caps'):
            with self.assertRaisesRegex(ValueError,'locked FROI'):
                self.service.prepare(a['directory'],'12345',False)
        self.assertEqual(self.config.read_bytes(),before)

    def test_damaged_other_manifest_does_not_block_index_switch(self):
        a,b=self.create(),self.create()
        (Path(b['directory'])/'lifetime.json').write_text('not JSON')
        select_existing_lifetime(a['directory'],self.storage,self.config)
        self.assertEqual(resolve_runtime_database(config=self.config),Path(a['database']))

    def test_index_write_failure_does_not_switch_pin(self):
        a,b=self.create(),self.create()
        before=self.config.read_bytes()
        with patch('individual.storage.update_index',side_effect=OSError('TEST_ONLY disk failure')):
            with self.assertRaises(OSError):
                select_existing_lifetime(a['directory'],self.storage,self.config)
        self.assertEqual(self.config.read_bytes(),before)
