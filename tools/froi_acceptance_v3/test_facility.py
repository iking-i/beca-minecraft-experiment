"""Independent measurement controls. Never create/run A, closure or Minecraft."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from tools.froi_acceptance_v3 import checks
from tools.froi_acceptance_v3.__main__ import V2_DIR, inventory
from tools.froi_acceptance_v2 import material as m


def fixture():
    raw = {'limit_id': 'fixed-failure', 'object_refs': ['fixed-query'], 'operation_performed': False}
    def output(sequence, status):
        frame = {'frame_id': 'f' + str(sequence), 'sequence_id': sequence, 'internal_observations': [deepcopy(raw)]}
        exp = {'limit_consequences': [deepcopy(raw)]}
        processing = {'consumed_limit_ids': [raw['limit_id']]}
        feedback = {'partial_id': 'p' + str(sequence), 'observed_limit_ids': [raw['limit_id']]}
        partial = {'partial_id': feedback['partial_id'], 'experience': exp, 'processing': processing}
        read = {'status': status, 'organization_status': 'COMPLETE', 'closure_complete': True}
        journal = [('FROI_ORGANIZATION_FORMED', {'status': 'COMPLETE','closure_complete': True}),
                   ('FROI_ORGANIZATION_CONSUMED', read), ('RECURSIVE_PARTIAL_OUTPUT', partial),
                   ('RECURSIVE_FEEDBACK_STORED', feedback), ('EXPERIENCE_FORMED', exp), ('OBSERVATION_FRAME', frame)]
        return {'frame': frame, 'experience': exp, 'processing': processing, 'feedback': feedback,
                'read': read, 'pending_consequences': [deepcopy(raw)],
                'internal': {'l0_state': {'feedback': feedback, 'pending_consequences': [deepcopy(raw)]}}, 'journal': journal}
    branch = output(3, 'UNRESOLVED_REFERENCE')
    branch['journal'].append(('CURRENT_LIMIT_ENCOUNTER', {'a_facing_payload': deepcopy(raw),
        'auditor_metadata': {'semantic_code': 'FROI_UNRESOLVED_REFERENCE', 'classification': 'TEST_ONLY_INTERVENTION'}}))
    out = output(4, 'READ_SUCCEEDED')
    out['journal'].append(('LIMIT_FEEDBACK_REENTERED_RECURSION',
        {'frame_id': 'f4', 'limit_ids': ['fixed-failure'], 'partial_id': 'p4'}))
    return branch, {'category': 'TEST_ONLY', 'original_raw_pending': [deepcopy(raw)], 'output': out}


class ChainControls(unittest.TestCase):
    def test_complete_exact_chain(self):
        b,c=fixture(); r=checks.verify_chain(b,c)
        self.assertEqual(r['organization_statuses'], ['COMPLETE','COMPLETE'])
        self.assertFalse(r['formal_live_natural_failure'])

    def test_negative_controls(self):
        changes = {
            'incomplete_failure': lambda b,c: checks.single(b['journal'],'FROI_ORGANIZATION_FORMED').update(status='RESOURCE_LIMIT'),
            'incomplete_next': lambda b,c: checks.single(c['output']['journal'],'FROI_ORGANIZATION_FORMED').update(status='RESOURCE_LIMIT'),
            'successful_read': lambda b,c: b['read'].update(status='READ_SUCCEEDED'),
            'changed_raw': lambda b,c: c['original_raw_pending'][0].update(object_refs=['changed']),
            'pending_removed': lambda b,c: b['internal']['l0_state']['pending_consequences'].clear(),
            'frame_loss': lambda b,c: c['output']['frame']['internal_observations'].clear(),
            'experience_loss': lambda b,c: c['output']['experience']['limit_consequences'].clear(),
            'partial_no_consumption': lambda b,c: c['output']['processing']['consumed_limit_ids'].clear(),
            'feedback_loss': lambda b,c: c['output']['feedback']['observed_limit_ids'].clear(),
            'wrong_partial': lambda b,c: checks.single(c['output']['journal'],'LIMIT_FEEDBACK_REENTERED_RECURSION').update(partial_id='other'),
            'wrong_reentry_limit': lambda b,c: checks.single(c['output']['journal'],'LIMIT_FEEDBACK_REENTERED_RECURSION').update(limit_ids=['other']),
            'wrong_reentry_frame': lambda b,c: checks.single(c['output']['journal'],'LIMIT_FEEDBACK_REENTERED_RECURSION').update(frame_id='other'),
            'sample_gap': lambda b,c: c['output']['frame'].update(sequence_id=5),
            'live_label': lambda b,c: c.update(category='FORMAL_LIVE'),
            'live_failure_label': lambda b,c: checks.single(b['journal'],'CURRENT_LIMIT_ENCOUNTER')['auditor_metadata'].update(classification='READ_OPERATION_UNAVAILABLE'),
            'log_only': lambda b,c: c['output']['journal'].pop(),
        }
        for name, mutate in changes.items():
            with self.subTest(name=name):
                b,c=fixture(); mutate(b,c)
                with self.assertRaises(ValueError): checks.verify_chain(b,c)

    def test_reselected_plan_rejected(self):
        plan={'versions':[16,20,22,25], 'pair_versions':[15,11], 'session':checks.SESSION}
        report={'measurement_commit':checks.BASE,'FROI1_ACCEPTANCE':'PARTIAL','session':{'session_id':checks.SESSION}}
        with self.assertRaises(ValueError): checks.validate_plan(plan,report)

    def test_duplicate_failure_rejected(self):
        b,c=fixture(); b['journal'].append(deepcopy(checks.single(b['journal'],'CURRENT_LIMIT_ENCOUNTER')))
        # Explicit tuple entry to keep the fixture journal schema valid.
        b['journal'][-1]=('CURRENT_LIMIT_ENCOUNTER',b['journal'][-1])
        with self.assertRaises(ValueError):checks.verify_chain(b,c)


@unittest.skipUnless((V2_DIR/'evidence-A16.json').is_file(), 'Local frozen v2 evidence not distributed')
class ExistingEvidenceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes=inventory(V2_DIR)
        cls.evidence=json.loads((V2_DIR/'evidence-A16.json').read_text(encoding='utf8'))
        cls.plan=json.loads((V2_DIR/'measurement-plan.json').read_text(encoding='utf8'))
        cls.report=json.loads((V2_DIR/'report.json').read_text(encoding='utf8'))
        cls.manifest=json.loads((V2_DIR/'artifact-A16.json').read_text(encoding='utf8'))
        cls.artifact=m.load_manifest(m.canonical(cls.manifest),cls.manifest['source_freeze'],cls.manifest['source_events_digest'])

    def verify(self,evidence):
        with (patch('integration.froi.produce',side_effect=AssertionError('No producer')),
              patch('experimental.gsc0.engine.Engine.run',side_effect=AssertionError('No closure')),
              patch('individual.formal_froi.FormalFROIEngine.advance',side_effect=AssertionError('No new round')),
              patch('individual.formal_froi.FormalFROIEngine.resume_from_read_checkpoint',side_effect=AssertionError('No new resume'))):
            return checks.validate_saved(self.artifact,evidence,self.plan,self.report)

    def test_saved_evidence_regression_no_execution(self):
        r=self.verify(self.evidence)
        self.assertTrue(all(r[k]['status']=='PASS' for k in ('T1','T2','T3','T4')))
        self.assertEqual(inventory(V2_DIR),self.hashes)

    def test_saved_negative_controls(self):
        mutations={
            'wrong_checkpoint':lambda e:e['T2'].update(checkpoint_digest='other'),
            'wrong_condition':lambda e:e['T2']['condition']['fields'].update(version='other'),
            'fabricated_next_observation':lambda e:e['T2_continuations'][1]['source_event']['payload']['observation'].update(health=-999),
            'continuation_digest':lambda e:e['T2_continuations'][1].update(isolated_history_digest='other'),
            'wrong_handle_request':lambda e:e['T2']['handles'][1]['fields']['request']['fields'].update(reference='other'),
            'missing_replay':lambda e:e['T3'].update(unscreened_replay='FAIL'),
            'wrong_saved_read':lambda e:e['T2']['reads'][1].update(status='READ_SUCCEEDED'),
            'wrong_consumed_keys':lambda e:e['T2_continuations'][1]['output']['read'].update(consumed_keys=[]),
            'wrong_direct_supports':lambda e:e['T2_continuations'][1]['output']['read'].update(direct_supports=[]),
            'wrong_root_witnesses':lambda e:e['T2_continuations'][1]['output']['read'].update(root_witnesses=[]),
            'T3_log_only':lambda e:e['T3']['screened'].update(processing=deepcopy(e['T3']['normal']['processing'])),
        }
        for name,mutate in mutations.items():
            with self.subTest(name=name):
                e=deepcopy(self.evidence);mutate(e)
                with self.assertRaises(ValueError):self.verify(e)

    def test_t5_complete_gate_not_relaxed(self):
        from tools.froi_acceptance_v2 import checks as old
        f=self.artifact.payload['source_freeze']
        base={**self.evidence,'T4':checks.verify_chain(self.evidence['T2']['outputs'][1],self.evidence['T2_continuations'][1])}
        self.assertTrue(old.verify_t5(self.artifact,f,f,base)['checks']['all_used_organizations_COMPLETE'])
        base['T4']['organization_statuses'][1]='RESOURCE_LIMIT'
        self.assertFalse(old.verify_t5(self.artifact,f,f,base)['checks']['all_used_organizations_COMPLETE'])


if __name__=='__main__':unittest.main()
