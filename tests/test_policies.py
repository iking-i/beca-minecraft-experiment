from copy import deepcopy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from individual.actions import select_action
from individual.core import ACore
from individual.internal_state import InternalState, PhysicalCaps
from individual.integration import integrate
from individual.events import EventStore
from individual.experiment_audit import audit
from individual.policies import CATEGORIES, PolicyRegistry
from individual.policy_audit import audit_policies
from individual.recursion import generate_processes, advance_processes
from tests.test_core import FakeBridge
from tests.test_structure import experience, observation


class PolicyTests(unittest.TestCase):
    def test_initial_registry_categories_and_state_copies_are_separate(self):
        a, b = InternalState(), InternalState()
        self.assertTrue(all(r['category'] in CATEGORIES and r['policy_id'] == key
                            for key, r in a.policy_registry.items()))
        for key in ('action.scoring', 'generation.quantity', 'generation.resolution',
                    'generation.stability', 'recursion.channels', 'recursion.allocation'):
            self.assertEqual(a.policy_registry[key]['category'], 'INITIAL_EXTERNAL_POLICY')
        a.policy_registry['action.scoring']['parameters']['unresolved_weight'] = 9
        self.assertEqual(b.policy_registry['action.scoring']['parameters']['unresolved_weight'], 1)
        self.assertFalse(any(r['category'] == 'INTERNAL_VARIABLE_POLICY' for r in a.policy_registry.values()))

    def test_initial_score_matches_old_formula_and_all_components_are_explained(self):
        for seed in (0, 1, 991335708):
            for count in (0, 1, 3):
                internal = InternalState()
                internal.exploration_state['random_state'] = seed
                internal.relations['X:1'] = {'unresolved': True}
                internal.exploration_state['attempts']['X:0'] = count
                old_scores = {0: 1 / (1 + count), 1: 2.0, 2: 1.0}
                old_candidates = [x for x in (0, 1, 2) if old_scores[x] == max(old_scores.values())]
                next_seed = (1664525 * seed + 1013904223) & 0xffffffff
                chosen, record = select_action(internal, 'X')
                self.assertEqual(chosen, old_candidates[next_seed % len(old_candidates)])
                self.assertEqual(record['scores'], {str(k): v for k, v in old_scores.items()})
                for key, parts in record['score_components'].items():
                    self.assertAlmostEqual(sum(parts[x]['value'] for x in ('initial_policy_component',
                        'internal_structure_component', 'temporary_evaluation_component')), record['scores'][key])
                self.assertIsNone(record['reward'])

    def test_scoring_reads_state_and_does_not_silently_relabel_manual_edits(self):
        internal = InternalState()
        internal.exploration_state['random_state'] = 1
        internal.relations['X:0'] = {'unresolved': True}
        internal.policy_registry['action.scoring']['parameters']['unresolved_weight'] = 7
        code, record = select_action(internal, 'X')
        self.assertEqual(code, 0)
        self.assertEqual(record['scores']['0'], 8)
        source = record['policy_provenance']['parameters']['unresolved_weight']
        self.assertEqual(source['value_origin'], 'untracked_state_assignment')
        self.assertEqual(source['source'], 'INITIAL_EXTERNAL_POLICY')

    def test_counterexample_provenance_and_next_generation_preserve_external_authorship(self):
        internal, caps, journal = InternalState(), PhysicalCaps(), []
        for seq, outcome in ((1, 'Y'), (2, 'Z')):
            e = experience(seq, outcome)
            generate_processes(internal, e, seq, caps, journal)
            integrate(internal, advance_processes(internal, e, caps, journal), seq, caps, journal)
        updates = [p for kind, p in journal if kind == 'POLICY_PARAMETER_UPDATED']
        self.assertEqual(len(updates), 3)
        self.assertTrue(all(p['metadata']['source'] == 'INITIAL_EXTERNAL_POLICY' for p in updates))
        self.assertTrue(all(p['metadata']['provenance']['experience_ids'] == ['exp2'] for p in updates))
        self.assertEqual(PolicyRegistry(internal).summary()['source_migrations'], 0)
        generate_processes(internal, experience(3, root='NEW:1'), 3, caps, journal)
        selected = internal.latest_generation['quantity_decision']['current_internal_state']['selected_parameter']
        self.assertEqual(selected['value'], 3)
        self.assertEqual(selected['modified_by'], internal.latest_feedback['integration_id'])
        self.assertTrue(selected['change_id'])

    def test_resource_allocation_is_separate_from_policy_migration(self):
        internal = InternalState(resource_state={'pressure': 0.9})
        internal.generation_parameters['default_quantity'] = 8
        generate_processes(internal, experience(1), 1, PhysicalCaps(processes=8), [])
        decision = internal.latest_generation['quantity_decision']
        self.assertEqual((decision['requested_quantity'], decision['granted_quantity']), (8, 4))
        self.assertEqual(decision['resource_limit']['source']['category'], 'ENVIRONMENT_CONSTRAINT')
        self.assertEqual(decision['resource_limit']['allocation_policy']['category'], 'INITIAL_EXTERNAL_POLICY')
        self.assertEqual(PolicyRegistry(internal).summary()['source_migrations'], 0)

    def test_legacy_snapshots_get_no_retroactive_claim_of_verified_history(self):
        raw = InternalState().to_dict()
        for key in ('policy_registry', 'parameter_sources', 'policy_migration_status'):
            raw.pop(key)
        raw['generation_parameters']['default_quantity'] = 3
        before = deepcopy(raw)
        imported = InternalState.from_dict(raw)
        self.assertEqual(raw, before)
        self.assertEqual(imported.parameter_sources['generation_parameters.default_quantity']['value_origin'], 'legacy_untracked')
        self.assertFalse(imported.policy_migration_status['generation.quantity']['historical_origin_verified'])

    def test_future_review_cannot_promote_fixed_rule_or_rewrite_environment(self):
        internal = InternalState()
        registry = PolicyRegistry(internal)
        for owner in ('core.identity', 'environment.capacity', 'generation.quantity'):
            with self.assertRaises(ValueError):
                registry.validate_internal_proposal({'policy_id': owner, 'provenance': {'producer_category': 'INITIAL_EXTERNAL_POLICY'}})
        before = internal.to_dict()
        result = registry.validate_internal_proposal({'policy_id': 'generation.quantity', 'provenance': {
            'producer_category': 'INTERNAL_VARIABLE_POLICY', 'process_id': 'p', 'partial_ids': ['partial'],
            'experience_ids': ['e'], 'evaluation_id': 'review'}})
        self.assertFalse(result['activated'])
        self.assertFalse(result['history_references_verified'])
        self.assertEqual(internal.to_dict(), before)


class PolicyCoreTests(unittest.TestCase):
    def test_external_verifier_waits_for_initial_state_commit(self):
        parent = Path('.test-tmp')
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            database = Path(directory) / 'initializing.db'
            store = EventStore(database)
            try:
                with self.assertRaisesRegex(ValueError, 'initialization'):
                    audit(database, check_chain=False)
            finally:
                store.close()

    def test_changes_actions_generations_are_auditable_and_identity_is_stable(self):
        parent = Path('.test-tmp')
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            database = Path(directory) / 'policies.db'
            core = ACore(database, FakeBridge(), initialize_lifetime=True)
            marker = core.state.individual_id
            try:
                for x in (0, 0, 0, 0, 0, 0, 1):
                    core.accept_observation(observation(x))
                core.execute_discrete_action()
                report = audit_policies(database)
                self.assertTrue(report['boundary_checks_passed'], report)
                self.assertEqual(report['verified_internal_policy_migrations'], 0)
                self.assertFalse(report['autonomous_policy_formation_proven'])
                self.assertEqual(core.state.individual_id, marker)
                with closing(sqlite3.connect(database)) as db:
                    initial = json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=0').fetchone()[0])
                    self.assertTrue(initial['continuity_required'])
                    self.assertEqual(initial['internal_state']['policy_registry']['generation.quantity']['individual_id'], marker)
            finally:
                core.shutdown('test_completed')


if __name__ == '__main__':
    unittest.main()
