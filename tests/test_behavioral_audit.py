from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from debug.behavioral_validation import validate
from individual.behavioral_audit import action_trace, audit_behavior
from individual.bridge import ROOT


class BehavioralAuditTests(unittest.TestCase):
    def action(self):
        return {'action_id': 'action', 'action_code': 16,
            'args': {'code': 16, 'parameters': {'slot': 7}},
            'provenance': {'source_state_version': 4, 'source_structure_revision': 3,
                'frame_id': 'frame', 'integration_id': 'integration', 'selection': {
                    'source': 'EXTERNAL_FIXED_POLICY', 'policy_id': 'formal.action_sampling',
                    'seed_before': 0, 'tie_state': 1, 'available_codes': [16],
                    'parameter_binding': {'source': {'category': 'INITIAL_EXTERNAL_POLICY'},
                        'choices': [{'parameter': 'slot', 'value': 7, 'domain': list(range(9))}]}}}}

    def events(self):
        experience = {'experience_id': 'experience', 'frame_ids': ['f1','f2']}
        return [{'state_version': 2, 'event_type': 'EXPERIENCE_FORMED', 'payload': experience},
            {'state_version': 2, 'event_type': 'RECURSIVE_PARTIAL_OUTPUT', 'payload': {
                'partial_id': 'partial', 'process_id': 'process', 'experience': deepcopy(experience)}},
            {'state_version': 2, 'event_type': 'INTEGRATION_COMPLETED', 'payload': {
                'integration_id': 'integration', 'input_partial_ids': ['partial'],
                'experience_ids': ['experience'], 'operations': [{'relation_id': 'relation'}]}}]

    def test_resolved_history_is_not_a_behavior_cause_by_itself(self):
        trace = action_trace(self.action(), self.events())
        self.assertTrue(trace['resolved_history'][0]['references_resolved'])
        self.assertFalse(trace['resolved_history'][0]['behavioral_dependency_proven'])
        self.assertTrue(trace['ongoing_external_author'])
        self.assertFalse(trace['bootstrap_eligible'])
        self.assertEqual(trace['audited_authorship'], 'EXTERNAL_FIXED_POLICY')
        self.assertEqual(trace['parameter_provenance']['slot']['author'], 'INITIAL_EXTERNAL_POLICY')
        self.assertFalse(trace['behavioral_causal_closure_proven'])

    def test_bootstrap_label_only_without_prior_recursive_experience(self):
        trace = action_trace(self.action(), [])
        self.assertEqual(trace['audited_authorship'], 'PURE_EXTERNAL_BOOTSTRAP')
        self.assertFalse(trace['integration_reference_resolved'])
        self.assertFalse(trace['behavioral_causal_closure_proven'])

    def test_missing_forged_or_future_references_do_not_resolve(self):
        for mutate in ('missing', 'forged', 'future'):
            with self.subTest(mutate=mutate):
                events = self.events()
                if mutate == 'missing': events = events[1:]
                if mutate == 'forged': events[1]['payload']['experience']['frame_ids'] = ['wrong']
                if mutate == 'future': events[0]['state_version'] = 5
                self.assertFalse(action_trace(self.action(), events)['resolved_history'][0]['references_resolved'])

    def test_test_only_authorship_stays_separate(self):
        action = self.action()
        action['provenance']['selection']['category'] = 'TEST_ONLY'
        trace = action_trace(action, self.events())
        self.assertEqual(trace['audited_authorship'], 'TEST_ONLY')
        self.assertEqual(trace['parameter_provenance']['slot']['author'], 'TEST_ONLY')

    def test_internal_label_without_producer_and_counterfactual_is_not_proof(self):
        action = self.action()
        action['provenance']['selection'] = {'source': 'INTERNAL_VARIABLE_STRUCTURE',
            'parameter_binding': {'source': {'category':'INTERNAL_VARIABLE_POLICY'}}}
        trace = action_trace(action, self.events())
        self.assertEqual(trace['reported_authorship']['aggregate_source'], 'INTERNAL_VARIABLE_STRUCTURE')
        self.assertEqual(trace['audited_authorship'], 'UNVERIFIED_AUTHORSHIP')
        self.assertFalse(trace['behavioral_causal_closure_proven'])

    def test_external_parameter_binder_keeps_internal_label_mixed_and_unproven(self):
        action = self.action()
        action['provenance']['selection']['source'] = 'INTERNAL_VARIABLE_STRUCTURE'
        action['provenance']['selection'].pop('policy_id')
        trace = action_trace(action, self.events())
        self.assertEqual(trace['audited_authorship'], 'MIXED_POLICY')
        self.assertFalse(trace['behavioral_causal_closure_proven'])

    def test_auditor_refuses_uncheckpointed_wal_and_missing_db_without_creating_files(self):
        parent = ROOT/'.test-tmp'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            path = Path(temporary)/'input.db'
            with self.assertRaises(ValueError): audit_behavior(path)
            self.assertFalse(path.exists())
            path.write_bytes(b'not SQLite')
            wal = Path(str(path)+'-wal'); wal.write_bytes(b'live')
            with self.assertRaisesRegex(ValueError, 'WAL'): audit_behavior(path)
            self.assertEqual(path.read_bytes(), b'not SQLite')
            self.assertEqual(wal.read_bytes(), b'live')

    def test_two_actual_histories_and_ablation_close_recursion_but_not_behavior(self):
        parent = ROOT/'.test-tmp'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            report = validate(Path(temporary)/'individuals')
            self.assertEqual(len(set(report['validation_individual_ids'])), 2)
            self.assertTrue(report['same_bootstrap_state'])
            self.assertTrue(report['same_caps'])
            self.assertTrue(report['current_frame_equal_except_identity_and_audit_delta'])
            self.assertTrue(report['internal_relation_contents_differ'])
            self.assertTrue(report['action_commands_equal'])
            self.assertTrue(report['actual_formal_commands_equal'])
            self.assertTrue(report['parameter_domain_probes'])
            self.assertTrue(all(p['parameters_equal'] for p in report['parameter_domain_probes']))
            self.assertTrue(report['ablation']['recursive_read_changed'])
            self.assertTrue(report['ablation']['before']['processing']['read_succeeded'])
            self.assertFalse(report['ablation']['after']['processing']['read_succeeded'])
            self.assertFalse(report['ablation']['action_changed'])
            self.assertTrue(report['canonical_unchanged'])
            self.assertFalse(report['real_minecraft'])
            self.assertEqual(report['BEHAVIORAL_CAUSAL_CLOSURE'], 'failed')
            for audit in report['audits']:
                trace = audit['actions'][0]
                self.assertTrue(all(x['references_resolved'] for x in trace['resolved_history']))
                self.assertEqual(trace['audited_authorship'], 'EXTERNAL_FIXED_POLICY')
            # Read-only audit does not append Session or create sidecars on a closed DB.
            database = Path(report['databases'][0])
            before = database.read_bytes()
            audit_behavior(database)
            self.assertEqual(database.read_bytes(), before)
            self.assertFalse(Path(str(database)+'-wal').exists())


if __name__ == '__main__':
    unittest.main()
