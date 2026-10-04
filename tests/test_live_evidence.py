"""Negative evidence gates in isolated data; never claim a simulated live result."""
from copy import deepcopy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from debug.live_evidence import FOUNDATIONS, LIVE, INPUT, CONDITIONAL, freeze_decision, matching_blocks, server_slot, verdict
from debug.world_entry_live import server_positions, retained_history_checks


class LiveEvidenceTests(unittest.TestCase):
    def step(self):
        return {'step_id':'unit-only', 'action_code':37,'input_sent':True,'authorship':'TEST_ONLY',
                'source_frame':{'frame_id':'A:E1'},'renewed_frame':{'frame_id':'A:E2'},
                'source_version':4,'observation_version':7,'out_wire_sequences':[2]}

    def test_sent_packet_and_predicted_change_do_not_prove_server_consequence(self):
        out={'wire_sequence':2,'direction':'OUT','name':'block_dig'}
        self.assertEqual(verdict([self.step()],[out],{'local_predicted_air':True},'unit')['status'],INPUT)
        self.assertEqual(freeze_decision({'completed_dig':{'status':INPUT}})['WORLD_ENTRY_FREEZE'],'blocked')

    def test_server_input_requires_real_renewed_frame_and_test_authorship(self):
        packet={'wire_sequence':3,'direction':'IN','name':'block_change'}
        self.assertEqual(verdict([self.step()],[packet],{'verified_difference':1},'unit')['status'],LIVE)
        for field,value in [('renewed_frame',None),('observation_version',4),('authorship','EXTERNAL_FIXED_POLICY'),('out_wire_sequences',[])]:
            step=self.step();step[field]=value
            self.assertNotEqual(verdict([step],[packet],{'verified_difference':1},'unit')['status'],LIVE)
        failed=self.step();failed['input_sent']=False
        self.assertEqual(verdict([failed],[packet],{'verified_difference':1},'unit')['status'],CONDITIONAL)

    def test_matching_block_must_be_inbound_exact_position_and_expected_type(self):
        p={'x':1,'y':2,'z':3}
        received={'wire_sequence':3,'direction':'IN','normalized':{'blocks':[{'position':p,'block_type_id':0}]}}
        outgoing={**received,'direction':'OUT'}
        elsewhere=deepcopy(received);elsewhere['normalized']['blocks'][0]['position']['x']=2
        self.assertEqual(matching_blocks([outgoing,elsewhere,received],p,0),[received])
        self.assertEqual(matching_blocks([received],p,1),[])

    def test_slot_prediction_or_wrong_server_window_cannot_count_as_confirmation(self):
        received={'wire_sequence':8,'direction':'IN','normalized':{'window_id':2,'slots':[{'slot':0,'item_type_id':None,'count':0}]}}
        outgoing={**received,'direction':'OUT'}
        self.assertEqual(server_slot([outgoing,received],0,None,0,2),[received])
        self.assertEqual(server_slot([received],0,None,0,1),[])
        self.assertEqual(server_slot([received],0,None,1,2),[])

    def test_freeze_requires_all_six_live_chains(self):
        chains={key:{'status':LIVE} for key in FOUNDATIONS}
        self.assertEqual(freeze_decision(chains),{'WORLD_ENTRY_FREEZE':'passed','blockers':[]})
        for key in FOUNDATIONS:
            changed=deepcopy(chains);changed[key]['status']=INPUT
            self.assertEqual(freeze_decision(changed)['blockers'],[key])

    def test_authoritative_pos_query_parses_nbt_text_but_ignores_outgoing_text(self):
        incoming={'wire_sequence':3,'direction':'IN','name':'system_chat','data':{'content':{
            'translate':'commands.data.entity.query','with':[{'text':'BECA_Validate'},{'text':'[1.25d, 76.0d, -4.5d]'}]}}}
        outgoing={**incoming,'direction':'OUT'}
        self.assertEqual(server_positions([incoming,outgoing]),[(incoming,{'x':1.25,'y':76.0,'z':-4.5})])
        unrelated=deepcopy(incoming);unrelated['data']['content']['translate']='unrelated.message'
        self.assertEqual(server_positions([unrelated]),[])

    def test_actual_26_1_colored_nbt_component_is_decoded_without_usage_knowledge(self):
        def string(v): return {'type':'string','value':v}
        def compound(v): return {'type':'compound','value':v}
        fragments=[compound({'':string('[')}),compound({'text':string('-1240.5'),'color':string('gold')}),
                   compound({'text':string('d')}),compound({'':string(', ')}),compound({'text':string('80.0d')}),
                   compound({'':string(', ')}),compound({'text':string('342.7d')}),compound({'':string(']')})]
        component=compound({'translate':string('commands.data.entity.query'),
            'with':{'type':'list','value':{'type':'compound','value':[compound({'text':string('BECA_Validate')}),
                compound({'text':string(''),'extra':{'type':'list','value':{'type':'compound','value':fragments}}})]}}})
        incoming={'wire_sequence':7154,'direction':'IN','name':'system_chat','data':{'content':component}}
        self.assertEqual(server_positions([incoming]),[(incoming,{'x':-1240.5,'y':80.,'z':342.7})])

    def history_fixture(self):
        root=Path(__file__).resolve().parents[1]/'.test-tmp'
        root.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=root)
        assert Path(temp.name).resolve().is_relative_to(root.resolve())
        self.addCleanup(temp.cleanup)
        database=Path(temp.name)/'unit-only.db'
        step=self.step();step.update(action_id='test-action',parameters={'block_ref':'opaque'})
        requested={'action_id':'test-action','method':'perform','args':{'code':37,'parameters':step['parameters']},
                   'provenance':{'source_state_version':4,'decision_authorship':{'aggregate_source':'TEST_ONLY'}}}
        with closing(sqlite3.connect(database)) as db:
            db.execute('CREATE TABLE events(event_type TEXT,payload TEXT)')
            db.execute('CREATE TABLE states(state_version INTEGER,individual_id TEXT,snapshot TEXT)')
            db.executemany('INSERT INTO events VALUES (?,?)',[
                ('ACTION_REQUESTED',json.dumps(requested)),('ACTION_EXECUTED',json.dumps({'action_id':'test-action','status':'executed'}))])
            db.executemany('INSERT INTO states VALUES (?,?,?)',[(4,'A-unit-only',json.dumps({'observation_frame':step['source_frame']})),
                (7,'A-unit-only',json.dumps({'observation_frame':step['renewed_frame']}))])
            db.commit()
        return {'database':str(database),'individual_id':'A-unit-only','steps':[step]}

    def test_retained_history_rejects_forged_frame_even_when_report_claims_success(self):
        report=self.history_fixture()
        self.assertTrue(all(retained_history_checks(report).values()))
        report['steps'][0]['renewed_frame']['frame_id']='forged'
        self.assertFalse(retained_history_checks(report)['frames_match_states'])

    def test_retained_history_rejects_changed_parameters_and_source_version(self):
        report=self.history_fixture()
        report['steps'][0]['parameters']={'block_ref':'different'}
        report['steps'][0]['source_version']=9
        checks=retained_history_checks(report)
        self.assertFalse(checks['numeric_formal_path'])
        self.assertFalse(checks['requested_events_match'])

    def test_frozen_boundary_matches_exact_sources_and_keeps_debug_macros_separate(self):
        root=Path(__file__).resolve().parents[1]
        frozen=json.loads((root/'WORLD_ENTRY_FREEZE.json').read_text(encoding='utf-8'))
        for path,expected in frozen['component_hashes'].items():
            with self.subTest(path=path):
                actual=hashlib.sha256((root/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                self.assertEqual(actual,expected)
        catalog=json.loads((root/'minecraft/action-space.json').read_text(encoding='utf-8'))
        formal=[a['code'] for a in catalog['actions'] if a.get('formal_enabled') is not False]
        debug=[a['code'] for a in catalog['actions'] if a.get('formal_enabled') is False]
        self.assertEqual(formal,frozen['action_space']['formal_codes'])
        self.assertEqual(debug,frozen['action_space']['debug_only_codes'])
        self.assertTrue(set(formal).isdisjoint(debug))
