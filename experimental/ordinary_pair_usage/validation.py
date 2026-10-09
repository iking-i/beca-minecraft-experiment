"""Offline saved-data comparison; never starts a Core/body or writes the source DB."""
from copy import deepcopy
import json
from pathlib import Path
from collections import Counter
from individual.formal_l0 import FormalLimits
from experimental.observation_interface_references.real.adapter import RealEncoder, RealEffectEngine, canonical_observation
from .engine import UsageRealEngine, MODE, VERSION

EVIDENCE = Path('experimental/observation_interface_references/evidence/host-controlled-world-run1/REPORT.json')

def saved_inputs():
    r = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    record = r['records'][-1]
    state = deepcopy(record['state_before'])
    a = r['recursive_executions'][0]['payload']
    raw = canonical_observation(record['raw_observation'])
    raw['nativeExecutionRecords'] = [{'action_id': a['action_id'], 'source': 'NATIVE_BRIDGE_EXECUTION',
        'request': deepcopy(a['args']), 'receipt': deepcopy(a['result']),
        'before_frame_id': state['observation_frame']['frame_id'], 'individual_id': state['individual_id']}]
    frame = RealEncoder(state['individual_id']).encode(raw, state['environment_sequence']+1, state['carrier_epoch'])
    pending = [{'action_id': a['action_id'], 'action_code': a['action_code'],
                'parameters': deepcopy(a['args']['parameters']), 'status': a['status']}]
    return state, frame, pending

def compare_saved():
    state, frame, pending = saved_inputs()
    current = deepcopy(state['internal_state']); local = current['l0_state']
    caps = FormalLimits(**local['locked_caps']); resources = local['locked_resource_caps']
    try:
        RealEffectEngine(caps, resources).advance(deepcopy(current), deepcopy(frame), state['state_version']+1, pending)
    except Exception as error:
        old_error = {'type': type(error).__name__, 'message': str(error)}
    else:
        old_error = None
    current['l0_state'][MODE] = {'version': VERSION}
    output, encoded, events = UsageRealEngine(caps, resources).advance(current, frame, state['state_version']+1, pending)
    pool = output.l0_state['observation_interface_references_test_only']
    packet = output.l0_state['observation_reference_effects_test_only']['current']
    experiences = [v for k,v in events if k=='EXPERIENCE_FORMED']
    return {'scope': 'OFFLINE_SAVED_REAL_DATA_NOT_LIVE', 'old_error':old_error,
        'units':len(output.units),'content_nodes':len(pool['nodes']),
        'content_types':dict(Counter(n['type'] for n in pool['nodes'].values())),
        'effects':len(packet['effects']),'operations':len(packet['operations']),
        'capacity_total':len(output.units)+len(pool['nodes'])+len(packet['effects'])+len(packet['operations']),
        'reused_content':output.l0_state['body_reference_execution']['reused_content'],
        'numeric_channels_retained':len(encoded.numeric_channels),
        'exact_numeric_input_retained':encoded.numeric_channels==frame.numeric_channels,
        'receipt_reentered':pending[0]['action_id'] in experiences[-1]['action_ids'],
        'experiences':experiences,'routes':len(output.l0_state['observation_reference_effects_test_only']['routes'])}

if __name__=='__main__':
    print(json.dumps(compare_saved(),ensure_ascii=False,indent=2))
