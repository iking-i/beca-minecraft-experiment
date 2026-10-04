from contextlib import closing
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from individual.actions import select_action
from individual.bridge import ROOT
from individual.change_detection import detect_changes
from individual.core import ACore
from individual.inspect import verify
from individual.internal_state import InternalState, PhysicalCaps
from individual.integration import integrate
from individual.observation import FrameEncoder
from individual.recursion import RecursiveProcess, advance_processes, generate_processes, finish_process
from individual.state import utc_now
from individual.structure import StructuralEngine
from tests.test_core import FakeBridge
from individual.experiment_audit import audit


def observation(x=0, health=20, name='arbitrary_label'):
    return {'timestamp': utc_now(), 'position': {'x': x, 'y': 64, 'z': 0},
            'health': health, 'hunger': 18, 'inventory': [{'name': name, 'type': 7, 'count': 1}],
            'nearbyEntities': [{'id': 11, 'type_id': 2, 'name': name, 'position': {'x': 3, 'y': 64, 'z': 0}}],
            'nearbyBlocks': [{'type': 5, 'name': name, 'position': {'x': 1, 'y': 63, 'z': 0}}],
            'coverage': {}, 'encoding': {'protocol_version': 'numeric-test'}}


def experience(sequence, outcome='Y', root='X:1', context=None):
    return {'experience_id': f'exp{sequence}', 'root': root, 'antecedent': root.split(':')[0],
            'action_code': 1, 'outcome': outcome, 'context': context or {'1': 10},
            'sequence_id': sequence, 'frame_id': f'f{sequence}', 'frame_ids': [f'f{sequence-1}', f'f{sequence}'],
            'action_ids': [f'a{sequence}'], 'action_statuses': ['executed'], 'causality': 'temporal_association_only'}


class StructureTests(unittest.TestCase):
    def test_inventory_numeric_channel_sums_stacks_of_the_same_type(self):
        raw = observation()
        raw['inventory'] = [{'type': 7, 'name': 'arbitrary', 'count': 2}, {'type': 7, 'name': 'arbitrary', 'count': 3}]
        encoder = FrameEncoder('A-test')
        frame = encoder.encode(raw, 1)
        self.assertEqual(frame.nearby_data['inventory'], [{'type_id': 7, 'count': 5}])
        channel = next(key for key, label in encoder.debug_mapping['channels'].items() if label == 'inventory:7.count')
        self.assertEqual(frame.numeric_channels[channel], 5)
    def test_names_have_no_effect_on_numeric_frames_structure_or_action(self):
        engines = [StructuralEngine(), StructuralEngine()]
        encoders = [FrameEncoder('A-test'), FrameEncoder('A-test')]
        states = [InternalState(), InternalState()]
        states[0].exploration_state['random_state'] = states[1].exploration_state['random_state'] = 123
        for sequence, x in enumerate([0, 1, 1, 1, 2, 2, 2], 1):
            raws = [observation(x, name='food'), observation(x, name='enemy')]
            raws[1]['timestamp'] = raws[0]['timestamp']
            frames = [encoders[i].encode(raws[i], sequence) for i in range(2)]
            self.assertEqual(frames[0].to_dict(), frames[1].to_dict())
            for i in range(2):
                states[i], _, _ = engines[i].advance(states[i].to_dict(), frames[i], sequence, [])
            self.assertEqual(states[0].units, states[1].units)
            # UUID references differ, but relational evidence/parameters/selected action cannot depend on labels.
            self.assertEqual(states[0].generation_parameters, states[1].generation_parameters)
            p = states[0].observation_history_window[-1]['unit_id']
            self.assertEqual(select_action(states[0], p), select_action(states[1], p))

    def test_difference_is_descriptive_and_partial_coverage_is_not_absence(self):
        encoder = FrameEncoder('A-test')
        a = encoder.encode(observation(0), 1)
        raw = observation(1, health=19)
        raw['nearbyEntities'] = []
        raw['coverage'] = {'entitiesTruncated': True}
        b = encoder.encode(raw, 2)
        delta = detect_changes(a, b, ['a1']).to_dict()
        self.assertTrue({'increased', 'decreased', 'unobserved'} <= {c['kind'] for c in delta['changes']})
        self.assertEqual(delta['after_action_ids'], ['a1'])
        self.assertNotIn('danger', json.dumps(delta))
        self.assertTrue(detect_changes(a, replace(b, body_epoch=1)).sample_gap)

    def test_process_uploads_repeatedly_and_parallel_outputs_count_one_experience(self):
        internal = InternalState()
        journal = []
        caps = PhysicalCaps()
        first = experience(1, context={'1': 10, '2': 20})
        generate_processes(internal, first, 10, caps, journal)
        ids = list(internal.active_processes)
        self.assertEqual(len(ids), 2)
        for seq in (1, 2):
            outputs = advance_processes(internal, experience(seq, context={'1': 10, '2': 20}), caps, journal)
            self.assertEqual(len(outputs), 2)
            integrate(internal, outputs, 10 + seq, caps, journal)
        self.assertEqual(internal.relations['X:1']['evidence_count'], 2)
        for pid in ids:
            publications = [p for kind, p in journal if kind == 'RECURSIVE_PARTIAL_OUTPUT' and p['process_id'] == pid]
            self.assertEqual([p['publication_number'] for p in publications], [1, 2])

    def test_context_questions_and_finer_resolution_change_actual_computation(self):
        e = experience(1, context={'1': 0.75, '2': 2.25})
        a = RecursiveProcess('a', 0, 'X:1', {'context_channel': '1', 'resolution': 1.0})
        b = RecursiveProcess('b', 0, 'X:1', {'context_channel': '2', 'resolution': 1.0})
        fine = RecursiveProcess('fine', 0, 'X:1', {'context_channel': '1', 'resolution': 0.5})
        outputs = [p.publish_partial_result(e) for p in (a, b, fine)]
        self.assertEqual([o['condition']['interval_index'] for o in outputs], [0, 2, 1])
        internal, journal = InternalState(), []
        integrate(internal, outputs, 1, PhysicalCaps(), journal)
        self.assertEqual(internal.relations['X:1']['evidence_count'], 1)
        self.assertEqual(len(internal.relations['X:1']['conditional_evidence']), 3)

    def test_rare_counterexample_survives_repetition_and_changes_next_generation(self):
        internal, caps, journal = InternalState(), PhysicalCaps(), []
        for seq in range(1, 5):
            e = experience(seq)
            generate_processes(internal, e, seq, caps, journal)
            outputs = advance_processes(internal, e, caps, journal)
            if outputs:
                integrate(internal, outputs, seq, caps, journal)
        self.assertEqual(internal.generation_parameters['pattern_quantities']['X:1'], 1)
        e = experience(5, 'Z', context={'1': 99})
        generate_processes(internal, e, 5, caps, journal)
        integrate(internal, advance_processes(internal, e, caps, journal), 5, caps, journal)
        self.assertEqual(set(internal.relations['X:1']['outcomes']), {'Y', 'Z'})
        self.assertTrue(internal.relations['X:1']['unresolved'])
        self.assertTrue(internal.relations['X:1']['condition_candidates'])
        old_feedback = internal.latest_feedback['integration_id']
        generate_processes(internal, experience(6, 'Y'), 6, caps, journal)
        self.assertEqual(internal.latest_generation['requested_quantity'], 3)
        self.assertEqual(internal.latest_generation['feedback_integration_id'], old_feedback)
        for seq in range(6, 20):
            outputs = advance_processes(internal, experience(seq), caps, journal)
            integrate(internal, outputs, seq, caps, journal)
        self.assertEqual(internal.relations['X:1']['outcomes']['Z']['evidence_count'], 1)
        self.assertEqual(set(internal.relations['X:1']['outcomes']), {'Y', 'Z'})

    def test_feedback_reduces_next_unknown_question_quantity(self):
        internal, caps, journal = InternalState(), PhysicalCaps(), []
        for seq in range(1, 4):
            e = experience(seq, context={'1': 0, '2': 1})
            generate_processes(internal, e, seq, caps, journal)
            integrate(internal, advance_processes(internal, e, caps, journal), seq, caps, journal)
        self.assertEqual(internal.generation_parameters['default_quantity'], 1)
        generate_processes(internal, experience(4, root='NEW:1'), 4, caps, journal)
        self.assertEqual(internal.latest_generation['requested_quantity'], 1)
        self.assertEqual(internal.latest_generation['granted_quantity'], 1)
        self.assertIsNotNone(internal.latest_generation['feedback_integration_id'])

    def test_lifecycle_and_physical_capacity_are_logged(self):
        internal, caps, journal = InternalState(), PhysicalCaps(processes=2), []
        generate_processes(internal, experience(1, context={'1': 1, '2': 2}), 1, caps, journal)
        pid = next(iter(internal.active_processes))
        finish_process(internal, pid, 'PAUSED', 'test_pause', journal)
        generate_processes(internal, experience(2), 2, caps, journal)
        self.assertEqual(internal.active_processes[pid]['status'], 'ACTIVE')
        generate_processes(internal, experience(3, root='NEW:1'), 3, caps, journal)
        self.assertLessEqual(len(internal.active_processes), caps.processes)
        self.assertTrue(any(kind == 'RECURSIVE_PROCESS_STATUS' and p['reason'] == 'physical_working_capacity' for kind, p in journal))

    def test_resource_pressure_changes_working_allocation_without_reward(self):
        internal = InternalState(resource_state={'pressure': 0.9})
        caps, journal = PhysicalCaps(processes=8), []
        internal.generation_parameters['default_quantity'] = 8
        generate_processes(internal, experience(1), 1, caps, journal)
        self.assertEqual(len(internal.active_processes), 4)
        self.assertEqual(internal.latest_generation['requested_quantity'], 8)
        self.assertEqual(internal.latest_generation['granted_quantity'], 4)

    def test_whole_relation_is_archived_at_capacity_without_voting_away_exceptions(self):
        internal, caps, journal = InternalState(), PhysicalCaps(outcomes_per_relation=2), []
        for seq, outcome in enumerate(('Y', 'Y', 'Y', 'Z', 'NEW'), 1):
            value = experience(seq, outcome)
            integrate(internal, [{'partial_id': f'p{seq}', 'experience': value}], seq, caps, journal)
        archives = [p['relation'] for kind, p in journal if kind == 'RELATION_ARCHIVED']
        self.assertEqual(len(archives), 1)
        self.assertEqual(set(archives[0]['outcomes']), {'Y', 'Z'})
        self.assertEqual(archives[0]['outcomes']['Z']['evidence_count'], 1)
        self.assertEqual(set(internal.relations['X:1']['outcomes']), {'NEW'})


class NormalCoreTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / 'stage3.db'
        self.bridge = FakeBridge()
        self.core = ACore(self.database, self.bridge, observation_interval=0.01, initialize_lifetime=True)
        self.addCleanup(self.core.shutdown)
        self.core.start()
        self.core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 1})

    def test_default_path_is_not_smoke_policy_and_provenance_is_complete(self):
        self.assertIsNone(self.core._policy)
        with self.assertRaises(ValueError):
            self.core.execute_action({'method': 'chat', 'args': {'message': 'find food'}})
        self.core.accept_observation(observation())
        self.core.execute_discrete_action()
        action = self.core.state.latest_action
        self.core.accept_observation(observation(1))
        with closing(sqlite3.connect(self.database)) as db:
            events = [(kind, json.loads(raw)) for kind, raw in db.execute('SELECT event_type,payload FROM events ORDER BY event_sequence')]
        exp = next(p for kind, p in events if kind == 'EXPERIENCE_FORMED')
        self.assertIn(action['action_id'], exp['action_ids'])
        self.assertEqual(exp['frame_ids'][0], action['provenance']['frame_id'])
        self.assertTrue({'RECURSIVE_PROCESS_CREATED', 'RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED'} <= {k for k, _ in events})
        self.assertTrue(verify(self.database)['valid_state_chain'])

    def test_default_scheduler_pause_and_resume_use_structural_actions(self):
        self.core.tick(10)
        self.assertEqual(self.core.state.latest_action['initiator'], 'internal_structure')
        before = self.core.state.environment_sequence
        self.core.pause()
        self.assertEqual(self.core.state.status, 'paused')
        with self.assertRaises(RuntimeError):
            self.core.execute_discrete_action()
        self.core.tick(10000000000)
        self.assertGreater(self.core.state.environment_sequence, before)
        self.assertEqual(self.core.state.latest_action['initiator'], 'supervisor_pause')
        self.core.resume()
        self.core.tick(10000000001)
        self.assertEqual(self.core.state.latest_action['initiator'], 'internal_structure')

    def test_atomic_structural_events_roll_back_with_snapshot(self):
        before = self.core.state
        old = self.core._store._insert_event
        def fail(state, kind, payload):
            if kind == 'INTEGRATION_COMPLETED':
                raise RuntimeError('simulated disk failure')
            return old(state, kind, payload)
        self.core.accept_observation(observation())
        before = self.core.state
        self.core._store._insert_event = fail
        try:
            with self.assertRaises(RuntimeError):
                self.core.accept_observation(observation(1))
        finally:
            self.core._store._insert_event = old
        self.assertEqual(self.core.state, before)
        self.assertTrue(verify(self.database)['valid_state_chain'])

    def test_carrier_failure_does_not_create_new_individual_or_reward(self):
        self.core.accept_observation(observation())
        identity = self.core.state.individual_id
        self.core.accept_bridge_status({'state': 'dead', 'connected': False, 'attempt': 1})
        self.core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 1})
        self.core.accept_observation(observation(1))
        self.assertEqual(self.core.state.individual_id, identity)
        self.assertTrue(self.core.state.observation_frame['delta']['sample_gap'])
        incident = self.core.state.internal_state['continuity_incidents'][-1]
        self.assertTrue(incident['carrier_only'])
        self.assertFalse(incident['subject_death_inferred'])

    def test_audit_requires_actual_feedback_use_and_works_while_running(self):
        self.core.accept_observation(observation())
        first = audit(self.database)
        self.assertFalse(first['closed_loop_observed'])
        # Same empty-change pattern repeats, allowing the same question to publish repeatedly.
        for _ in range(5):
            self.core.accept_observation(observation())
        self.core.accept_observation(observation(1))
        result = audit(self.database)
        self.assertTrue(result['closed_loop_observed'])
        self.assertGreater(result['processes_with_repeated_publications'], 0)
        self.assertTrue(result['within_layer_witnesses'])
        self.assertEqual(result['feedback_generations'], [])  # Single-process recursion needs no branching.
        self.assertFalse(result['upward_recursion_observed'])

    def test_session_shutdown_preserves_processes_and_telemetry_is_detached(self):
        for x in (0, 1, 2):
            self.core.accept_observation(observation(x))
        telemetry = self.core.telemetry()
        telemetry['resources']['forged'] = True
        self.assertNotIn('forged', self.core.state.internal_state['resource_state'])
        ids = set(self.core.state.internal_state['active_processes'])
        self.assertTrue(ids)
        self.core.shutdown('test_finished')
        self.assertEqual(set(self.core.state.internal_state['active_processes']), ids)
        with closing(sqlite3.connect(self.database)) as db:
            ended = {json.loads(raw)['process_id'] for (raw,) in db.execute(
                "SELECT payload FROM events WHERE event_type='RECURSIVE_PROCESS_STATUS' AND state_version=?",
                (self.core.state.state_version,))}
        self.assertEqual(ended, set())


if __name__ == '__main__':
    unittest.main()
