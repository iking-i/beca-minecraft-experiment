from contextlib import closing
from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from individual.core import ACore
from individual.experiment_audit import audit
from individual.formal_l0 import FormalL0Engine, FormalLimits, select_uniform_action
from individual.inspect import verify
from individual.internal_state import InternalState
from individual.observation import FrameEncoder
from individual.policy_audit import audit_policies
from tests.test_core import FakeBridge
from tests.test_structure import observation


class FormalL0Tests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / 'individual.db'
        self.cores = []
        self.addCleanup(self.close)

    def close(self):
        for core in self.cores:
            core.shutdown()

    def core(self, caps=None, profile='formal_l0'):
        core = ACore(self.database, FakeBridge(), initialize_lifetime=True,
                     physical_caps=caps, experiment_profile=profile)
        self.cores.append(core)
        return core

    def events(self, kind):
        with closing(sqlite3.connect(self.database)) as db:
            return [(v, json.loads(raw)) for v, raw in db.execute(
                'SELECT state_version,payload FROM events WHERE event_type=? ORDER BY event_sequence', (kind,))]

    def test_one_process_repeats_and_previous_result_changes_later_processing_without_branching(self):
        core = self.core(FormalLimits(history=100, evidence_window=100))
        for _ in range(9):
            core.accept_observation(observation())
        publications = self.events('RECURSIVE_PARTIAL_OUTPUT')
        self.assertEqual(len({p['process_id'] for _, p in publications}), 1)
        self.assertEqual(len(self.events('RECURSIVE_PROCESS_CREATED')), 1)
        self.assertTrue(publications[-1][1]['processing']['outcome_previously_observed'])
        proof = audit(self.database)
        self.assertTrue(proof['classifications']['WITHIN_LAYER_RECURSION'])
        self.assertFalse(proof['classifications']['CURRENT_LIMIT_ENCOUNTER'])
        self.assertFalse(proof['formal_stage_goal_observed'])
        self.assertFalse(proof['upward_recursion_observed'])
        self.assertEqual(proof['active_recursive_layers'], ['L0'])

    def test_new_results_pressure_and_legacy_quantity_fields_do_not_cause_branching(self):
        core = self.core()
        original = deepcopy(core.state.internal_state['generation_parameters'])
        for x in (0, 1, 0, 2, 4, 0, 5):
            core.accept_resources({'pressure': 100, 'timestamp': 'external'})
            core.accept_observation(observation(x))
        self.assertEqual(len(core.state.internal_state['active_processes']), 1)
        self.assertEqual(len(self.events('RECURSIVE_PROCESS_CREATED')), 1)
        self.assertEqual(core.state.internal_state['generation_parameters'], original)
        self.assertEqual(self.events('POLICY_PARAMETER_UPDATED'), [])
        self.assertEqual(self.events('RECURSIVE_PROCESS_STATUS'), [])

    def test_full_memory_rejects_writes_and_preserves_old_records_no_eviction_compression_or_spawn(self):
        caps = FormalLimits(units=1, relations=1, history=1, outcomes_per_relation=1, evidence_window=1)
        core = self.core(caps)
        core.accept_observation(observation(0))
        first_unit = set(core.state.internal_state['units'])
        first_memory = deepcopy(core.state.internal_state['observation_history_window'])
        for x in (1, 1, 0, 2, 2, 0):
            core.accept_observation(observation(x))
        state = core.state.internal_state
        self.assertEqual(set(state['units']), first_unit)
        self.assertEqual(state['observation_history_window'], first_memory)
        self.assertEqual(len(state['relations']), 1)
        self.assertEqual(len(state['active_processes']), 1)
        codes = {p['code'] for _, p in self.events('CURRENT_LIMIT_ENCOUNTER')}
        self.assertTrue({'WRITE_FAILED_CAPACITY', 'ACTIVE_MEMORY_LIMIT', 'RELATION_CAPACITY_REACHED'} <= codes)
        for kind in ('UNIT_ARCHIVED', 'RELATION_ARCHIVED', 'DOWNWARD_FEEDBACK_UPDATED', 'POLICY_PARAMETER_UPDATED'):
            self.assertEqual(self.events(kind), [])
        self.assertTrue(audit(self.database)['behaviorally_binding_limit_observed'])
        for _, p in self.events('INTEGRATION_COMPLETED'):
            self.assertFalse(p['organization_changed'])
            self.assertFalse(any(x['operation'] in ('split','merge','remove_from_working_set') for x in p['operations']))
        self.assertTrue(verify(self.database)['valid_state_chain'])

    def test_limit_is_raw_observation_and_later_recursion_consumes_exact_failure(self):
        core = self.core(FormalLimits(history=1))
        for x in (0, 0, 0, 0):
            core.accept_observation(observation(x))
        limits = {p['limit_id']: (v, p) for v, p in self.events('CURRENT_LIMIT_ENCOUNTER')}
        found = []
        for version, partial in self.events('RECURSIVE_PARTIAL_OUTPUT'):
            for raw in partial['experience']['limit_consequences']:
                old_version, original = limits[raw['limit_id']]
                if old_version < version:
                    self.assertEqual(raw, original)
                    self.assertIn(raw['limit_id'], partial['processing']['consumed_limit_ids'])
                    found.append(raw)
        self.assertTrue(found)
        proof = audit(self.database, include_sample=True)
        self.assertTrue(proof['classifications']['LIMIT_FEEDBACK_REENTERED_RECURSION'])
        self.assertTrue(proof['limit_reentry_witnesses'])
        self.assertFalse(proof['classifications']['ARCHITECTURE_LIMIT_RECOGNITION_CANDIDATE'])
        self.assertFalse(proof['formal_stage_goal_observed'])

    def test_history_counterfactual_changes_real_relation_read(self):
        core = self.core(FormalLimits(history=100, evidence_window=100))
        for _ in range(5):
            core.accept_observation(observation())
        original = core.state.internal_state
        erased = deepcopy(original)
        erased['relations'] = {}
        engine = FormalL0Engine(FormalLimits(history=100, evidence_window=100))
        sequence = core.state.environment_sequence + 1
        outputs = []
        for state in (original, erased):
            frame = FrameEncoder(core.state.individual_id).encode(observation(), sequence, core.state.carrier_epoch)
            _, _, journal = engine.advance(state, frame, core.state.state_version+1, [])
            outputs.append(next(p for kind,p in journal if kind=='RECURSIVE_PARTIAL_OUTPUT'))
        self.assertTrue(outputs[0]['processing']['read_succeeded'])
        self.assertFalse(outputs[1]['processing']['read_succeeded'])
        self.assertNotEqual(outputs[0]['processing']['expected_outcomes'], outputs[1]['processing']['expected_outcomes'])

    def test_formal_path_never_calls_old_adaptation_engine_or_action_scoring(self):
        core = self.core(FormalLimits(history=1, units=1))
        with patch('individual.core.select_action', side_effect=AssertionError('legacy scoring called')), \
             patch('individual.structure.generate_processes', side_effect=AssertionError('legacy generation called')), \
             patch('individual.structure.integrate', side_effect=AssertionError('legacy adaptation called')):
            for x in (0, 1, 0, 2):
                core.accept_observation(observation(x))
            core.execute_discrete_action()
        selection = core.state.latest_action['provenance']['selection']
        self.assertEqual(selection['source'], 'EXTERNAL_FIXED_POLICY')
        self.assertFalse(selection['uses_attempt_count'])
        self.assertFalse(selection['uses_unresolved'])
        self.assertTrue(audit(self.database)['classifications']['EXTERNAL_POLICY_EFFECT'])
        self.assertTrue(audit_policies(self.database)['boundary_checks_passed'])

    def test_action_sampler_ignores_novelty_and_attempts_and_is_not_claimed_internal(self):
        a = InternalState(); a.exploration_state['random_state'] = 8
        b = deepcopy(a)
        b.exploration_state['attempts'] = {'sample:1':1000}
        b.relations = {'sample:1':{'unresolved': True}}
        self.assertEqual(select_uniform_action(a, 'sample', [1,2]), select_uniform_action(b, 'sample', [1,2]))

    def test_information_integration_revision_and_raw_failures_never_count_as_upward_or_recognition(self):
        core = self.core(FormalLimits(history=1))
        for _ in range(6):core.accept_observation(observation())
        state = deepcopy(core.state.internal_state)
        state['structure_revision'] = 1000000
        core._transition('TEST_REVISION', {'source':'TEST_ONLY'}, internal_state=state)
        core._transition('ARCHITECTURE_HYPOTHESIS_PROPOSED', {'source':'EXTERNAL_FIXED_POLICY',
            'problem_representation':{'target_kind':'current_organization'}, 'evidence_limit_ids':[]})
        proof = audit(self.database)
        self.assertTrue(proof['classifications']['WITHIN_LAYER_RECURSION'])
        self.assertFalse(proof['upward_recursion_observed'])
        self.assertEqual(proof['upward_recursion_count'], 0)
        self.assertFalse(proof['classifications']['ARCHITECTURE_LIMIT_RECOGNITION_CANDIDATE'])
        self.assertTrue(proof['rejected_recognition_claims'])

    def test_caps_are_immutable_and_malformed_configuration_is_rejected(self):
        caps = FormalLimits()
        with self.assertRaises(FrozenInstanceError):caps.processes = 9
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):FormalLimits(history=value)

    def test_process_slot_failure_preserves_all_legacy_lineage_no_forced_retirement(self):
        engine = FormalL0Engine(FormalLimits(processes=1))
        state = InternalState(); state.active_processes['old'] = {'process_id':'old', 'status':'ACTIVE'}
        frame = FrameEncoder('test').encode(observation(), 1)
        result, _, journal = engine.advance(state.to_dict(), frame, 1, [])
        self.assertEqual(set(result.active_processes), {'old'})
        self.assertEqual(result.active_processes['old']['status'], 'PAUSED')
        self.assertTrue(any(k=='CURRENT_LIMIT_ENCOUNTER' and p['code']=='PROCESS_SLOT_UNAVAILABLE' for k,p in journal))
        self.assertFalse(any(k=='RECURSIVE_PROCESS_CREATED' for k,_ in journal))

    def test_debug_old_policies_cannot_satisfy_formal_stage(self):
        core = self.core(profile='legacy_policy_debug')
        for x in (0,0,0,0,1,0,0):core.accept_observation(observation(x))
        proof = audit(self.database)
        self.assertEqual(proof['profile'], 'legacy_policy_debug')
        self.assertFalse(proof['formal_stage_goal_observed'])
        self.assertFalse(proof['upward_recursion_observed'])

    def test_formal_lifetime_cannot_silently_reenter_legacy_adaptation(self):
        core = self.core()
        core.accept_observation(observation())
        core.shutdown()
        before = self.database.read_bytes()
        with self.assertRaisesRegex(ValueError, 'independent debug fixture'):
            ACore(self.database, FakeBridge(), experiment_profile='legacy_policy_debug')
        self.assertEqual(self.database.read_bytes(), before)


if __name__ == '__main__':unittest.main()
