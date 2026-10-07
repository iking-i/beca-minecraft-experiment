"""FROI-1 interface/regression controls. ALL observations here are TEST_ONLY.

These controls do not stand in for formal live T1--T5 acceptance.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experimental.gsc0.engine import Caps, Condition
from experimental.gsc0.model import Binding, PortBinding, Witness, encode
from individual.core import ACore
from individual.formal_l0 import FormalLimits, select_uniform_action
from individual.internal_state import InternalState
from individual.observation import FrameEncoder
from integration.froi import (History, OrganizationSession, ReadRequest, advance_detached,
    canonical, consume, encode_input, history_from_store, produce)
from tests.test_core import FakeBridge
from tests.test_structure import observation


class CapturingSession(OrganizationSession):
    def read(self, *args):
        result = super().read(*args)
        self.handle = result[0]
        return result


def historical_test_organization(store, state, caps):
    """Explicit frozen FROI-1 test source, never a production CLI fallback."""
    return OrganizationSession(history_from_store(store, state), caps)


class FroiTests(unittest.TestCase):
    def setUp(self):
        parent = Path('.test-tmp'); parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.cores = []
        self.addCleanup(self.close)

    def close(self):
        for core in self.cores:
            core.shutdown()

    def core(self, caps=None, physical=None):
        core = ACore(Path(self.temp.name) / f'{len(self.cores)}.db', FakeBridge(),
                     organization_factory=historical_test_organization,
                     initialize_lifetime=True, froi=True, froi_caps=caps,
                     physical_caps=physical or FormalLimits(history=100, evidence_window=100))
        self.cores.append(core)
        return core

    def prepare(self):
        core = self.core()
        histories = []
        for _ in range(4):
            core.accept_observation(observation())
            histories.append(history_from_store(core._store, core.state))
        state = core.state
        frame = FrameEncoder(state.individual_id).encode(observation(), state.environment_sequence+1, state.carrier_epoch)
        session = CapturingSession(histories[-1], core._froi_caps)
        normal = core._engine.advance(state.internal_state, deepcopy(frame), state.state_version+1, [], organization=session)
        self.assertTrue(session.handle.complete)
        return core, histories, frame, session.handle, normal

    def partial(self, output):
        return next(p for k,p in output[2] if k == 'RECURSIVE_PARTIAL_OUTPUT')

    def events(self, core, kind):
        return [json.loads(x[0]) for x in core._store.connection.execute(
            'SELECT payload FROM events WHERE event_type=? ORDER BY event_sequence', (kind,))]

    def test_mechanical_codec_all_records_and_original_sources(self):
        core, histories, _, handle, _ = self.prepare()
        encoded = encode_input(histories[-1], handle.request)
        records, _, registry = histories[-1].material()
        bindings = tuple(s.fact for s in encoded.seeds if isinstance(s.fact, Binding))
        self.assertEqual(len(bindings), len(records))
        self.assertEqual({b.value.value for b in bindings}, {r[0]['outcome'] for r in records})
        self.assertTrue(all(s.rule == 'INPUT' for s in encoded.seeds))
        self.assertFalse(any(s.fact.key[0] == 'Eq' for s in encoded.seeds))
        self.assertFalse(any(b.variable == handle.request.relation.ports[0] for b in bindings))
        self.assertEqual(len(registry), len(set(registry)))

    def test_complete_handle_immutable_and_all_graph_roots_registered(self):
        _, _, _, handle, _ = self.prepare()
        with self.assertRaises(FrozenInstanceError):
            handle.status = 'INVALID'
        registry = json.loads(handle.registry_json)
        self.assertTrue(all(root[1] in registry for root in handle.roots))
        supports, witnesses = dict(handle.supports), dict(handle.root_witnesses)
        for fact in handle.graph:
            self.assertTrue(supports[fact.key])
            self.assertTrue(witnesses[fact.key])
        self.assertTrue(all(f.key[0] != 'Composite' for f in handle.graph))

    def test_consumer_reads_actual_shared_and_portbind_and_all_supports(self):
        _, _, _, handle, normal = self.prepare()
        read = consume(handle, handle.request)
        self.assertTrue(read.succeeded)
        self.assertEqual({k[0] for k in read.consumed_keys}, {'Shared', 'PortBind'})
        self.assertEqual(read.outcomes, tuple(self.partial(normal)['processing']['expected_outcomes']))
        self.assertTrue(all(p for _,p in read.supports))
        self.assertTrue(all(p for _,p in read.roots))

    def test_missing_shared_or_portbind_cannot_read_raw_history_or_old_table(self):
        core, histories, frame, handle, _ = self.prepare()
        for kind in (Witness, PortBinding):
            masked = replace(handle, graph=tuple(f for f in handle.graph if not isinstance(f, kind)))
            self.assertFalse(consume(masked, masked.request).succeeded)
        erased = deepcopy(core.state.internal_state); erased['relations'] = {}
        session = OrganizationSession(histories[-1], core._froi_caps)
        output = core._engine.advance(erased, deepcopy(frame), core.state.state_version+1, [], organization=session)
        self.assertTrue(self.partial(output)['processing']['read_succeeded'])

    def test_history_counterfactual_identical_frame_condition_and_other_state(self):
        core, histories, frame, handle, _ = self.prepare()
        # Two complete recorded prefixes, not hand-deleted target relations.
        a, b = histories[-1], histories[1]
        ea, eb = encode_input(a, handle.request), encode_input(b, handle.request)
        nodes = {n.key:n for n in (*ea.condition.nodes, *eb.condition.nodes)}
        values = {v.key:v for v in (*ea.condition.values, *eb.condition.values)}
        condition = Condition(tuple(sorted(nodes.values(), key=lambda x:encode(x.key))),
                              tuple(sorted(values.values(), key=lambda x:encode(x.key))), ea.condition.signatures)
        ha, hb = (produce(h, handle.request, core._froi_caps, condition) for h in (a,b))
        self.assertTrue(ha.complete and hb.complete)
        self.assertNotEqual(ha.graph_content(), hb.graph_content())
        original = deepcopy(core.state.internal_state)
        outputs = [advance_detached(core._engine, original, frame, core.state.state_version+1, [], h) for h in (ha,hb)]
        self.assertTrue(self.partial(outputs[0])['processing']['read_succeeded'])
        self.assertFalse(self.partial(outputs[1])['processing']['read_succeeded'])
        self.assertTrue(outputs[1][0].l0_state['pending_consequences'])
        self.assertEqual(original, core.state.internal_state)

    def test_effect_screening_keeps_history_graph_and_inputs_no_producer_call(self):
        core, histories, frame, handle, _ = self.prepare()
        original = deepcopy(core.state.internal_state)
        before = canonical((histories[-1].events, handle.audit(), frame.to_dict(), original))
        with patch('integration.froi.Engine.run', side_effect=AssertionError('No recomputation allowed')):
            ordinary = advance_detached(core._engine, original, frame, core.state.state_version+1, [], handle)
            screened = advance_detached(core._engine, original, frame, core.state.state_version+1, [], handle, screen_effect=True)
        self.assertTrue(self.partial(ordinary)['processing']['read_succeeded'])
        self.assertFalse(self.partial(screened)['processing']['read_succeeded'])
        raw = screened[0].l0_state['pending_consequences']
        self.assertTrue(raw)
        self.assertNotEqual(ordinary[0].l0_state['pending_consequences'], raw)
        self.assertEqual(before, canonical((histories[-1].events, handle.audit(), frame.to_dict(), original)))
        metadata = next(p['auditor_metadata'] for k,p in screened[2] if k=='CURRENT_LIMIT_ENCOUNTER')
        self.assertEqual(metadata['classification'], 'TEST_ONLY_INTERVENTION')
        self.assertFalse(metadata['physical_capacity_exhaustion_claimed'])

    def test_detached_effect_state_cannot_write_back_to_a(self):
        core, _, frame, handle, _ = self.prepare()
        state = advance_detached(core._engine, core.state.internal_state, frame, core.state.state_version+1, [],
                                 handle, screen_effect=True)[0]
        before = core.state
        with self.assertRaisesRegex(ValueError, 'cannot be persisted'):
            core._transition('ILLEGAL_TEST_WRITE', {}, internal_state=state.to_dict())
        self.assertEqual(core.state, before)

    def test_resource_limit_is_not_complete_and_raw_failure_reenters(self):
        core = self.core(Caps(nodes=1))
        for _ in range(3):core.accept_observation(observation())
        formed = self.events(core, 'FROI_ORGANIZATION_FORMED')[-1]
        self.assertEqual(formed['status'], 'RESOURCE_LIMIT')
        self.assertFalse(formed['closure_complete'])
        raw = deepcopy(core.state.internal_state['l0_state']['pending_consequences'])
        self.assertTrue(raw)
        core.accept_observation(observation())
        partial = self.events(core, 'RECURSIVE_PARTIAL_OUTPUT')[-1]
        for failure in raw:
            self.assertIn(failure, partial['experience']['limit_consequences'])
            self.assertIn(failure['limit_id'], partial['processing']['consumed_limit_ids'])

    def test_invalid_material_never_uses_legacy_answer(self):
        core, histories, frame, _, _ = self.prepare()
        history = histories[-1]
        invalid = replace(history, events=tuple(s for s in history.events if json.loads(s)['event_type']!='OBSERVATION_FRAME'))
        output = core._engine.advance(core.state.internal_state, deepcopy(frame), core.state.state_version+1, [],
                                     organization=OrganizationSession(invalid, core._froi_caps))
        processing = self.partial(output)['processing']
        self.assertFalse(processing['read_succeeded'])
        self.assertEqual(processing['organization_read']['organization_status'], 'INVALID')
        self.assertTrue(core.state.internal_state['relations'])

    def test_raw_history_retained_beyond_active_window_and_no_current_self_answer(self):
        core = self.core(physical=FormalLimits(history=1))
        for _ in range(4): core.accept_observation(observation())
        history = history_from_store(core._store, core.state)
        self.assertEqual(len(core.state.internal_state['observation_history_window']), 1)
        self.assertEqual(len(history.material()[0]), 3)
        formed = self.events(core, 'FROI_ORGANIZATION_FORMED')[-1]
        current_id = core.state.observation_frame['frame_id']
        # Prior historical records never contain the current unfinished experience.
        historical = [r for r in formed['input_registry'].values() if r.get('event_type')=='EXPERIENCE_FORMED']
        self.assertTrue(historical)
        self.assertTrue(all(current_id not in r['payload']['frame_ids'] for r in historical))

    def test_first_frames_and_sample_gap_do_not_manufacture_query(self):
        core = self.core()
        with patch('integration.froi.produce', side_effect=AssertionError('No actual read requested')):
            for _ in range(2):core.accept_observation(observation())
            core._body_epoch += 1
            core.accept_observation(observation())
        self.assertEqual(self.events(core, 'FROI_ORGANIZATION_FORMED'), [])

    def test_boundary_mismatch_is_explicit_not_empty_success(self):
        _, _, _, handle, _ = self.prepare()
        other = replace(handle.request, source_state_version=handle.request.source_state_version+1)
        self.assertEqual(consume(handle, other).status, 'BOUNDARY_MISMATCH')

    def test_old_reference_keeps_original_epoch_not_current_epoch(self):
        _, history, _, handle, _ = self.prepare()
        raw = handle.request.frame; raw['body_epoch'] += 1
        request = replace(handle.request, frame_json=canonical(raw))
        self.assertEqual(request.scope, handle.request.scope)
        self.assertEqual(request.origin, handle.request.origin)
        encoded = encode_input(history[-1], request)
        self.assertIn(handle.request.relation.ports[0], encoded.condition.nodes)

    def test_profile_and_capacities_locked_on_resume_before_any_writer(self):
        core = self.core()
        core.accept_observation(observation())
        database = core._store.path
        core.shutdown()
        before = database.read_bytes()
        for enabled, caps in ((False, Caps()), (True, Caps(nodes=2))):
            with patch('individual.core.EventStore', side_effect=AssertionError('Writer forbidden')):
                with self.assertRaisesRegex(ValueError, 'locked FROI'):
                    ACore(database, FakeBridge(), froi=enabled, froi_caps=caps)
        self.assertEqual(before, database.read_bytes())

    def test_action_sampler_remains_independent_of_organization_effect(self):
        core, _, frame, handle, _ = self.prepare()
        outputs = [advance_detached(core._engine, core.state.internal_state, frame, core.state.state_version+1, [],
                                   handle, screen_effect=screen)[0] for screen in (False,True)]
        a, b = (InternalState.from_dict(x.to_dict()) for x in outputs)
        self.assertEqual(select_uniform_action(a, a.l0_state['current_pattern'], (0,1,2)),
                         select_uniform_action(b, b.l0_state['current_pattern'], (0,1,2)))


if __name__ == '__main__':
    unittest.main()
