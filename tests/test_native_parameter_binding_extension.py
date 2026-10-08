from copy import deepcopy
import json
import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from individual.core import ACore
from individual.formal_l0 import digest
from experimental.formall0_continuous.runner import FakeBridge
from experimental.operative_content.runner import capture
from experimental.operative_content.engine import KEY as CONTENT
from experimental.typed_operative_connection.engine import KEY as GRAPH, connection, value_ref
from experimental.typed_operative_connection.channel import ConnectionCore, ConnectionConfig
from experimental.native_parameter_binding_extension.channel import BindingCore, BindingConfig
from experimental.native_parameter_binding_extension.runner import create, reopen, sample, receipt, slot_ref, setup


def products(row):
    l = row['after']['l0_state']
    return {r: l[CONTENT]['nodes'][r] for r in l['content_execution']['constructed']}


def new_binding(core, value):
    return digest(connection(slot_ref(sample(2, value)), value_ref(value)))


def test_same_material_history_controls_concrete_new_binding_and_operands(tmp_path):
    a, b = create(tmp_path/'a.db'), create(tmp_path/'b.db')
    try:
        ha, hb = setup(a, 1), setup(b, 2)
        sa, sb = a.state.internal_state, b.state.internal_state
        material = lambda s: {r:u['pattern'] for r,u in s['units'].items() if u.get('operand_kind')=='NATIVE_SENSOR'}
        assert material(sa)==material(sb)
        ra, rb = new_binding(a,1), new_binding(b,2)
        assert sa['l0_state'][GRAPH]['evidence'][ra]['supports']['kind']=='EXACT_ENDPOINT_COMPOSITION'
        assert sb['l0_state'][GRAPH]['evidence'][rb]['supports']['kind']=='EXACT_ENDPOINT_COMPOSITION'
        assert ra not in ha[-1]['after']['internal_state']['l0_state']['typed_connection_execution']['connections']
        normal = capture(a,sample(3,1))
        def replace(s):
            g=s['l0_state'][GRAPH]; other=sb['l0_state'][GRAPH]
            del g['edges'][ra]; g['edges'][rb]=deepcopy(other['edges'][rb]); g['evidence'][rb]=deepcopy(other['evidence'][rb])
            return s
        alternate=capture(a,sample(3,1),replace)
        expected=replace(deepcopy(normal['before']))
        assert alternate['before']==expected
        assert products(normal)!=products(alternate)
        assert normal['partial']['processing']['expected_outcomes']!=alternate['partial']['processing']['expected_outcomes']
        # New slot->1/2 assignment was never in either input receipt (slot->0 only).
        for rows in (ha,hb):
            assert rows[1]['input']['typedExecutionReceipts'][0]['assignments'][0]['operand_ref']==value_ref(0)
    finally: a.shutdown(); b.shutdown()


def test_edge_only_ablation_restore_actual_binding_product(tmp_path):
    c=create(tmp_path/'a.db')
    try:
        setup(c); state=c.state.to_dict(); ref=new_binding(c,1)
        normal=capture(c,sample(3,1))
        def screen(s): del s['l0_state'][GRAPH]['edges'][ref]; return s
        ablated=capture(c,sample(3,1),screen); restored=capture(c,sample(3,1))
        missing=set(products(normal))-set(products(ablated)); assert len(missing)==1
        product=next(iter(missing))
        assert product in normal['partial']['processing']['expected_outcomes']
        assert product not in ablated['partial']['processing']['expected_outcomes']
        assert normal['after']['l0_state'][CONTENT]['evidence'][product]['direct_supports']['connection_refs']==[ref]
        assert products(normal)==products(restored)
        assert c.state.to_dict()==state
    finally: c.shutdown()


@pytest.mark.parametrize('edit',['provenance','order','distractor'])
def test_no_audit_or_order_policy(tmp_path,edit):
    c=create(tmp_path/'a.db')
    try:
        setup(c); baseline=capture(c,sample(3,1))
        def modify(s):
            g=s['l0_state'][GRAPH]
            if edit=='provenance': g['evidence']={}
            elif edit=='order': g['edges']=dict(reversed(list(g['edges'].items())))
            else:
                for name in ('disconnected-a','disconnected-b'): s['units'][name]={'unit_id':name,'pattern':[]}
                edge=connection('disconnected-a','disconnected-b'); g['edges'][digest(edge)]=edge
            return s
        assert products(capture(c,sample(3,1),modify))==products(baseline)
    finally: c.shutdown()


@pytest.mark.parametrize('history',[True,False])
def test_cross_actual_process_current_state_reuse(tmp_path,history):
    rows=[]; db=tmp_path/'a.db'
    for phase in ('create','resume'):
        cmd=[sys.executable,'-m','experimental.native_parameter_binding_extension.runner',phase,str(db)]
        if not history: cmd.append('--history-off')
        r=subprocess.run(cmd,capture_output=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},timeout=40)
        assert r.returncode==0,r.stderr
        rows.append(json.loads(r.stdout))
    a,b=rows
    assert a['pid']!=b['pid'] and a['lease_released'] and b['lease_released']
    assert a['shutdown']['individual_id']==b['start']['individual_id']
    assert b['start']['state_version']==a['shutdown']['state_version']+1
    for key in (GRAPH,CONTENT): assert a['shutdown']['internal_state']['l0_state'][key]==b['start']['internal_state']['l0_state'][key]
    final=b['records'][-1]['after']['internal_state']['l0_state']
    assert final[GRAPH]==a['shutdown']['internal_state']['l0_state'][GRAPH]
    assert not final['content_execution']['new_nodes']
    saved=a['records'][-1]['after']['internal_state']['l0_state']['content_execution']['constructed']
    assert set(saved)<=set(final['content_execution']['reused_content'])


@pytest.mark.parametrize('bad',['missing','port','failed','duplicate','value'])
def test_invalid_receipt_rejects_before_commit(tmp_path,bad):
    c=create(tmp_path/'a.db')
    try:
        c.accept_observation(sample(1,0)); before=c.state.to_dict()
        raw=sample(2,1); r=receipt(raw)
        if bad=='missing': r['assignments'][0]['operand_ref']='missing'
        elif bad=='port': r['code']=0
        elif bad=='failed': r['status']='failed'
        elif bad=='duplicate': r['assignments']*=2
        else: r['assignments'][0]['operand_ref']=value_ref(64)
        raw['typedExecutionReceipts']=[r]
        with pytest.raises(ValueError): c.accept_observation(raw)
        assert c.state.to_dict()==before
    finally: c.shutdown()


def test_absent_receipt_and_multi_slot_facts_no_choice(tmp_path):
    c=create(tmp_path/'a.db')
    try:
        c.accept_observation(sample(1,0)); raw=sample(2,1)
        c.accept_observation(raw)
        assert new_binding(c,1) not in c.state.internal_state['l0_state'][GRAPH]['edges']
    finally: c.shutdown()
    c=create(tmp_path/'b.db')
    try:
        c.accept_observation(sample(1,0)); raw=sample(2,1); r=receipt(raw)
        r['assignments']+=receipt(raw,name='pitch_delta')['assignments']; raw['typedExecutionReceipts']=[r]
        c.accept_observation(raw)
        for name in ('yaw_delta','pitch_delta'):
            ref=digest(connection(slot_ref(raw,name),value_ref(1)))
            assert ref in c.state.internal_state['l0_state'][GRAPH]['edges']
    finally: c.shutdown()


def test_mode_refusal_and_tripwires(tmp_path):
    db=tmp_path/'a.db'; c=create(db)
    try:
        with patch('individual.core.select_uniform_action',side_effect=AssertionError('sampler')),patch('individual.core.bind_parameters',side_effect=AssertionError('binder')):
            setup(c); c.accept_observation(sample(3,1))
        with pytest.raises(RuntimeError): c.execute_discrete_action()
    finally: c.shutdown()
    data=db.read_bytes()
    for call in (lambda: ACore(db,FakeBridge()),lambda: ConnectionCore(db,FakeBridge(),config=ConnectionConfig(str(db))),lambda: BindingCore(db,FakeBridge(),config=BindingConfig(str(db),version='wrong'))):
        with pytest.raises(ValueError): call()
    assert db.read_bytes()==data


@pytest.mark.parametrize('capacity',['units','relations'])
def test_original_capacity_rejects_whole_batch(tmp_path,capacity):
    c=create(tmp_path/'a.db')
    try:
        setup(c); before=c.state.to_dict()
        def fill(s):
            if capacity=='units':
                while len(s['units'])+len(s['l0_state'][CONTENT]['nodes'])<c._engine.caps.units:
                    key='unrelated:'+str(len(s['units'])); s['units'][key]={'unit_id':key,'pattern':[]}
            else:
                while len(s['relations'])+len(s['l0_state']['operative_test_only']['edges'])+len(s['l0_state'][GRAPH]['edges'])<c._engine.caps.relations:
                    key='unrelated:'+str(len(s['relations'])); s['relations'][key]={'relation_id':key,'outcomes':{}}
            return s
        with pytest.raises(ValueError): capture(c,sample(3,2),fill)
        assert c.state.to_dict()==before
    finally: c.shutdown()


def test_renamed_initial_operands_and_receipt_identity(tmp_path):
    from experimental.formall0_operative.validation import initial
    names=('arbitrary-left','arbitrary-right')
    origin=initial()[0]
    mapping=dict(zip(('U-origin-0','U-origin-1'),names))
    origin['units']={mapping[k]:{**u,'unit_id':mapping[k]} for k,u in origin['units'].items()}
    for row in origin['relations'].values():
        row['antecedent']=mapping[row['antecedent']]
        row['outcomes']={mapping[k]:{**u,'unit_id':mapping[k]} for k,u in row['outcomes'].items()}
    c=create(tmp_path/'a.db',origin=origin,origin_edges=(connection(*names),))
    try:
        c.accept_observation(sample(1,0)); raw=sample(2,1)
        raw['typedExecutionReceipts']=[receipt(raw,execution_id='arbitrary-receipt-identity')]
        c.accept_observation(raw)
        assert new_binding(c,1) in c.state.internal_state['l0_state'][GRAPH]['edges']
        row=capture(c,sample(3,1)); assert new_binding(c,1) in row['after']['l0_state']['typed_connection_execution']['connections']
    finally: c.shutdown()


def test_multiple_successor_candidates_are_all_retained(tmp_path):
    c=create(tmp_path/'a.db')
    try:
        setup(c,1); c.accept_observation(sample(3,0)); c.accept_observation(sample(4,2))
        edges=c.state.internal_state['l0_state'][GRAPH]['edges']
        assert {new_binding(c,1),new_binding(c,2)}<=set(edges)
        row=capture(c,sample(5,2))
        assert {new_binding(c,1),new_binding(c,2)}<=set(row['after']['l0_state']['typed_connection_execution']['connections'])
    finally: c.shutdown()


@pytest.mark.parametrize('stale',[False,True])
def test_observed_reference_premise_not_new_reference_propagation(tmp_path,stale):
    from experimental.native_body_operands.runner import observation
    c=create(tmp_path/'a.db')
    try:
        raw=observation(1,0,codes=(13,)); c.accept_observation(raw)
        units=c.state.internal_state['units']
        slot=next(r for r,u in units.items() if isinstance(u['pattern'],dict) and u['pattern']['type']=='ParameterSlot')
        value=next(r for r,u in units.items() if isinstance(u['pattern'],dict) and u['pattern']['type']=='ObservedReference')
        second=observation(2,1,codes=(13,))
        second['typedExecutionReceipts']=[{'execution_id':'reference-premise','catalog_version':2,'code':13,'status':'executed',
            'source':'EXTERNAL_SYNTHETIC_TYPED_RECEIPT','assignments':[{'slot_ref':slot,'operand_ref':value}]}]
        if stale: second['nearbyEntities']=[]
        before=c.state.to_dict()
        if stale:
            with pytest.raises(ValueError,match='stale'): c.accept_observation(second)
            assert c.state.to_dict()==before
        else:
            c.accept_observation(second); ref=digest(connection(slot,value))
            assert c.state.internal_state['l0_state'][GRAPH]['evidence'][ref]['supports']['kind']=='RECORDED_EXTERNAL_INCIDENCE'
            third=observation(3,1,codes=(13,)); row=capture(c,third)
            assert ref in row['after']['l0_state']['typed_connection_execution']['connections']
    finally: c.shutdown()


def test_multiple_native_ports_no_code_specific_formation(tmp_path):
    from experimental.native_body_operands.runner import observation
    c=create(tmp_path/'a.db')
    try:
        def raw(seq,value):
            r=observation(seq,value,codes=(8,16)); r.update(health=1,hunger=2); return r
        first=raw(1,0); c.accept_observation(first)
        second=raw(2,1)
        a=receipt(second)
        other=deepcopy(second); other['actionSpace']=other['actionSpace'][1:]
        b=receipt(other,name='slot',execution_id='other-native-port')
        second['typedExecutionReceipts']=[a,b]
        c.accept_observation(second)
        expected={digest(connection(x['assignments'][0]['slot_ref'],value_ref(1))) for x in (a,b)}
        assert expected<=set(c.state.internal_state['l0_state'][GRAPH]['edges'])
        row=capture(c,raw(3,1))
        assert expected<=set(row['after']['l0_state']['typed_connection_execution']['connections'])
    finally: c.shutdown()
