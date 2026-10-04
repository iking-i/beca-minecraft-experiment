"""TEST_ONLY evidence checks; no policy, no action execution, no inferred ACK."""
from copy import deepcopy

LIVE = 'LIVE_CAUSAL_VALIDATED'
INPUT = 'INPUT_ONLY_VALIDATED'
CONDITIONAL = 'CONDITIONAL_NOT_TESTED'
LIMITATION = 'CARRIER_LIMITATION'
FOUNDATIONS = ('ground_movement', 'completed_dig', 'placement', 'item_use', 'entity', 'container')


def at(a, b):
    return all(abs(a[k] - b[k]) < 1e-6 for k in ('x', 'y', 'z'))


def matching_blocks(records, position, block_type=None):
    return [r for r in records if r['direction'] == 'IN' and any(
        at(b['position'], position) and (block_type is None or b['block_type_id'] == block_type)
        for b in (r.get('normalized') or {}).get('blocks', []))]


def server_slot(records, slot, item_type, count, window_id=0):
    found = []
    for r in records:
        n = r.get('normalized') or {}
        if r['direction'] != 'IN' or n.get('window_id') != window_id:
            continue
        slots = n.get('slots', []) + ([n['slot']] if 'slot' in n else [])
        if any(s['slot'] == slot and s['item_type_id'] == item_type and s['count'] == count for s in slots):
            found.append(r)
    return found


def verdict(steps, consequence_records, measurable_difference, reason):
    # The wire record interval is bounded by the actual request/renewed frame.
    actions = [s for s in steps if s.get('action_code') is not None]
    sent = bool(actions) and all(s.get('input_sent') and s.get('out_wire_sequences')
                                and s.get('authorship') == 'TEST_ONLY' for s in actions)
    frames = bool(actions) and all(s.get('source_frame') and s.get('renewed_frame')
                                  and s['observation_version'] > s['source_version'] for s in actions)
    raw = [r for r in consequence_records if r.get('direction') == 'IN']
    status = LIVE if sent and frames and raw and measurable_difference else INPUT if sent else CONDITIONAL
    return {'status': status, 'step_ids': [s['step_id'] for s in steps],
            'server_wire_sequences': [r['wire_sequence'] for r in raw],
            'measurable_difference': deepcopy(measurable_difference), 'reason': reason}


def freeze_decision(chains):
    blockers = [key for key in FOUNDATIONS if chains.get(key, {}).get('status') != LIVE]
    return {'WORLD_ENTRY_FREEZE': 'blocked' if blockers else 'passed', 'blockers': blockers}
