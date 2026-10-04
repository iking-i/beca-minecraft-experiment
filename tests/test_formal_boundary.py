"""Isolated baseline boundary tests; never open the selected real lifetime."""

from contextlib import closing, redirect_stderr
from copy import deepcopy
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from individual.core import ACore
from individual.events import EventStore
from individual.formal_l0 import FormalL0Engine, FormalLimits
from individual.formal_boundary import BASELINE_VERSION, RESOURCE_CAP_KEYS
from individual.limit_consequences import RAW_FIELDS, raw_consequence
from individual.decision_provenance import decision_authorship
from individual.experiment_audit import audit
from individual.policy_audit import audit_policies
from individual.observation import FrameEncoder
from individual.lifetime import fork_snapshot
from individual.state import utc_now
from tests.test_core import FakeBridge
from tests.test_structure import observation


class FormalBoundaryTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / 'individual.db'
        self.cores = []
        self.addCleanup(lambda: [c.shutdown() for c in self.cores])

    def core(self, **kwargs):
        result = ACore(self.database, FakeBridge(), initialize_lifetime=True, **kwargs)
        self.cores.append(result)
        return result

    def family(self):
        return {p.name: p.read_bytes() for p in self.database.parent.glob('individual.db*') if p.is_file()}

    def events(self, kind):
        with closing(sqlite3.connect(self.database)) as db:
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM events WHERE event_type=? ORDER BY event_sequence', (kind,))]

    def test_first_session_locks_before_first_observation(self):
        caps = FormalLimits(units=3)
        core = self.core(physical_caps=caps)
        local = core.state.internal_state['l0_state']
        self.assertEqual(local['locked_caps'], asdict(caps))
        self.assertEqual(local['baseline_version'], BASELINE_VERSION)
        self.assertTrue(local['formal_condition_id'].startswith('C-'))
        self.assertEqual(len(self.events('FORMAL_CAPS_LOCKED')), 1)
        self.assertEqual(core.state.environment_sequence, 0)

    def test_same_conditions_restart_and_session_keep_identity_version_lineage_and_lock(self):
        caps = FormalLimits(history=1)
        core = self.core(physical_caps=caps)
        for x in (0, 1, 0, 2): core.accept_observation(observation(x))
        core.shutdown()
        before = core.state
        resumed = self.core(physical_caps=caps)
        self.assertEqual(resumed.state.individual_id, before.individual_id)
        self.assertEqual(resumed.state.state_version, before.state_version + 1)
        self.assertEqual(resumed.state.internal_state, before.internal_state)
        resumed.end_session()
        resumed.begin_session({'experiment_profile': 'arbitrary_session_label'})
        self.assertEqual(resumed.state.internal_state, before.internal_state)
        self.assertEqual(len(self.events('FORMAL_CAPS_LOCKED')), 1)

    def test_each_changed_logical_cap_refuses_before_store_lease_session_or_state_write(self):
        core = self.core()
        core.shutdown()
        before = self.family()
        for key, value in asdict(FormalLimits()).items():
            with self.subTest(capacity=key), \
                 patch('individual.core.EventStore', side_effect=AssertionError('Must not open writer')), \
                 patch('individual.core.ExperimentLease', side_effect=AssertionError('Must not acquire writer')):
                with self.assertRaisesRegex(ValueError, 'locked_caps'):
                    self.core(physical_caps=replace(FormalLimits(), **{key: value + 1}))
            self.assertEqual(self.family(), before)

    def test_changed_configuration_file_refuses_and_keeps_entire_database_family(self):
        core = self.core(); core.shutdown()
        path = Path(self.temp.name) / 'experiment.json'
        path.write_text(json.dumps({**asdict(FormalLimits()), 'relations': 2}), encoding='utf-8')
        before = self.family()
        with self.assertRaisesRegex(ValueError, 'locked_caps'):
            self.core(physical_caps=FormalLimits.load(path))
        self.assertEqual(self.family(), before)

    def test_interrupted_session_does_not_get_recovery_events_when_caps_mismatch(self):
        core = self.core()
        # Simulate an exited carrier with an open Session in this disposable DB only.
        core._closed = True; core._store.close(); core._lease.release()
        before = self.family()
        with self.assertRaisesRegex(ValueError, 'locked_caps'):
            self.core(physical_caps=FormalLimits(history=1))
        self.assertEqual(self.family(), before)
        self.assertEqual(self.events('SESSION_INTERRUPTED'), [])

    def test_preflight_honors_latest_lock_in_uncheckpointed_wal(self):
        store = EventStore(self.database); store.register_lifetime(); store.close()
        core = self.core(physical_caps=FormalLimits(units=3))
        files = [self.database, Path(str(self.database) + '-wal')]
        before = {p.name:p.read_bytes() for p in files if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'locked_caps'):
            self.core(physical_caps=FormalLimits(units=2))
        after = {p.name:p.read_bytes() for p in files if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(core.state.internal_state['l0_state']['locked_caps']['units'], 3)

    def test_session_switch_and_live_engine_replacement_cannot_bypass(self):
        core = self.core(); core.end_session()
        before = core.state
        event_count = core._store.connection.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        original = core._engine
        core._engine = FormalL0Engine(FormalLimits(units=1))
        try:
            with self.assertRaisesRegex(ValueError, 'locked_caps'): core.begin_session()
            self.assertEqual(core.state, before)
            self.assertEqual(core._store.connection.execute('SELECT COUNT(*) FROM events').fetchone()[0], event_count)
        finally: core._engine = original

    def test_database_trigger_prevents_lock_edit_or_removal_through_generic_transition(self):
        core = self.core()
        before = core.state
        for remove in (False, True):
            internal = deepcopy(before.internal_state)
            if remove: internal['l0_state'].pop('locked_caps')
            else: internal['l0_state']['locked_caps']['units'] += 1
            attempted = replace(before, state_version=before.state_version+1, last_update_at=utc_now(), internal_state=internal)
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'locked formal capacities'):
                core._store.transition(before, attempted, 'INVALID_TEST_WRITE', {})
            self.assertEqual(core._store.latest_state(), before)
        self.assertFalse(hasattr(core, 'set_caps'))
        self.assertFalse(hasattr(core, 'unlock_caps'))
        with self.assertRaises(AttributeError): core._engine.caps = FormalLimits(units=1)

    def test_unsealed_historical_formal_data_refuses_without_automatic_migration(self):
        store = EventStore(self.database)
        old = store.create_initial_state()
        internal = deepcopy(old.internal_state)
        internal['l0_state'] = {'profile': 'formal_l0', 'pending_consequences': [{'code': 'OLD'}]}
        store.transition(old, replace(old, state_version=1, internal_state=internal), 'HISTORICAL_FIXTURE', {})
        store.close()
        before = self.family()
        with self.assertRaisesRegex(ValueError, 'Unsealed historical'):
            self.core()
        self.assertEqual(self.family(), before)

    def test_snapshot_branch_inherits_conditions_but_has_distinct_identity(self):
        core = self.core()
        snapshot = core._store.save_snapshot()
        branch_path = Path(self.temp.name) / 'branch.db'
        branch = fork_snapshot(self.database, snapshot, branch_path)
        child = ACore(branch_path, FakeBridge())
        self.cores.append(child)
        self.assertNotEqual(child.state.individual_id, core.state.individual_id)
        self.assertEqual(child.state.internal_state['l0_state'], core.state.internal_state['l0_state'])
        self.assertFalse(branch['original_mainline'])

    def test_all_supervisor_resource_cap_changes_refuse_before_supervisor_audit_creation(self):
        from supervisor.supervisor import DEFAULT_LIMITS, cli
        from individual.formal_boundary import sensor_caps
        limits = {key: DEFAULT_LIMITS[key] for key in RESOURCE_CAP_KEYS}
        limits['body_observation_caps'] = sensor_caps(Path(__file__).resolve().parents[1] / 'minecraft/config.json')
        core = self.core(resource_caps=limits); core.shutdown()
        for key in RESOURCE_CAP_KEYS:
            before = self.family()
            changed = {**DEFAULT_LIMITS, key: DEFAULT_LIMITS[key] + 1}
            with patch('sys.argv', ['main.py', '--use-config-port']), \
                 patch('individual.lifetime.resolve_runtime_database', return_value=self.database), \
                 patch('supervisor.supervisor.load_limits', return_value=changed), \
                 patch('supervisor.supervisor.Supervisor') as supervisor, redirect_stderr(io.StringIO()):
                self.assertEqual(cli(), 1)
                supervisor.assert_not_called()
            self.assertEqual(self.family(), before)
            self.assertFalse(self.database.with_name('individual.supervisor.db').exists())

    def test_each_changed_sensor_capacity_refuses_and_defaults_are_normalized(self):
        from individual.formal_boundary import sensor_caps
        from supervisor.supervisor import DEFAULT_LIMITS
        config = Path(self.temp.name) / 'body-config.json'
        config.write_text('{}', encoding='utf-8')
        original = sensor_caps(config)
        limits = {key: DEFAULT_LIMITS[key] for key in RESOURCE_CAP_KEYS}
        limits['body_observation_caps'] = original
        core = self.core(resource_caps=limits); core.shutdown()
        before = self.family()
        for key in original:
            config.write_text(json.dumps({'observation':{**original, key: original[key] + 1}}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'locked_caps'):
                self.core(resource_caps={**limits, 'body_observation_caps': sensor_caps(config)})
            self.assertEqual(self.family(), before)

    def test_raw_only_frames_experiences_partials_pending_and_exact_event_association(self):
        core = self.core(physical_caps=FormalLimits(units=1, relations=1, history=1, evidence_window=1))
        for x in (0, 1, 1, 0, 2, 2, 0): core.accept_observation(observation(x))
        wrappers = {p['limit_id']: p for p in self.events('CURRENT_LIMIT_ENCOUNTER')}
        self.assertTrue(wrappers)
        self.assertTrue(any(p['auditor_metadata']['semantic_code']=='RELATION_CAPACITY_REACHED' for p in wrappers.values()))
        values = list(core.state.internal_state['l0_state']['pending_consequences'])
        values += [x for f in self.events('OBSERVATION_FRAME') for x in f['internal_observations']]
        values += [x for p in self.events('RECURSIVE_PARTIAL_OUTPUT') for x in p['experience']['limit_consequences']]
        values += [x for e in self.events('EXPERIENCE_FORMED') for x in e['limit_consequences']]
        forbidden = ('relation_memory','active_memory_units','observation_history','L0.relation_memory',
                     'current_organization','bounded_keyed_records_v1','RELATION_CAPACITY_REACHED','WRITE_FAILED_CAPACITY','ACTIVE_MEMORY_LIMIT')
        for value in values:
            self.assertEqual(set(value), RAW_FIELDS)
            self.assertEqual(value, wrappers[value['limit_id']]['a_facing_payload'])
            self.assertFalse(any(word in json.dumps(value) for word in forbidden))
        proof = audit(self.database)
        self.assertTrue(proof['baseline_goal_observed'])
        self.assertTrue(proof['classifications']['BEHAVIORALLY_BINDING_LIMIT'])
        self.assertTrue(proof['classifications']['LIMIT_FEEDBACK_REENTERED_RECURSION'])
        self.assertEqual(proof['recognition_status'], 'not_observed')

    def test_deleting_or_renaming_auditor_metadata_has_zero_effect_on_actual_recursion(self):
        caps = FormalLimits(units=1, relations=1, history=1)
        core = self.core(physical_caps=caps)
        for x in (0, 1, 1): core.accept_observation(observation(x))
        original = core.state.internal_state
        frame = FrameEncoder(core.state.individual_id).encode(observation(2), 4, core.state.carrier_epoch)
        results = []
        for metadata in (None, {}, {'semantic_code': 'RENAMED', 'resource_name': 'UNRELATED', 'organization_ref': 'ANY'}):
            with patch('individual.formal_l0.uuid4', side_effect=iter(range(1000, 1100))):
                if metadata is None:
                    state, signal, journal = FormalL0Engine(caps).advance(original, deepcopy(frame), core.state.state_version+1, [])
                else:
                    with patch('individual.formal_l0.auditor_metadata', return_value=deepcopy(metadata)):
                        state, signal, journal = FormalL0Engine(caps).advance(original, deepcopy(frame), core.state.state_version+1, [])
            results.append((state.to_dict(), signal.to_dict(), [(k,p) for k,p in journal if k!='CURRENT_LIMIT_ENCOUNTER']))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])
        self.assertEqual(core.state.internal_state, original)  # Copies only; original history untouched.

    def test_raw_validator_rejects_semantic_fields(self):
        core = self.core(physical_caps=FormalLimits(history=1))
        for _ in range(3): core.accept_observation(observation())
        raw = core.state.internal_state['l0_state']['pending_consequences'][0]
        with self.assertRaises(ValueError): raw_consequence({**raw, 'resource': 'relation_memory'})

    def test_session_audit_resolves_raw_consequence_origin_in_prior_session(self):
        core = self.core(physical_caps=FormalLimits(history=1))
        for _ in range(3): core.accept_observation(observation())
        prior_ids = {v['limit_id'] for v in core.state.internal_state['l0_state']['pending_consequences']}
        self.assertTrue(prior_ids)
        core.end_session(); core.begin_session()
        core.accept_observation(observation())
        self.assertTrue(prior_ids <= {v['limit_id'] for v in core.state.observation_frame['internal_observations']})
        self.assertTrue(audit(self.database, session_id='latest')['boundary_checks']['raw_consequences_separated'])

    def test_authorship_derivation_distinguishes_external_internal_test_mixed_and_unknown(self):
        cases = [({'source':'EXTERNAL_FIXED_POLICY'}, 'external_fixed_policy'),
                 ({'category':'INITIAL_EXTERNAL_POLICY'}, 'external_fixed_policy'),
                 ({'source':'INTERNAL_VARIABLE_STRUCTURE'}, 'internal_structure'),
                 ({'source':'INTERNAL_VARIABLE_STRUCTURE','parameter_binding':{'source':{'category':'INITIAL_EXTERNAL_POLICY'}}}, 'mixed_policy'),
                 ({'category':'TEST_ONLY'}, 'capability_test'),
                 ({'policy_provenance':{'data_source':'INTERNAL_VARIABLE_STRUCTURE'}}, 'unattributed'),
                 ({'source':'INTERNAL_VARIABLE_STRUCTURE','policy_provenance':{'sampling':{'category':'INITIAL_EXTERNAL_POLICY'}}}, 'external_fixed_policy')]
        for selection, author in cases:
            self.assertEqual(decision_authorship(selection)['initiator'], author)

    def test_auditors_reject_external_sampling_mislabeled_as_internal(self):
        core = self.core()
        for _ in range(4): core.accept_observation(observation())
        core.execute_discrete_action()
        good = deepcopy(core.state.latest_action)
        self.assertEqual(good['initiator'], 'external_fixed_policy')
        self.assertTrue(audit_policies(self.database)['boundary_checks_passed'])
        bad = {**good, 'action_id':'test-only-false-label', 'initiator':'internal_structure'}
        core._transition('ACTION_REQUESTED', bad)  # Deliberate isolated negative fixture.
        self.assertFalse(audit(self.database)['boundary_checks']['action_authorship_consistent'])
        self.assertFalse(audit_policies(self.database)['boundary_checks_passed'])


if __name__ == '__main__': unittest.main()
