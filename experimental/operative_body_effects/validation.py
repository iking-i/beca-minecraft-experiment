"""Collect exact synthetic causal evidence; never invokes a real carrier."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

from individual.observation import ObservationFrame
from individual.formal_l0 import digest
from .engine import EffectEngine, KEY

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    folder = Path(tempfile.mkdtemp(prefix='operative-effect-final-', dir=ROOT/'.test-tmp'))
    process_records = []
    for phase in ('create', 'resume'):
        done = subprocess.run([sys.executable, '-X', 'utf8', '-m',
            'experimental.operative_body_effects.runner', phase, str(folder/'canonical.db')],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        (folder/f'{phase}.stdout.json').write_text(done.stdout, encoding='utf-8')
        (folder/f'{phase}.stderr.txt').write_text(done.stderr, encoding='utf-8')
        if done.returncode:
            raise RuntimeError(done.stderr)
        process_records.append(json.loads(done.stdout))
    first, resumed = process_records
    activation = first['records'][3]
    before = activation['before']
    frame = ObservationFrame(**activation['after']['observation_frame'])
    route = next(ref for ref, r in before['internal_state']['l0_state'][KEY]['routes'].items()
                 if r['trigger']['kind'] == 'increased')
    controls = {}
    for name in ('present', 'ablated', 'restored'):
        internal = deepcopy(before['internal_state'])
        if name == 'ablated':
            del internal['l0_state'][KEY]['routes'][route]
            del internal['l0_state'][KEY]['supports'][route]
        after, _, journal = EffectEngine().advance(internal, deepcopy(frame), before['state_version'] + 1, [])
        packet = after.l0_state[KEY]['current']
        partial = next(p for k, p in journal if k == 'RECURSIVE_PARTIAL_OUTPUT')
        controls[name] = {'packet': packet, 'processing': partial['processing'],
                          'after': after.to_dict()}
    assert controls['present']['packet']['operations'] == controls['restored']['packet']['operations']
    assert controls['present']['packet']['operations'] and not controls['ablated']['packet']['operations']
    operation, = controls['present']['packet']['operations']
    assert digest(operation) in controls['present']['processing']['expected_outcomes']
    assert first['calls'] == [operation['expression']]
    assert first['end']['individual_id'] == resumed['start']['individual_id'] == resumed['end']['individual_id']
    assert first['pid'] != resumed['pid']
    with sqlite3.connect((folder/'canonical.db').as_uri() + '?mode=ro', uri=True) as db:
        events = [{'event_sequence': seq, 'state_version': version, 'event_type': kind,
                   'payload': json.loads(payload)} for seq, version, kind, payload in db.execute(
            "SELECT event_sequence,state_version,event_type,payload FROM events WHERE event_type IN "
            "('ACTION_REQUESTED','ACTION_EXECUTED','ACTION_FAILED','RECURSIVE_PARTIAL_OUTPUT') ORDER BY event_sequence")]
    persisted_partial = next(e for e in events if e['event_type'] == 'RECURSIVE_PARTIAL_OUTPUT'
                             and e['state_version'] == before['state_version'] + 1)
    assert digest(operation) in persisted_partial['payload']['processing']['expected_outcomes']
    requests = [e for e in events if e['event_type'] == 'ACTION_REQUESTED']
    assert len(requests) == 1 and requests[0]['payload']['args'] == operation['expression']
    report = {'classification': 'PARTIAL', 'local_scope': 'PASS',
        'real_world_scope': 'NOT_ESTABLISHED', 'minecraft_run': False,
        'mechanism_version': first['end']['internal_state']['l0_state'][KEY]['version'],
        'raw_evidence_directory': str(folder), 'process_records': process_records,
        'route_only_controls': controls, 'persisted_events': events,
        'expression': operation['expression'], 'route_identity': route,
        'same_individual': True, 'cross_process_route_persistence':
            first['end']['internal_state']['l0_state'][KEY]['routes'] ==
            resumed['start']['internal_state']['l0_state'][KEY]['routes'],
        'source_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'):
            hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [*HERE.glob('*.py'), ROOT/'tests/test_operative_body_effects.py']},
        'authorship': {'formation_and_effect_rule': 'EXTERNALLY_SUPPLIED_GENERIC_TEST_ONLY_MECHANISM',
            'initial_native_binding': 'EXTERNAL_SYNTHETIC_RECEIPT',
            'port_identity': 'ACTIVATED_FORMED_ROUTE_RECEIVER_NATIVE_OWNER',
            'parameter_value': 'CURRENT_EXACT_OCCURRENCE_AFTER_OPERAND',
            'activation': 'PERSISTED_ROUTE_MATCH_IN_ORDINARY_OPERATIVE_READ',
            'autonomous_port_choice_claimed': False},
        'remaining_real_boundary': 'No real native binding-incidence training source or eligible live occurrence verified; no port guessed or synthetic source relabeled',
        'nonclaims': ['real Minecraft execution', 'world-effect causal law',
            'autonomous goals/action selection', 'general expression adoption',
            'mainline adoption', 'sustained real-world closure', 'universal recursion']}
    with (HERE/'VALIDATION.json').open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
    print(json.dumps({'classification': report['classification'], 'expression': report['expression'],
                      'raw_evidence': str(folder), 'same_individual': True}))


if __name__ == '__main__':
    main()
