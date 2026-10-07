"""TEST_ONLY current-state carrier controls; no Minecraft or canonical DB writes."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import pickle
import tempfile
import sqlite3
import time
import unittest
from unittest.mock import patch

from experimental.gsc0.engine import Caps
from individual.core import ACore
from individual.observation import FrameEncoder
from integration.current_structure import CurrentStructureSource, current_organization
from integration.froi import canonical, consume
from integration.froi_worker import JobSpec, execute, validate_result
from tests.test_core import FakeBridge
from tests.test_structure import observation


class CurrentStructureRuntimeTests(unittest.TestCase):
    def setUp(self):
        Path('.test-tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='.test-tmp')
        self.addCleanup(self.temp.cleanup)
        self.core = ACore(Path(self.temp.name) / 'current.db', FakeBridge(),
                         initialize_lifetime=True, froi=True)
        self.addCleanup(self.core.shutdown)

    def prepare(self):
        for _ in range(3):
            self.core.accept_observation(observation())
        state = self.core.state
        frame = FrameEncoder(state.individual_id).encode(observation(),
            state.environment_sequence + 1, state.carrier_epoch)
        session = current_organization(None, state, self.core._froi_caps)
        session.session_id = state.session_id
        checkpoint = self.core._engine.prepare_read_checkpoint(state.internal_state,
            frame, state.state_version + 1, [], organization=session)
        job = JobSpec.create(session.history, checkpoint.frame, checkpoint.feedback,
            checkpoint.payload['state_version'], state.session_id, session.caps)
        return state, checkpoint, job

    def test_default_runtime_never_reads_external_events(self):
        with (patch('integration.froi.history_from_store', side_effect=AssertionError('history read')),
              patch('integration.froi.History.material', side_effect=AssertionError('history material'))):
            for _ in range(4):
                self.core.accept_observation(observation())
        formed = self.core._store.connection.execute(
            "select payload from events where event_type='FROI_ORGANIZATION_FORMED' order by event_sequence desc limit 1").fetchone()
        self.assertFalse(json.loads(formed[0])['runtime_source']['external_history_loaded'])

    def test_external_audit_growth_does_not_change_job_or_checkpoint(self):
        state, checkpoint, job = self.prepare()
        db = self.core._store.connection
        before = db.execute('select count(*) from events').fetchone()[0]
        # Deliberately unusable historical input: the runtime must never parse it.
        with db:
            for _ in range(1000):
                self.core._store._insert_event(self.core._state, 'OBSERVATION_FRAME',
                    {'TEST_ONLY_EXTERNAL_SENTINEL': 'x' * 1024})
        with (patch('integration.froi.history_from_store', side_effect=AssertionError('history read')),
              patch('integration.froi.History.material', side_effect=AssertionError('history material'))):
            source = CurrentStructureSource.capture(self.core.state)
            new_job = replace(job, history=source)
            session = current_organization(None, self.core.state, self.core._froi_caps)
            session.session_id = state.session_id
            new_checkpoint = self.core._engine.prepare_read_checkpoint(state.internal_state,
                checkpoint.frame, checkpoint.payload['state_version'], [], organization=session)
        self.assertEqual(job.identity, new_job.identity)
        self.assertEqual(len(pickle.dumps(job)), len(pickle.dumps(new_job)))
        # Prefix-generated UUIDs may differ; external records never enter either checkpoint.
        self.assertNotIn('TEST_ONLY_EXTERNAL_SENTINEL', new_checkpoint.content)
        self.assertLess(abs(len(checkpoint.content) - len(new_checkpoint.content)), 100)
        self.core.accept_observation(observation())
        self.assertGreaterEqual(db.execute('select count(*) from events').fetchone()[0], before + 1000)

    def test_current_structure_and_process_survive_and_are_read(self):
        state, cp, job = self.prepare()
        result = execute(job)
        self.assertEqual(validate_result(job, result), 'RETURNED')
        read = consume(result.handle, result.handle.request)
        self.assertTrue(read.succeeded)
        self.assertEqual({k[0] for k in read.consumed_keys}, {'Shared', 'PortBind'})
        self.core.accept_observation(observation())
        after = self.core.state.internal_state
        self.assertEqual(set(state.internal_state['active_processes']), set(after['active_processes']))
        self.assertTrue(set(state.internal_state['units']) <= set(after['units']))
        self.assertTrue(set(state.internal_state['relations']) <= set(after['relations']))
        self.assertNotEqual(state.internal_state['l0_state']['feedback']['partial_id'],
                            after['l0_state']['feedback']['partial_id'])

    def test_current_relation_ablation_changes_read_without_history_fallback(self):
        _, _, job = self.prepare()
        normal = execute(job)
        raw = json.loads(job.history.structure_json)
        raw['relations'] = {}
        masked = replace(job.history, structure_json=canonical(raw))
        changed = execute(replace(job, history=masked))
        self.assertTrue(consume(normal.handle, normal.handle.request).succeeded)
        self.assertEqual(consume(changed.handle, changed.handle.request).status, 'UNRESOLVED_REFERENCE')

    def test_all_retained_relations_encoded_without_priority(self):
        _, _, job = self.prepare()
        raw = json.loads(job.history.structure_json)
        old = next(iter(raw['relations'].values()))
        extra = deepcopy(old); extra['relation_id'] = 'opaque:unrelated'
        raw['relations'][extra['relation_id']] = extra
        source = replace(job.history, structure_json=canonical(raw))
        from integration.froi import ReadRequest, ReferenceOrigin
        request = ReadRequest(job.individual_id, job.source_state_version, job.frame_json,
            json.loads(job.feedback_json)['next_relation_ref'],
            ReferenceOrigin(**json.loads(job.origin_json)['origin']))
        encoded = source.encode_current(request)
        names = {s.fact.name for s in encoded.seeds if hasattr(s.fact, 'type_id') and s.fact.type_id == 'froi.record'}
        self.assertEqual(len(names), sum(len(r['outcomes']) for r in raw['relations'].values()))

    def test_resource_limit_not_complete_and_no_fallback(self):
        _, _, job = self.prepare()
        limited = replace(job, caps_json=canonical(Caps(nodes=1).__dict__))
        result = execute(limited)
        self.assertEqual(result.handle.status, 'RESOURCE_LIMIT')
        self.assertFalse(consume(result.handle, result.handle.request).succeeded)
        self.assertFalse(result.handle.graph)

    def test_current_source_has_no_events_or_historical_material(self):
        _, cp, job = self.prepare()
        self.assertFalse(hasattr(job.history, 'events'))
        self.assertFalse(hasattr(job.history, 'material'))
        self.assertNotIn('WORLD_OBSERVATION', job.identity)
        self.assertNotIn('immutable_input_identity', cp.content)
        self.assertEqual(job.audit()['runtime_source']['cutoff_kind'], 'state_version')

    def test_store_unavailable_to_adapter(self):
        state, _, _ = self.prepare()
        class ForbiddenStore:
            def __getattribute__(self, name):
                raise AssertionError('Store access: ' + name)
        source = current_organization(ForbiddenStore(), state, self.core._froi_caps)
        self.assertIsInstance(source.history, CurrentStructureSource)

    def test_sqlite_guard_rejects_all_runtime_event_reads(self):
        db = self.core._store.connection
        statements = []
        def authorize(action, table, *rest):
            # SQLite checks FK identity columns while INSERTing states/events.
            # Allow those integrity checks, forbid reading history material.
            forbidden = action == sqlite3.SQLITE_READ and table == 'events' and rest[0] not in ('state_version', 'individual_id')
            return sqlite3.SQLITE_DENY if forbidden else sqlite3.SQLITE_OK
        db.set_authorizer(authorize)
        db.set_trace_callback(statements.append)
        try:
            for _ in range(4):
                self.core.accept_observation(observation())
        finally:
            db.set_authorizer(None)
            db.set_trace_callback(None)
        self.assertFalse(any('FROM EVENTS' in sql.upper() for sql in statements if sql.lstrip().upper().startswith('SELECT')))
        self.assertTrue(self.core.state.internal_state['relations'])

    def test_default_async_worker_reads_current_state_and_resumes(self):
        core = ACore(Path(self.temp.name) / 'async.db', FakeBridge(),
                     initialize_lifetime=True, froi=True, froi_async=True)
        self.addCleanup(core.shutdown)
        with patch('integration.froi.history_from_store', side_effect=AssertionError('history read')):
            for _ in range(3):
                core.accept_observation(observation())
            pending = core._computation
            self.assertIsInstance(pending['job'].history, CurrentStructureSource)
            self.assertLess(len(pickle.dumps(pending['job'])), 100000)
            deadline = time.monotonic() + 10
            while core._computation is not None and time.monotonic() < deadline:
                core._poll_computation()
                time.sleep(.01)
            self.assertIsNone(core._computation)
            self.assertEqual(core.state.environment_sequence, 3)
            payload = core._store.connection.execute("select payload from events where event_type='FROI_ORGANIZATION_CONSUMED' order by event_sequence desc limit 1").fetchone()[0]
            self.assertEqual(json.loads(payload)['status'], 'READ_SUCCEEDED')


if __name__ == '__main__':
    unittest.main()
