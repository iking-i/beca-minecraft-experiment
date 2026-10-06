"""TEST_ONLY v1/v2 equivalence and negative controls. Never live acceptance."""
from copy import deepcopy
import ast
import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.test_froi_acceptance import AcceptanceFacilityTests
from debug import froi_acceptance_checks as v1
from debug import froi_acceptance_material as old
from tools.froi_acceptance_v2 import checks as v2, material as new


class V2FacilityTests(unittest.TestCase):
    setUp = AcceptanceFacilityTests.setUp
    close = AcceptanceFacilityTests.close
    core = AcceptanceFacilityTests.core
    material = AcceptanceFacilityTests.material

    def converted(self, a):
        f, ev = new.freeze(a.payload['database'])
        text = new.export_manifest(a.payload['database'], a.checkpoint.payload['state_version'], f, ev, test_fixture=True)
        return new.load_manifest(text, f, ev), f

    def test_v1_v2_logical_digest_exact_and_whole_freeze(self):
        _,a = self.material(); b,f = self.converted(a)
        self.assertEqual(old.freeze(a.payload['database']), f)
        self.assertEqual(a.checkpoint, b.checkpoint)
        self.assertEqual(a.handle, b.handle)
        self.assertEqual(a.history, b.history)
        self.assertEqual(a.payload['formal_snapshot'], b.payload['formal_snapshot'])

    def test_v1_v2_T1_full_evidence_equal(self):
        _,a = self.material(); b,_ = self.converted(a)
        self.assertEqual(v1.verify_t1(a,fixture_control=True),v2.verify_t1(b,fixture_control=True))

    def test_v1_v2_T2_full_input_output_equal(self):
        _,a = self.material(); b,_ = self.converted(a)
        hs=[a.history,old.read_history(a.payload['database'],1)]
        # Fix ONLY fixture-test entropy to compare identical counterfactual outputs.
        from uuid import UUID
        for fn, artifact in ((v1.run_t2,a),(v2.run_t2,b)):
            with patch('individual.formal_froi.uuid4',side_effect=[UUID(int=i+1) for i in range(40)]):
                result=fn(artifact,hs,fixture_control=True)
            if fn is v1.run_t2: expected=result
            else: self.assertEqual(expected,result)

    def test_v1_v2_T3_full_replay_and_ablation_equal(self):
        _,a = self.material(); b,_ = self.converted(a)
        from uuid import UUID
        with patch('individual.formal_froi.uuid4',side_effect=[UUID(int=i+1) for i in range(40)]):
            expected=v1.run_t3(a,fixture_control=True)
        with patch('individual.formal_froi.uuid4',side_effect=[UUID(int=i+1) for i in range(40)]):
            actual=v2.run_t3(b,fixture_control=True)
        self.assertEqual(expected,actual)
        self.assertEqual(actual['status'],'PASS',actual)

    def test_v1_v2_T4_exact_trace_equal(self):
        _,db,v = self.material(failure=True)
        with new.readonly(db) as c:
            limits=[r['payload'] for r in new.events(c,version=v,types=('CURRENT_LIMIT_ENCOUNTER',))]
        limit=next(p['limit_id'] for p in limits if p['auditor_metadata']['semantic_code']=='FROI_RESOURCE_LIMIT')
        self.assertEqual(v1.trace_t4(db,limit),v2.trace_t4(db,limit))

    def test_v1_v2_T5_exact_status_and_freeze_equal(self):
        _,a = self.material(); b,f = self.converted(a)
        # The already pinned contract is checked separately; this fixes no experimental data.
        for evidence in ({}, {'T4':{'organization_statuses':['RESOURCE_LIMIT']}}):
            self.assertEqual(v1.verify_t5(a,f,f,evidence),v2.verify_t5(b,f,f,evidence))

    def test_v1_v2_detached_continuation_equal(self):
        _,a = self.material(); b,_ = self.converted(a)
        from integration.froi import resume_detached
        from uuid import UUID
        for checks,artifact in ((v1,a),(v2,b)):
            with patch('individual.formal_froi.uuid4',side_effect=[UUID(int=i+1) for i in range(40)]):
                output=resume_detached(checks.engine_for(artifact.checkpoint),artifact.checkpoint,artifact.handle,screen_effect=True)
                result=checks.detached_continue(artifact,output)
            if checks is v1: expected=result
            else: self.assertEqual(expected,result)

    def test_missing_locator_corrupt_binding_and_changed_full_source_rejected(self):
        _,a = self.material(); b,f = self.converted(a); m=json.loads(b.manifest_text)
        original=deepcopy(m);m['locators'].pop()
        with self.assertRaises(ValueError): new.load_manifest(new.canonical(m),f,b.verified_source_events_digest)
        m=deepcopy(original);m['locators'][0]['content_digest']='corrupt'
        with self.assertRaises(ValueError): new.load_manifest(new.canonical(m),f,b.verified_source_events_digest)
        with self.assertRaises(ValueError): new.load_manifest(b.manifest_text,f,'corrupt')

    def test_no_full_materializer_used_and_fixture_gate_retained(self):
        _,a = self.material()
        with patch.object(old,'event_rows',side_effect=AssertionError('full events')):
            b,_=self.converted(a)
            self.assertEqual(v2.verify_t1(b)['status'],'NOT_TESTABLE')
            self.assertEqual(v2.run_t3(b,fixture_control=True)['status'],'PASS')

    def test_predicates_and_replay_helpers_are_identical_to_v1(self):
        for name in ('run_t2','run_t3','verify_t5','processing_effect','entropy_for_replay',
                     'unscreened_replay','apply_recorded_commit_boundary','frozen_contract'):
            self.assertEqual(ast.dump(ast.parse(inspect.getsource(getattr(v1,name)))),
                             ast.dump(ast.parse(inspect.getsource(getattr(v2,name)))))

    def test_keyset_pages_complete_and_ordered(self):
        _,a = self.material()
        with old.readonly(a.payload['database']) as db: expected=old.event_rows(db)
        with new.readonly(a.payload['database']) as db: actual=list(new.events(db))
        self.assertEqual(expected,actual)

    def test_final_acceptance_statuses_equivalent(self):
        from contextlib import redirect_stderr
        from io import StringIO
        from debug.froi_acceptance import validate
        from tools.froi_acceptance_v2 import __main__ as entry
        _,a=self.material();b,f=self.converted(a)
        self.assertEqual(old.freeze(a.payload['database']),f)
        contract=v1.frozen_contract()
        outer=entry.tooling_contract()
        self.assertEqual(contract,outer['v1_contract'])
        expected=validate(a,pair_versions=[a.history.state_version,1])

        # Final orchestration: compare PRE rejection with PRE rejection, not
        # v1's early return with a v2 local item that must never be executed.
        if contract['status']!='PASS':
            self.assertEqual(expected['T5']['reason'],'PRE source/database freeze mismatch')
            self.assertEqual(expected['T5']['contract'],contract)
            self.assertEqual(expected['T5']['status'],'FAIL')
            for item in ('T1','T2','T3','T4'):
                self.assertEqual(expected[item]['status'],'NOT_TESTABLE')
                self.assertEqual(expected[item]['reason'],'PRE freeze gate rejected')
        if outer['status']!='PASS':
            output=Path(self.temp.name)/'outer-rejected'
            argv=['froi-v2','--database',a.payload['database'],
                  '--session',a.checkpoint.payload['session_id'],
                  '--versions',str(a.history.state_version),
                  '--pair-versions',str(a.history.state_version),'1',
                  '--limit-id','TEST_ONLY_MISSING_CONSEQUENCE','--output',str(output)]
            errors=StringIO()
            with patch('sys.argv',argv), redirect_stderr(errors), \
                    patch.object(entry,'validate_local',wraps=entry.validate_local) as local, \
                    patch.object(new,'freeze',wraps=new.freeze) as freeze:
                with self.assertRaises(SystemExit) as rejected:
                    entry.main()
            self.assertEqual(rejected.exception.code,2)
            self.assertIn('Frozen v1/v2 contract rejected',errors.getvalue())
            local.assert_not_called()
            freeze.assert_not_called()
            self.assertFalse(output.exists())
        else:
            # Both outer contracts passed; only now compare final item statuses.
            actual=entry.validate_local(b,pair_versions=[b.history.state_version,1])
            actual['T5']=v2.verify_t5(b,f,new.freeze(b.payload['database'])[0],actual)
            self.assertEqual({k:expected[k]['status'] for k in ('T1','T2','T3','T4','T5')},
                             {k:actual[k]['status'] for k in ('T1','T2','T3','T4','T5')})

        # Local T4 is a different boundary. With the same absent consequence
        # identity, compare actual item validators, without a PRE early return.
        limit='TEST_ONLY_MISSING_CONSEQUENCE'
        local_expected=v1.trace_t4(a.payload['database'],limit)
        local_actual=entry.validate_local(b,limit_id=limit)['T4']
        self.assertEqual(local_expected,local_actual)


if __name__ == '__main__': unittest.main()
