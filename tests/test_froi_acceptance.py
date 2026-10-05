"""TEST_ONLY facility controls, never formal live T1--T5 acceptance."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
from unittest.mock import patch
import unittest

from debug.froi_acceptance_material import (ValidationArtifact, export_artifact,
    readonly, read_history, pack, digest, freeze, SCHEMA)
from debug.froi_acceptance_checks import (verify_t1,run_t2,run_t3,unscreened_replay,
    trace_t4,detached_continue,verify_t5,engine_for,HistoricalIntervention)
from integration.froi import HISTORY_TYPES, resume_detached, produce, consume, encode_input
from integration.read_checkpoint import AUDIT_EVENT, ordered_json
from experimental.gsc0.engine import Caps
from individual.formal_l0 import FormalLimits
from tests import test_froi as controls
from tests.test_structure import observation


class AcceptanceFacilityTests(unittest.TestCase):
    setUp=controls.FroiTests.setUp
    close=controls.FroiTests.close
    core=controls.FroiTests.core

    def material(self, *, failure=False, next_observation=True):
        core=self.core(caps=Caps(operations=1) if failure else None,
            physical=FormalLimits(history=1,condition_channels=1,evidence_window=1))
        for _ in range(3): core.accept_observation(observation())
        # Failure fixtures are T4-only: do not pretend they have COMPLETE artifacts.
        version=core.state.state_version
        if next_observation: core.accept_observation(observation())
        db=Path(self.temp.name)/'0.db'
        if failure: return core,db,version
        return core,export_artifact(db,version,test_fixture=True)

    def alter(self,artifact,change):
        p=artifact.payload;change(p)
        return ValidationArtifact(ordered_json(p))

    def test_artifact_serialization_round_trip_immutable(self):
        _,a=self.material();b=ValidationArtifact.deserialize(a.serialize())
        self.assertEqual(a,b);self.assertEqual(a.handle,b.handle)
        with self.assertRaises(FrozenInstanceError): a.content='{}'
        p=a.payload;p['history']={};self.assertEqual(a,b)

    def test_corrupt_artifact_digest_and_handle_rejected(self):
        _,a=self.material();p=json.loads(a.serialize());p['digest']='0'*64
        with self.assertRaises(ValueError): ValidationArtifact.deserialize(json.dumps(p))
        with self.assertRaises(ValueError): self.alter(a,lambda p:p.update(handle_digest='0'*64))

    def test_saved_handle_restored_without_closure(self):
        core,_=self.material();db=Path(self.temp.name)/'0.db'
        with patch('integration.froi.Engine.run',side_effect=AssertionError('closure')):
            a=export_artifact(db,core.state.state_version-1,test_fixture=True)
        self.assertTrue(a.handle.complete);self.assertTrue(consume(a.handle,a.checkpoint.request).succeeded)

    def test_export_never_writes_eventstore_or_history(self):
        core,a=self.material();before=freeze(a.payload['database'])
        with patch('individual.events.EventStore.transition',side_effect=AssertionError('write')):
            b=export_artifact(a.payload['database'],a.checkpoint.payload['state_version'],test_fixture=True)
        self.assertEqual(before,freeze(a.payload['database']))
        self.assertNotIn(SCHEMA,HISTORY_TYPES);self.assertEqual(a.history,b.history)

    def test_readonly_database_rejects_writes(self):
        _,a=self.material()
        import sqlite3
        with readonly(a.payload['database']) as db:
            with self.assertRaises(sqlite3.OperationalError): db.execute('DELETE FROM events')

    def test_t1_source_events_seeds_and_roots(self):
        _,a=self.material();r=verify_t1(a,fixture_control=True)
        self.assertEqual(r['status'],'PASS',r)
        self.assertTrue(r['seed_evidence']);self.assertTrue(r['registry'])

    def test_fixture_cannot_be_official_acceptance(self):
        _,a=self.material()
        self.assertEqual(verify_t1(a)['status'],'NOT_TESTABLE')
        self.assertEqual(run_t3(a)['status'],'NOT_TESTABLE')

    def test_missing_corrupt_source_detected(self):
        _,a=self.material();b=self.alter(a,lambda p:p['source_events'].pop())
        self.assertEqual(verify_t1(b,fixture_control=True)['status'],'FAIL')
        b=self.alter(a,lambda p:p['source_events'][0].update(event_id='corrupt'))
        self.assertEqual(verify_t1(b,fixture_control=True)['status'],'FAIL')

    def test_favorable_history_selection_rejected(self):
        _,a=self.material();h=a.history
        b=self.alter(a,lambda p:p.update(history=pack(replace(h,events=h.events[1:]))))
        self.assertEqual(verify_t1(b,fixture_control=True)['status'],'FAIL')

    def test_t2_only_history_intervention_and_cutoff_contract(self):
        _,a=self.material();db=a.payload['database'];cp=a.checkpoint
        h1=read_history(db,a.history.state_version);h2=read_history(db,1)
        original=cp.serialize();r=run_t2(a,[h1,h2],fixture_control=True)
        self.assertIn(r['status'],('PASS','FAIL'),r)
        self.assertIn('outputs',r,r)
        self.assertEqual(cp.serialize(),original)
        from debug.froi_acceptance_material import unpack
        for saved,h in zip(r['handles'],(h1,h2)):
            handle=unpack(saved)
            self.assertEqual(handle.request,cp.request)
            self.assertEqual(handle.history_cutoff,h.event_cutoff)
        alternate=unpack(r['handles'][1])
        with self.assertRaises(ValueError): cp.verify_handle(alternate)
        self.assertTrue(r['provenance']['checkpoint_history_inconsistency_disclosed'])

    def test_t2_rejects_fabricated_pair(self):
        _,a=self.material();h=a.history
        r=run_t2(a,[h,replace(h,events=h.events[:-1])],fixture_control=True)
        self.assertEqual(r['status'],'FAIL')

    def test_t2_complete_gate(self):
        _,a=self.material();h2=read_history(a.payload['database'],1)
        with patch('debug.froi_acceptance_checks.produce',return_value=replace(a.handle,status='RESOURCE_LIMIT')):
            r=run_t2(a,[a.history,h2],fixture_control=True)
        self.assertEqual(r['status'],'NOT_TESTABLE')

    def test_intervention_rejects_query_substitution(self):
        _,a=self.material();b=HistoricalIntervention(a.checkpoint,a.history,a.handle,a.handle.condition)
        with self.assertRaises(ValueError): b.verify_handle(replace(a.handle,request=replace(a.handle.request,reference='substitute')))

    def test_t3_unscreened_replay_with_exact_original_uuid(self):
        _,a=self.material();output=unscreened_replay(a)
        expected=a.payload['formal_snapshot']['internal_state']
        self.assertEqual(output[0].to_dict(),expected)
        self.assertEqual(output[1].to_dict(),a.payload['formal_snapshot']['observation_frame'])

    def test_t3_mismatch_gate_prevents_ablation(self):
        _,a=self.material();b=self.alter(a,lambda p:p['formal_snapshot']['internal_state'].update(structure_revision=9999))
        with patch('debug.froi_acceptance_checks.resume_detached',side_effect=AssertionError('must not screen')):
            r=run_t3(b,fixture_control=True)
        self.assertIn(r['status'],('FAIL','NOT_TESTABLE'))
        self.assertNotIn('normal',r)

    def test_t3_actual_replay_processing_mismatch_rejected(self):
        _,a=self.material()
        original=engine_for(a.checkpoint).resume_from_read_checkpoint
        def corrupt(*args,**kwargs):
            output=original(*args,**kwargs)
            output[0].structure_revision+=1
            return output
        with patch('individual.formal_froi.FormalFROIEngine.resume_from_read_checkpoint',side_effect=corrupt):
            r=run_t3(a,fixture_control=True)
        self.assertEqual(r['status'],'FAIL');self.assertFalse(r['ablation_executed'])

    def test_t3_same_checkpoint_shared_resume_only_effect(self):
        _,a=self.material();before=a.serialize()
        with (patch('individual.formal_froi.FormalFROIEngine.prepare_read_checkpoint',side_effect=AssertionError('prefix')),
              patch('integration.froi.Engine.run',side_effect=AssertionError('recompute'))):
            r=run_t3(a,fixture_control=True)
        self.assertEqual(r['status'],'PASS',r)
        self.assertEqual(a.serialize(),before)
        self.assertTrue(r['normal']['processing']['read_succeeded'])
        self.assertFalse(r['screened']['processing']['read_succeeded'])

    def test_detached_persistence_rejected(self):
        core,a=self.material();result=resume_detached(engine_for(a.checkpoint),a.checkpoint,a.handle)
        before=core.state
        with self.assertRaises(ValueError): core._transition('FORBIDDEN',{},internal_state=result[0].to_dict())
        self.assertEqual(core.state,before)

    def test_t4_exact_limit_identity_reentry(self):
        _,db,v=self.material(failure=True)
        with readonly(db) as conn:
            rows=conn.execute("SELECT payload FROM events WHERE state_version=? AND event_type='CURRENT_LIMIT_ENCOUNTER'",(v,)).fetchall()
        limits=[json.loads(r[0]) for r in rows]
        limit=next(p['limit_id'] for p in limits if p['auditor_metadata']['semantic_code']=='FROI_RESOURCE_LIMIT')
        r=trace_t4(db,limit);self.assertEqual(r['status'],'PASS',r)
        self.assertEqual(r['raw_consequence']['limit_id'],limit)

    def test_t4_missing_next_observation(self):
        _,db,v=self.material(failure=True,next_observation=False)
        with readonly(db) as conn:
            rows=conn.execute("SELECT payload FROM events WHERE state_version=? AND event_type='CURRENT_LIMIT_ENCOUNTER'",(v,)).fetchall()
        limit=next(json.loads(r[0])['limit_id'] for r in rows if json.loads(r[0])['auditor_metadata']['semantic_code']=='FROI_RESOURCE_LIMIT')
        self.assertEqual(trace_t4(db,limit)['status'],'MATERIAL_UNAVAILABLE')

    def test_detached_next_real_recorded_observation(self):
        _,a=self.material();result=resume_detached(engine_for(a.checkpoint),a.checkpoint,a.handle,screen_effect=True)
        before=freeze(a.payload['database']);r=detached_continue(a,result)
        self.assertEqual(r['status'],'PASS',r);self.assertEqual(before,freeze(a.payload['database']))
        self.assertTrue(r['output']['internal']['l0_state']['froi_detached_test_only'])

    def test_detached_no_invented_observation(self):
        _,a=self.material();result=resume_detached(engine_for(a.checkpoint),a.checkpoint,a.handle,screen_effect=True)
        b=self.alter(a,lambda p:p['next_round_events'][0].update(event_id='invented'))
        # Change specifically the next actual world event, not an unrelated row.
        b=self.alter(a,lambda p:next(r for r in p['next_round_events'] if r['event_type']=='WORLD_OBSERVATION').update(event_id='invented'))
        self.assertEqual(detached_continue(b,result)['status'],'FAIL')

    def test_detached_missing_observation(self):
        _,a=self.material(next_observation=False);result=resume_detached(engine_for(a.checkpoint),a.checkpoint,a.handle,screen_effect=True)
        self.assertEqual(detached_continue(a,result)['status'],'MATERIAL_UNAVAILABLE')

    def test_t2_continuation_preserves_intervened_history(self):
        _,a=self.material();h=read_history(a.payload['database'],1)
        r=run_t2(a,[a.history,h],fixture_control=True)
        self.assertIn('outputs',r,r)
        saved=r['outputs'][1]
        from individual.internal_state import InternalState
        from individual.observation import ObservationFrame
        output=(InternalState.from_dict(saved['internal']),ObservationFrame(**saved['frame']),saved['journal'])
        continued=detached_continue(a,output,intervention_history=h)
        self.assertEqual(continued['status'],'PASS',continued)
        self.assertEqual(continued['producer_history_digest'],digest(pack(h)))
        self.assertNotEqual(continued['producer_history_digest'],digest(pack(a.history)))
        self.assertTrue(continued['checkpoint_frame_source_material'])

    def test_t5_freeze_detects_changed_sources_database_caps(self):
        _,a=self.material();before=freeze(a.payload['database']);after=deepcopy(before)
        after['protected_source_hashes']['integration/froi.py']='corrupt'
        self.assertEqual(verify_t5(a,before,after)['status'],'FAIL')
        after=deepcopy(before);after['database_content']='corrupt'
        self.assertEqual(verify_t5(a,before,after)['status'],'FAIL')
        p=a.checkpoint.payload;p['froi_caps']['operations']+=1
        from integration.read_checkpoint import ReadCheckpoint
        cp=ReadCheckpoint(ordered_json(p))
        with self.assertRaises(ValueError): cp.verify_engine(engine_for(a.checkpoint))

    def test_t5_frozen_behavior_hash_gate(self):
        from debug.froi_acceptance_checks import frozen_contract
        root=Path(self.temp.name)
        manifest={'freeze_source_commit':'TEST_ONLY','protected_source_hashes':{'engine.py':'abc'},
            'engineering_regression':{'passed':True}}
        (root/'FROI_ACCEPTANCE_FREEZE.json').write_text(json.dumps(manifest),encoding='utf-8')
        with patch('debug.froi_acceptance_checks.ROOT',root),patch('debug.froi_acceptance_checks.protected_files',return_value={'engine.py':'abc'}):
            self.assertEqual(frozen_contract()['status'],'PASS')
        with patch('debug.froi_acceptance_checks.ROOT',root),patch('debug.froi_acceptance_checks.protected_files',return_value={'engine.py':'changed'}):
            self.assertEqual(frozen_contract()['status'],'FAIL')

    def test_t5_incomplete_other_round_cannot_pass(self):
        _,a=self.material();before=freeze(a.payload['database'])
        with patch('debug.froi_acceptance_checks.frozen_contract',return_value={'status':'PASS'}):
            r=verify_t5(a,before,before,{'T4':{'organization_statuses':['RESOURCE_LIMIT']}})
        self.assertFalse(r['checks']['all_used_organizations_COMPLETE'])
        self.assertEqual(r['status'],'FAIL')

    def test_machine_local_ports_and_lifetime_pointer_are_not_source_rules(self):
        from debug.froi_acceptance_material import protected_files
        hashes=protected_files()
        self.assertNotIn('minecraft/config.json',hashes)
        self.assertNotIn('individual/lifetime.json',hashes)
        self.assertIn('integration/froi.py',hashes)
        self.assertIn('integration/read_checkpoint.py',hashes)

    def test_runtime_does_not_import_acceptance_tooling(self):
        import ast
        for folder in ('individual','integration','minecraft','bridge','supervisor','experimental/gsc0'):
            for path in Path(folder).rglob('*.py'):
                if '__pycache__' in path.parts or 'node_modules' in path.parts: continue
                tree=ast.parse(path.read_text(encoding='utf-8-sig'))
                modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
                modules.extend(a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names)
                self.assertFalse(any(m and m.startswith('debug.froi_acceptance') for m in modules),str(path))

    def test_old_round_missing_checkpoint_not_reconstructed(self):
        core,_=self.material()
        with self.assertRaisesRegex(ValueError,'HISTORICAL_CHECKPOINT_NOT_RECONSTRUCTABLE'):
            export_artifact(Path(self.temp.name)/'0.db',1,test_fixture=True)


if __name__=='__main__': unittest.main()
