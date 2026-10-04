from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from individual.core import ACore
from individual.events import EventStore, encode
from individual.identity import ExperimentInUse
from individual.inspect import verify
from individual.lifetime import resolve_runtime_database
from individual.storage import create_lifetime, create_branch, save_report
from tests.test_core import FakeBridge
from tests.test_structure import observation


class StorageTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / '.test-tmp'
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.storage = self.directory / 'individuals'
        self.config = self.directory / 'current.json'

    def create(self):
        return create_lifetime(self.storage, self.config, 'test lifetime')

    def test_explicit_new_individual_separates_files_and_keeps_previous_history(self):
        first = self.create()
        database = Path(first['database'])
        before = database.read_bytes()
        report = save_report(database, 'test', {'individual_id': first['individual_id']})
        second = self.create()
        self.assertNotEqual(first['individual_id'], second['individual_id'])
        self.assertEqual(database.read_bytes(), before)
        self.assertEqual(database.parent.name, first['individual_id'])
        self.assertEqual(Path(second['database']).parent.name, second['individual_id'])
        self.assertEqual(report.parent.parent, database.parent)
        self.assertEqual(resolve_runtime_database(config=self.config), Path(second['database']))
        self.assertEqual(verify(database)['last_state_version'], 0)
        self.assertEqual(verify(second['database'])['last_state_version'], 0)

    def test_sessions_keep_same_directory_identity_versions_and_internal_history(self):
        registered = self.create()
        database = Path(registered['database'])
        core = ACore(database, FakeBridge())
        try:
            for x in (0, 1, 2, 3):
                core.accept_observation(observation(x))
            old_internal = deepcopy(core.state.internal_state)
            old_version = core.state.state_version
        finally:
            core.shutdown()
        resumed = ACore(resolve_runtime_database(config=self.config), FakeBridge())
        try:
            self.assertEqual(resumed.state.individual_id, registered['individual_id'])
            self.assertGreater(resumed.state.state_version, old_version)
            self.assertEqual(encode(resumed.state.internal_state), encode(old_internal))
            self.assertEqual(resolve_runtime_database(config=self.config), database)
            self.assertEqual(len(list(self.storage.iterdir())), 1)
        finally:
            resumed.shutdown()
        self.assertTrue(verify(database)['valid_state_chain'])

    def test_running_individual_cannot_be_replaced_by_initialization(self):
        first = self.create()
        pin = self.config.read_bytes()
        core = ACore(first['database'], FakeBridge())
        try:
            with self.assertRaises(ExperimentInUse):
                self.create()
            self.assertEqual(self.config.read_bytes(), pin)
            self.assertEqual(len(list(self.storage.iterdir())), 1)
        finally:
            core.shutdown()

    def test_missing_selected_database_requires_explicit_new_individual_option(self):
        old = {'database': str(self.directory / 'absent.db'), 'individual_id':'A-missing', 'role':'mainline'}
        self.config.write_text(json.dumps(old), encoding='utf-8')
        before = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'replace-missing-selection'):
            self.create()
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.storage.exists())
        with self.assertRaisesRegex(ValueError, 'database is missing'):
            resolve_runtime_database(config=self.config)

    def test_explicit_missing_pointer_replacement_preserves_pin_and_other_data(self):
        old_db = self.directory / 'missing-individual' / 'individual.db'
        old_db.parent.mkdir()
        retained = old_db.parent / 'retained-history.txt'
        retained.write_bytes(b'old auxiliary data remains')
        old = {'database': str(old_db), 'individual_id':'A-missing', 'role':'mainline'}
        self.config.write_text(json.dumps(old), encoding='utf-8')
        pin = self.config.read_bytes()
        result = create_lifetime(self.storage, self.config, 'new test', replace_missing_selection=True)
        self.assertNotEqual(result['individual_id'], old['individual_id'])
        self.assertTrue(result['previous_database_missing'])
        self.assertFalse(result['previous_history_preserved'])
        self.assertFalse(result['original_individual_resumed'])
        self.assertEqual((Path(result['directory']) / 'previous-selection.json').read_bytes(), pin)
        self.assertEqual(retained.read_bytes(), b'old auxiliary data remains')
        self.assertFalse(old_db.exists())
        self.assertEqual(resolve_runtime_database(config=self.config), Path(result['database']))
        self.assertEqual(verify(result['database'])['last_state_version'], 0)

    def test_missing_option_cannot_bypass_existing_identity_mismatch_or_running_lease(self):
        first = self.create()
        core = ACore(first['database'], FakeBridge())
        try:
            with self.assertRaises(ExperimentInUse):
                create_lifetime(self.storage, self.config, replace_missing_selection=True)
        finally: core.shutdown()
        pin = json.loads(self.config.read_text(encoding='utf-8'))
        pin['individual_id'] = 'A-wrong'
        self.config.write_text(json.dumps(pin), encoding='utf-8')
        before = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'individual_id differs'):
            create_lifetime(self.storage, self.config, replace_missing_selection=True)
        self.assertEqual(self.config.read_bytes(), before)

    def test_snapshot_branch_is_separate_and_never_switches_mainline(self):
        first = self.create()
        database = Path(first['database'])
        store = EventStore(database)
        try:
            snapshot = store.save_snapshot(0, 'test')
        finally:
            store.close()
        source = database.read_bytes()
        pin = self.config.read_bytes()
        branch = create_branch(database, snapshot, self.storage)
        target = Path(branch['branch_database'])
        self.assertEqual(target.parent.name, branch['branch_individual_id'])
        self.assertNotEqual(target.parent, database.parent)
        self.assertEqual(self.config.read_bytes(), pin)
        self.assertEqual(database.read_bytes(), source)
        self.assertEqual(resolve_runtime_database(branch_database=target, config=self.config), target)
        self.assertEqual(json.loads((target.parent / 'lifetime.json').read_text())['role'], 'snapshot_branch')
        self.assertTrue(verify(target)['valid_state_chain'])

    def test_default_audit_commands_follow_pin_and_keep_separate_nonoverwritten_reports(self):
        from individual import experiment_audit, policy_audit, inspect
        first = self.create()
        database = Path(first['database'])
        before = database.read_bytes()
        second = self.create()
        for command in (inspect.main, experiment_audit.main, policy_audit.main, experiment_audit.main):
            with patch('sys.argv', ['audit']), patch('individual.lifetime.resolve_runtime_database', return_value=database), redirect_stdout(StringIO()):
                command()
        reports = list((database.parent / 'reports').glob('*.json'))
        self.assertEqual(len(reports), 3)
        self.assertTrue(all(json.loads(p.read_text(encoding='utf-8'))['individual_id'] == first['individual_id'] for p in reports))
        self.assertFalse((Path(second['database']).parent / 'reports').exists())
        self.assertEqual(database.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
