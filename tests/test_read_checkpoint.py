"""TEST_ONLY engineering controls. No historical/live T3 is executed here."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import itertools
import json
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import patch
from uuid import UUID

from individual.formal_froi import FormalFROIEngine
from individual.formal_l0 import FormalLimits
from individual.observation import FrameEncoder
from integration.froi import (HISTORY_TYPES, OrganizationSession, ReadResult,
                              canonical, consume, history_from_store, resume_detached)
from integration.froi_worker import JobSpec
from integration.read_checkpoint import AUDIT_EVENT, ReadCheckpoint, ordered_json
from tests import test_froi as froi_controls
from tests.test_structure import observation

BASELINE_COMMIT = '4838b74f288739276011240bbaca3186a9ddade5'


def historical_interpreter():
    # Read the immutable historical Git blob, never a maintained second runtime.
    source = subprocess.run(['git', 'show', BASELINE_COMMIT + ':individual/formal_froi.py'],
                            check=True, capture_output=True).stdout.decode('utf-8')
    module = types.ModuleType('individual._checkpoint_historical_reference')
    module.__package__ = 'individual'
    exec(compile(source, '<frozen pre-checkpoint Git blob>', 'exec'), module.__dict__)
    return module


def ids():
    counter = itertools.count(100000)
    return lambda: UUID(int=next(counter))


def comparable(result):
    internal, frame, journal = result
    return canonical((internal.to_dict(), frame.to_dict(),
                      [(k, p) for k, p in journal if k != AUDIT_EVENT]))


class ReadCheckpointTests(unittest.TestCase):
    setUp = froi_controls.FroiTests.setUp
    close = froi_controls.FroiTests.close
    core = froi_controls.FroiTests.core
    partial = froi_controls.FroiTests.partial

    def checkpoint_fixture(self):
        core = self.core(physical=FormalLimits(history=1, condition_channels=1, evidence_window=1))
        for _ in range(4):
            core.accept_observation(observation())
        state = core.state
        history = history_from_store(core._store, state)
        frame = FrameEncoder(state.individual_id).encode(observation(), state.environment_sequence+1, state.carrier_epoch)
        organization = froi_controls.CapturingSession(history, core._froi_caps)
        organization.session_id = state.session_id
        checkpoint = core._engine.prepare_read_checkpoint(state.internal_state, frame,
            state.state_version+1, [], organization=organization)
        handle, read, _ = organization.read(checkpoint.frame, checkpoint.feedback, state.state_version+1)
        self.assertTrue(handle.complete)
        self.assertGreaterEqual(len(checkpoint.payload['new_limits']), 2)
        return core, checkpoint, handle, read

    def test_serialization_identity_order_and_digest(self):
        _, cp, _, _ = self.checkpoint_fixture()
        restored = ReadCheckpoint.deserialize(cp.serialize())
        self.assertEqual(restored, cp)
        self.assertEqual(restored.digest, cp.digest)
        self.assertEqual(list(restored.frame.numeric_channels), list(cp.frame.numeric_channels))
        self.assertEqual(list(restored.payload['internal']['relations']), list(cp.payload['internal']['relations']))

    def test_checkpoint_is_deeply_immutable(self):
        _, cp, _, _ = self.checkpoint_fixture()
        with self.assertRaises(FrozenInstanceError):
            cp.content = '{}'
        copy = cp.payload
        copy['frame']['internal_observations'].clear()
        self.assertTrue(cp.frame.internal_observations)

    def test_corrupted_digest_and_request_rejected(self):
        _, cp, _, _ = self.checkpoint_fixture()
        envelope = json.loads(cp.serialize()); envelope['digest'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'digest'):
            ReadCheckpoint.deserialize(canonical(envelope))
        p = cp.payload; p['request']['reference'] = 'TEST_ONLY tampered reference'
        with self.assertRaisesRegex(ValueError, 'ReadRequest'):
            ReadCheckpoint(ordered_json(p))

    def test_exact_request_uuid_and_observations_preserved(self):
        core, cp, handle, read = self.checkpoint_fixture()
        restored = ReadCheckpoint.deserialize(cp.serialize())
        self.assertEqual(restored.request, handle.request)
        self.assertEqual(restored.frame.internal_observations, cp.frame.internal_observations)
        original_limits = deepcopy(cp.payload['new_limits'])
        output = core._engine.resume_from_read_checkpoint(restored, handle, read, {})
        # Existing post-read evidence writes may legitimately add a new failure.
        # Every frozen prefix object must survive intact, not suppress that path.
        before_read = cp.payload['prior_limits'] + original_limits
        self.assertEqual(output[1].internal_observations[:len(before_read)], before_read)
        self.assertEqual(output[0].l0_state['pending_consequences'][:len(original_limits)], original_limits)

    def test_normal_resume_never_executes_prefix(self):
        core, cp, handle, read = self.checkpoint_fixture()
        with patch.object(core._engine, 'prepare_read_checkpoint', side_effect=AssertionError('prefix replay')), \
             patch('individual.formal_froi.detect_changes', side_effect=AssertionError('prefix replay')), \
             patch('integration.froi.Engine.run', side_effect=AssertionError('closure recompute')):
            output = core._engine.resume_from_read_checkpoint(cp, handle, read, {})
        self.assertTrue(self.partial(output)['processing']['read_succeeded'])

    def test_detached_branches_share_exact_checkpoint_no_prefix_or_producer(self):
        core, cp, handle, _ = self.checkpoint_fixture()
        before = canonical((cp.serialize(), handle.audit()))
        with patch.object(core._engine, 'prepare_read_checkpoint', side_effect=AssertionError('prefix replay')), \
             patch('individual.formal_froi.detect_changes', side_effect=AssertionError('prefix replay')), \
             patch('integration.froi.Engine.run', side_effect=AssertionError('closure recompute')), \
             patch.object(core._engine, 'resume_from_read_checkpoint', wraps=core._engine.resume_from_read_checkpoint) as resume:
            normal = resume_detached(core._engine, cp, handle)
            screened = resume_detached(core._engine, cp, handle, screen_effect=True)
        self.assertEqual(resume.call_count, 2)
        self.assertIs(resume.call_args_list[0].args[0], cp)
        self.assertIs(resume.call_args_list[1].args[0], cp)
        self.assertTrue(self.partial(normal)['processing']['read_succeeded'])
        self.assertFalse(self.partial(screened)['processing']['read_succeeded'])
        self.assertEqual(self.partial(normal)['experience']['experience_id'],
                         self.partial(screened)['experience']['experience_id'])
        for limit in cp.frame.internal_observations:
            self.assertIn(limit, normal[1].internal_observations)
            self.assertIn(limit, screened[1].internal_observations)
        self.assertEqual(before, canonical((cp.serialize(), handle.audit())))
        metadata = next(p['auditor_metadata'] for k,p in screened[2]
                        if k == 'CURRENT_LIMIT_ENCOUNTER' and p['auditor_metadata']['semantic_code'] == 'FROI_TEST_ONLY_EFFECT_SCREENED')
        self.assertEqual(metadata['classification'], 'TEST_ONLY_INTERVENTION')
        self.assertFalse(metadata['physical_capacity_exhaustion_claimed'])

    def test_detached_cannot_write_back_to_a(self):
        core, cp, handle, _ = self.checkpoint_fixture()
        detached = resume_detached(core._engine, cp, handle, screen_effect=True)[0]
        before = core.state
        with self.assertRaisesRegex(ValueError, 'Detached'):
            core._transition('TEST_ONLY_FORBIDDEN', {}, internal_state=detached.to_dict())
        self.assertEqual(before, core.state)

    def test_audit_artifact_is_not_history_or_internal_memory(self):
        core, cp, handle, read = self.checkpoint_fixture()
        output = core._engine.resume_from_read_checkpoint(cp, handle, read, {})
        artifact = next(p for k,p in output[2] if k == AUDIT_EVENT)
        self.assertNotIn(AUDIT_EVENT, HISTORY_TYPES)
        self.assertFalse(artifact['recursive_input'])
        self.assertEqual(artifact['category'], 'EXPERIMENT_AUDIT')
        self.assertEqual(artifact['individual_id'], handle.request.individual_id)
        self.assertEqual(artifact['session_id'], core.state.session_id)
        self.assertEqual(artifact['checkpoint_digest'], cp.digest)
        self.assertEqual(artifact['job_id'], cp.payload['job_id'])
        self.assertEqual(artifact['organization_handle_digest'], sha256(canonical(handle.audit()).encode()).hexdigest())
        self.assertNotIn('checkpoint', output[0].l0_state)
        prior = history_from_store(core._store, core.state)
        core._transition(AUDIT_EVENT, artifact)
        after = history_from_store(core._store, core.state)
        self.assertEqual(prior.events, after.events)

    def test_identity_job_handle_and_capacity_binding(self):
        core, cp, handle, _ = self.checkpoint_fixture()
        history = history_from_store(core._store, core.state)
        job = JobSpec.create(history, cp.frame, cp.feedback, cp.payload['state_version'],
                             core.state.session_id, core._froi_caps)
        self.assertEqual(cp.bind_job(job), cp)
        with self.assertRaises(ValueError): cp.bind_job(replace(job, session_id='TEST_ONLY other session'))
        with self.assertRaises(ValueError): cp.verify_handle(replace(handle, history_cutoff=0))
        with self.assertRaises(ValueError): cp.verify_handle(replace(handle, request=replace(handle.request, reference='TEST_ONLY other reference')))
        wrong = FormalFROIEngine(replace(core._engine.caps, history=2), core._engine.resource_caps, core._froi_caps)
        with self.assertRaises(ValueError): cp.verify_engine(wrong)

    def test_synchronous_and_adapter_use_same_resume(self):
        core, cp, _, _ = self.checkpoint_fixture()
        frame = cp.frame
        session = OrganizationSession(history_from_store(core._store, core.state), core._froi_caps)
        with patch.object(core._engine, 'resume_from_read_checkpoint', wraps=core._engine.resume_from_read_checkpoint) as resume:
            core._engine.advance(core.state.internal_state, deepcopy(frame), cp.payload['state_version'], [], organization=session)
            self.assertEqual(resume.call_count, 1)

    def test_pre_refactor_normal_path_equivalence(self):
        core, cp, _, _ = self.checkpoint_fixture()
        baseline = historical_interpreter()
        history = history_from_store(core._store, core.state)
        # COMPLETE, real prefix failures, explicit RESOURCE_LIMIT, invalid reference,
        # no read, sample gap, and capacity-failed post-read relation writes.
        from experimental.gsc0.engine import Caps
        cases = ('complete', 'resource_limit', 'invalid', 'no_reference', 'sample_gap', 'relation_capacity', 'first_frame')
        for name in cases:
            with self.subTest(name=name):
                current = deepcopy(core.state.internal_state)
                frame = deepcopy(cp.frame)
                caps = core._froi_caps
                if name == 'resource_limit':
                    caps = Caps(operations=1)
                    current['l0_state']['froi_boundary']['caps'] = __import__('dataclasses').asdict(caps)
                if name == 'invalid': current['l0_state']['feedback']['next_relation_ref'] = 'TEST_ONLY missing reference'
                if name == 'no_reference': current['l0_state']['feedback'].pop('next_relation_ref', None)
                if name == 'sample_gap': frame.body_epoch += 1
                if name == 'first_frame':
                    current['l0_state']['previous_frame'] = None
                physical = core._engine.caps
                if name == 'relation_capacity':
                    physical = replace(physical, relations=len(current['relations']))
                    current['l0_state']['locked_caps']['relations'] = physical.relations
                    frame.numeric_channels = {k: v+1 for k,v in frame.numeric_channels.items()}
                old = baseline.FormalFROIEngine(physical, core._engine.resource_caps, caps)
                new = FormalFROIEngine(physical, core._engine.resource_caps, caps)
                with patch.object(baseline, 'uuid4', side_effect=ids()):
                    expected = old.advance(deepcopy(current), deepcopy(frame), cp.payload['state_version'], [],
                        organization=OrganizationSession(history, caps))
                with patch('individual.formal_froi.uuid4', side_effect=ids()):
                    actual = new.advance(deepcopy(current), deepcopy(frame), cp.payload['state_version'], [],
                        organization=OrganizationSession(history, caps))
                self.assertEqual(comparable(expected), comparable(actual))


if __name__ == '__main__':
    unittest.main()
