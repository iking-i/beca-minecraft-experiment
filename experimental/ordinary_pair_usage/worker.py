"""Offline independent-process persistence check; not real Minecraft evidence."""
from copy import deepcopy
from datetime import datetime,timedelta
import json,os,sys
from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from experimental.observation_interface_references.effects.channel import EffectConfig
from experimental.observation_interface_references.reference.references import KEY
from .channel import UsageRealCore
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

if __name__=='__main__':
    phase,path=sys.argv[1:]
    b=Carrier()
    c=UsageRealCore(path,b,config=EffectConfig(path,origin_state=initial()[0] if phase=='create' else None),initialize_lifetime=phase=='create')
    b.core=c
    restored=deepcopy(c.state.internal_state['l0_state'][KEY]['nodes'])
    if phase=='create':
        c.accept_observation(sample(1,0));c.bootstrap_once()
        for sequence,value in ((2,1),(3,0),(4,1),(5,1)):c.accept_observation(sample(sequence,value))
    else:c.accept_observation(sample(6,1))
    result={'pid':os.getpid(),'individual_id':c.state.individual_id,'state_version':c.state.state_version,
        'nodes':c.state.internal_state['l0_state'][KEY]['nodes'],'restored':restored,
        'authoritative':c._store.latest_state().to_dict()==c.state.to_dict()}
    c.shutdown()
    print(json.dumps(result))
