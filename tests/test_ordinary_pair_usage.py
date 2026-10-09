"""New semantics only; never reinterpret the frozen original validation."""
from copy import deepcopy
from datetime import datetime, timedelta
from collections import Counter
import json
import hashlib
import pytest
from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from experimental.observation_interface_references.effects.channel import EffectConfig
from experimental.observation_interface_references.reference.references import KEY
from experimental.observation_interface_references.effects.engine import KEY as FX
from experimental.observation_interface_references.real.channel import RealEffectCore,BOOTSTRAP
from experimental.operative_content.engine import identity,ContentCapacityError
from experimental.ordinary_pair_usage.channel import UsageRealCore
from experimental.ordinary_pair_usage.engine import MODE,VERSION
from experimental.ordinary_pair_usage.validation import compare_saved

class Carrier(FakeBridge):
    def __init__(self): self.calls=[]; self.core=None
    def call(self,method,args=None):
        assert method=='perform'
        self.calls.append(deepcopy(args))
        start=self.core.state.observation_frame['timestamp']
        return {'code':args['code'],'parameters':deepcopy(args['parameters']),
            'started_at':start,'finished_at':(datetime.fromisoformat(start)+timedelta(milliseconds=10)).isoformat(),
            'before':{},'after':{},'result':{'input_sent':1,'effect_acknowledged':0},
            'effect_attribution':'temporal_observation_only'}

def create(path,**kw):
    b=Carrier(); c=UsageRealCore(path,b,config=EffectConfig(str(path),**kw),initialize_lifetime='origin_state' in kw)
    b.core=c; return c

def prepared(path):
    c=create(path,origin_state=initial()[0]); c.accept_observation(sample(1,0)); c.bootstrap_once()
    c.accept_observation(sample(2,1)); c.accept_observation(sample(3,0)); return c

def memory_advance(c,current):
    frame=c._encoder.encode(sample(4,0),4,c._body_epoch)
    return c._engine.advance(current,frame,c.state.state_version+1,[])[0]

def test_saved_actual_e5_fits_without_history_erasure():
    r=compare_saved()
    assert r['old_error']['type']=='ContentCapacityError'
    assert (r['units'],r['content_nodes'],r['capacity_total'])==(7,47,54)
    assert r['content_types']['Pair']==25 and not r['reused_content']
    assert r['receipt_reentered'] and r['exact_numeric_input_retained']

def test_real_effect_path_and_renewed_receipt(tmp_path):
    c=prepared(tmp_path/'effect.db')
    try:
        c.accept_observation(sample(4,1)); action=c.state.latest_action['action_id']
        assert c._bridge.calls==[BOOTSTRAP,{'code':16,'parameters':{'slot':1}}]
        prior=c.state.internal_state['l0_state'][KEY]['nodes']
        c.accept_observation(sample(5,1))
        assert all(c.state.internal_state['l0_state'][KEY]['nodes'][k]==v for k,v in prior.items())
        row=c._store.connection.execute("SELECT payload FROM events WHERE event_type='EXPERIENCE_FORMED' ORDER BY event_sequence DESC LIMIT 1").fetchone()
        assert action in json.loads(row[0])['action_ids']
        assert not c.state.internal_state['l0_state']['body_reference_execution']['reused_content']
    finally: c.shutdown()

def test_all_explicit_content_operands_not_first_or_top_k(tmp_path):
    c=prepared(tmp_path/'explicit.db')
    try:
        current=deepcopy(c.state.internal_state); l=current['l0_state']; pool=l[KEY]
        pairs=[k for k,n in pool['nodes'].items() if n['type']=='Pair'][:2]
        root=l['feedback']['next_relation_ref']
        for ref in pairs: current['relations'][root]['outcomes'][ref]={'unit_id':ref,'content_ref':ref}
        used=memory_advance(c,current)
        assert used.l0_state['body_reference_execution']['reused_content']==sorted(pairs)
        for ref in pairs:
            right=identity({'type':'UnitRef','unit':used.l0_state['current_pattern']})
            new=identity({'type':'Pair','left':ref,'right':right})
            assert new in used.l0_state[KEY]['nodes']
        ablated=deepcopy(current)
        for ref in pairs: del ablated['relations'][root]['outcomes'][ref]
        without=memory_advance(c,ablated)
        assert not without.l0_state['body_reference_execution']['reused_content']
        assert len(without.l0_state[KEY]['nodes'])<len(used.l0_state[KEY]['nodes'])
    finally: c.shutdown()

@pytest.mark.parametrize('bad',['missing','mismatch','leaf'])
def test_invalid_explicit_content_rejects_without_fallback(tmp_path,bad):
    c=prepared(tmp_path/(bad+'.db'))
    try:
        state=deepcopy(c.state.internal_state); l=state['l0_state']; pool=l[KEY]
        ref=next(k for k,n in pool['nodes'].items() if n['type']==('Pair' if bad!='leaf' else 'BodyRef'))
        key=ref if bad!='missing' else 'T-missing'
        state['relations'][l['feedback']['next_relation_ref']]['outcomes'][key]={'unit_id':key,'content_ref':ref if bad!='mismatch' else 'T-missing'}
        original=deepcopy(state)
        with pytest.raises(ValueError): memory_advance(c,state)
        assert state==original and c._bridge.calls==[BOOTSTRAP]
    finally: c.shutdown()

def test_unrelated_nested_pair_and_provenance_do_not_activate_wrapping(tmp_path):
    c=prepared(tmp_path/'unrelated.db')
    try:
        state=deepcopy(c.state.internal_state); pool=state['l0_state'][KEY]
        ref=next(k for k,n in pool['nodes'].items() if n['type']=='Pair')
        right=next(k for k,n in pool['nodes'].items() if n['type']=='BodyRef')
        node={'type':'Pair','left':ref,'right':right}; key=identity(node)
        pool['nodes'][key]=node; pool['node_evidence'][key]={'source':'creator_control'}
        output=memory_advance(c,state)
        assert output.l0_state[KEY]['nodes'][key]==node
        assert not output.l0_state['body_reference_execution']['reused_content']
        for evidence in pool['node_evidence'].values(): evidence['source']='changed_audit_label'
        second=memory_advance(c,state)
        assert output.l0_state[KEY]['nodes']==second.l0_state[KEY]['nodes']
    finally: c.shutdown()

def test_saved_pair_reenters_actual_expected_operands(tmp_path):
    c=prepared(tmp_path/'reenter.db')
    try:
        old=c.state.internal_state['l0_state'][KEY]['nodes']
        ids={k for k,n in old.items() if n['type']=='Pair'}
        c.accept_observation(sample(4,1))
        row=c._store.connection.execute("SELECT payload FROM events WHERE event_type='RECURSIVE_PARTIAL_OUTPUT' ORDER BY event_sequence DESC LIMIT 1").fetchone()
        assert ids.intersection(json.loads(row[0])['processing']['expected_outcomes'])
    finally: c.shutdown()

def test_new_version_resume_and_old_database_rejection(tmp_path):
    p=tmp_path/'resume.db'; c=prepared(p); iid=c.state.individual_id; nodes=deepcopy(c.state.internal_state['l0_state'][KEY]['nodes']); c.shutdown()
    d=create(p)
    try:
        assert d.state.individual_id==iid and d.state.internal_state['l0_state'][KEY]['nodes']==nodes
        d.accept_observation(sample(4,1)); assert d._store.latest_state().to_dict()==d.state.to_dict()
    finally:d.shutdown()
    p=tmp_path/'old.db'; b=Carrier(); old=RealEffectCore(p,b,initialize_lifetime=True,config=EffectConfig(str(p),origin_state=initial()[0])); old.shutdown()
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='migration'):create(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==before

def test_true_capacity_failure_is_atomic(tmp_path):
    c=prepared(tmp_path/'capacity.db')
    try:
        state=deepcopy(c.state.internal_state); pool=state['l0_state'][KEY]
        right=next(k for k,n in pool['nodes'].items() if n['type']=='BodyRef'); left=right
        while len(state['units'])+len(pool['nodes'])<64:
            node={'type':'Pair','left':left,'right':right}; left=identity(node)
            pool['nodes'][left]=node;pool['node_evidence'][left]={'source':'capacity_control'}
        c._transition('TEST_ONLY_CAPACITY_CONTROL',{},internal_state=state)
        before=c.state.to_dict(); count=c._store.connection.execute('SELECT count(*) FROM events').fetchone()[0]
        with pytest.raises(ContentCapacityError):c.accept_observation(sample(4,1))
        assert c.state.to_dict()==before and c._store.latest_state().to_dict()==before
        assert count==c._store.connection.execute('SELECT count(*) FROM events').fetchone()[0]
        assert c._bridge.calls==[BOOTSTRAP]
    finally:c.shutdown()


def test_effect_ablation_restore_remains_causal(tmp_path):
    c=prepared(tmp_path/'ablation.db')
    try:
        state=deepcopy(c.state.internal_state); frame=c._encoder.encode(sample(4,1),4,c._body_epoch)
        a=c._engine.advance(state,deepcopy(frame),c.state.state_version+1,[])[0]
        without=deepcopy(state); without['l0_state'][FX]['routes']={}; without['l0_state'][FX]['supports']={}
        b=c._engine.advance(without,deepcopy(frame),c.state.state_version+1,[])[0]
        restored=c._engine.advance(state,deepcopy(frame),c.state.state_version+1,[])[0]
        assert a.l0_state[FX]['current']['operations'] and not b.l0_state[FX]['current']['operations']
        assert a.l0_state[FX]['current']['operations']==restored.l0_state[FX]['current']['operations']
    finally:c.shutdown()


def test_actual_subprocess_restore(tmp_path):
    import subprocess,sys
    path=tmp_path/'process.db'; results=[]
    for phase in ('create','resume'):
        p=subprocess.run([sys.executable,'-X','utf8','-m','experimental.ordinary_pair_usage.worker',phase,str(path)],capture_output=True,encoding='utf-8')
        assert p.returncode==0,p.stderr
        results.append(json.loads(p.stdout))
    a,b=results
    assert a['pid']!=b['pid'] and a['individual_id']==b['individual_id']
    assert a['nodes']==b['restored'] and b['state_version']>a['state_version']
    assert a['authoritative'] and b['authoritative']
