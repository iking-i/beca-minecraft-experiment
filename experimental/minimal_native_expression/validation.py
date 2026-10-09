"""Offline measurement evidence; never starts Minecraft or claims a real loop."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from experimental.native_parameter_binding_extension.runner import create, receipt, slot_ref
from experimental.native_body_operands.runner import observation
from experimental.typed_operative_connection.runner import record
from experimental.typed_operative_connection.engine import connection, value_ref, KEY as GRAPH
from experimental.operative_content.runner import capture
from individual.formal_l0 import digest
from .expression import read_expression, OneAttempt

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PORT = {'catalog_version': 2, 'code': 16}


def sample(sequence, value):
    raw = observation(sequence, value, codes=(16,))
    raw.update(health=1, hunger=2)
    return raw


def main():
    report = {'baseline': '0dc73536cb5a6b5422e651c06724ce2efeee769c',
        'classification': 'NOT_READY', 'real_observation': False, 'minecraft_run': False,
        'physical_perform_attempts': 0, 'complete_candidate_expression_decoded': True,
        'internally_constructed_complete_expression_object': 'NOT_ESTABLISHED',
        'action_code_author': 'EXPERIMENTER_MEASUREMENT_PORT',
        'initial_parameter_author': 'EXTERNAL_SYNTHETIC_TYPED_RECEIPT',
        'new_parameter_candidate_author': 'EXPERIENCED_SCALAR_CONNECTION_AND_EXTERNAL_GENERIC_COMPOSITION',
        'expression_adoption': 'NOT_ESTABLISHED', 'real_closed_loop': 'NOT_ESTABLISHED',
        'automatic_retry': False, 'spec_sha256': hashlib.sha256((HERE/'SPEC.md').read_bytes()).hexdigest()}
    with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp', prefix='minimal-expression-evidence-') as temp:
        c = create(Path(temp)/'a.db')
        try:
            raw = sample(2, 1)
            raw['typedExecutionReceipts'] = [receipt(raw, name='slot')]
            with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
                report['history'] = [record(c, sample(1,0)), record(c, raw), record(c, sample(3,1))]
                state = c.state.to_dict()
                report['checkpoint'] = state
                report['read'] = read_expression(state, PORT)
                assert report['read']['status'] == 'AMBIGUOUS'
                assert {e['parameters']['slot'] for e in report['read']['candidates']} == {0,1}
                with patch.object(c._bridge, 'call', side_effect=AssertionError('no physical transport')):
                    report['execution_gate'] = OneAttempt(Path(temp)/'attempt.json').execute(c, PORT)
                edge = digest(connection(slot_ref(raw,'slot'), value_ref(1)))
                def remove(internal):
                    del internal['l0_state'][GRAPH]['edges'][edge]
                    return internal
                rows = {'present':capture(c,sample(4,1)), 'ablated':capture(c,sample(4,1),remove), 'restored':capture(c,sample(4,1))}
                report['comparisons'] = rows
                reads = {}
                for name,row in rows.items():
                    s = deepcopy(state)
                    s['internal_state'] = row['after']
                    reads[name] = read_expression(s,PORT)
                report['comparison_reads'] = reads
                assert [{e['parameters']['slot'] for e in reads[n]['candidates']} for n in ('present','ablated','restored')] == [{0,1},{0},{0,1}]
                assert c.state.to_dict() == state
                report['canonical_state_unchanged_by_controls'] = True
            report['first_execution_blocker'] = 'TWO_COMPLETE_CANDIDATES_NO_INTERNAL_ADOPTION_RELATION'
            report['real_input_interface_limit'] = 'Frozen receipt admission accepts only external synthetic typed incidence; real ACTION_EXECUTED receipts are not automatically reified as typed receipt assignments.'
            report['real_gate_not_reached'] = True
        finally:
            c.shutdown('TEST_ONLY_expression_boundary_close')
    report['source_sha256'] = {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*.py'), ROOT/'tests/test_minimal_native_expression.py']}
    (HERE/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('NOT_READY: complete candidates slot=0/1; physical attempts=0; no internal adoption')


if __name__ == '__main__': main()
