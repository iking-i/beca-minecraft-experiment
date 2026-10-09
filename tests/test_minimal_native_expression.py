from copy import deepcopy
from unittest.mock import patch

import pytest

from experimental.native_parameter_binding_extension.runner import create, receipt, slot_ref
from experimental.native_body_operands.runner import observation
from experimental.typed_operative_connection.engine import KEY as GRAPH, connection, value_ref
from experimental.operative_content.engine import KEY as CONTENT
from experimental.operative_content.runner import capture
from individual.formal_l0 import digest
from experimental.minimal_native_expression.expression import read_expression, OneAttempt


PORT = {'catalog_version': 2, 'code': 16}  # External measurement, not A's choice.


def sample(seq, value):
    raw = observation(seq, value, codes=(16,))
    raw.update(health=1, hunger=2)
    return raw


def setup(core, successor=1):
    core.accept_observation(sample(1, 0))
    raw = sample(2, successor)
    raw['typedExecutionReceipts'] = [receipt(raw, name='slot')]
    core.accept_observation(raw)
    core.accept_observation(sample(3, successor))


def test_actual_code16_candidates_not_selected(tmp_path):
    c = create(tmp_path/'a.db')
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            setup(c)
            before = c.state.to_dict()
            r = read_expression(before, PORT)
            assert r['status'] == 'AMBIGUOUS'
            assert {e['parameters']['slot'] for e in r['candidates']} == {0, 1}
            assert all(e['code'] == 16 and set(e['parameters']) == {'slot'} for e in r['candidates'])
            assert r['action_code_author'] == 'EXPERIMENTER_MEASUREMENT_PORT'
            with patch.object(c._bridge, 'call', side_effect=AssertionError('must not dispatch')):
                result = OneAttempt(tmp_path/'attempt.json').execute(c, PORT)
            assert result['classification'] == 'NOT_READY' and result['perform_attempts'] == 0
            assert c.state.to_dict() == before and not (tmp_path/'attempt.json').exists()
    finally:
        c.shutdown()


def test_ordinary_s1_ablation_changes_candidate_not_adoption(tmp_path):
    c = create(tmp_path/'a.db')
    try:
        setup(c)
        edge = digest(connection(slot_ref(sample(2, 1), 'slot'), value_ref(1)))
        baseline = c.state.to_dict()
        def remove(s):
            del s['l0_state'][GRAPH]['edges'][edge]
            return s
        rows = [capture(c, sample(4, 1)), capture(c, sample(4, 1), remove), capture(c, sample(4, 1))]
        candidates = []
        for row in rows:
            state = deepcopy(baseline)
            state['internal_state'] = row['after']
            candidates.append({e['parameters']['slot'] for e in read_expression(state, PORT)['candidates']})
        assert candidates == [{0, 1}, {0}, {0, 1}]
        assert c.state.to_dict() == baseline
    finally:
        c.shutdown()


@pytest.mark.parametrize('edit', ['provenance', 'order', 'distractor'])
def test_no_source_or_order_selector(tmp_path, edit):
    c = create(tmp_path/'a.db')
    try:
        setup(c)
        state = c.state.to_dict()
        graph = state['internal_state']['l0_state'][GRAPH]
        if edit == 'provenance':
            graph['evidence'] = {}
        elif edit == 'order':
            graph['edges'] = dict(reversed(list(graph['edges'].items())))
        else:
            state['internal_state']['units']['disconnected'] = {'unit_id': 'disconnected', 'pattern': []}
        r = read_expression(state, PORT)
        assert r['status'] == 'AMBIGUOUS' and {e['parameters']['slot'] for e in r['candidates']} == {0, 1}
    finally:
        c.shutdown()


@pytest.mark.parametrize('bad', ['missing', 'support', 'version', 'unavailable', 'schema', 'port'])
def test_missing_or_invalid_rejects_no_fill(tmp_path, bad):
    c = create(tmp_path/'a.db')
    try:
        setup(c)
        state = c.state.to_dict()
        p = deepcopy(PORT)
        local = state['internal_state']['l0_state']
        if bad == 'missing':
            local['content_execution']['constructed'] = []
            assert read_expression(state, p)['status'] == 'MISSING_BINDING'
            return
        if bad == 'support':
            for e in local[CONTENT]['evidence'].values():
                if e.get('direct_supports', {}).get('connection_refs'):
                    e['direct_supports']['connection_refs'] = ['forged']
        elif bad == 'version': p['catalog_version'] = 3
        elif bad == 'unavailable': state['observation_frame']['nearby_data']['body']['action_space'][0]['currently_available'] = False
        elif bad == 'schema': state['observation_frame']['nearby_data']['body']['action_space'][0]['parameter_schema']['required'] = []
        else: p['code'] = 8
        with pytest.raises(ValueError):
            read_expression(state, p)
    finally:
        c.shutdown()


@pytest.mark.parametrize('failure', [None, 'transport', 'receipt', 'observation'])
def test_one_attempt_mechanical_mock_tail_no_real_claim(tmp_path, failure):
    c = create(tmp_path/'a.db')
    try:
        setup(c, successor=0)  # Only external premise; no new-value authorship claim.
        assert read_expression(c.state.to_dict(), PORT)['status'] == 'UNIQUE'
        calls = []
        def call(method, args=None):
            calls.append((method, deepcopy(args)))
            if method == 'perform':
                if failure == 'transport': raise TimeoutError('uncertain, no retry')
                return {'code': 16, 'parameters': {'slot': 0 if failure != 'receipt' else 2},
                    'started_at': 'test-start', 'finished_at': 'test-end',
                    'result': {'input_sent': 1, 'effect_acknowledged': 0},
                    'effect_attribution': 'temporal_observation_only'}
            if failure == 'observation': raise TimeoutError('no renewed observation')
            return sample(4, 0)
        start = c.state.to_dict()
        gate = OneAttempt(tmp_path/'attempt.json')
        with patch.object(c._bridge, 'call', side_effect=call), \
             patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            result = gate.execute(c, PORT)
            with pytest.raises(FileExistsError): gate.execute(c, PORT)
        assert sum(m == 'perform' for m, _ in calls) == 1
        assert calls[0] == ('perform', {'code': 16, 'parameters': {'slot': 0}})
        assert (tmp_path/'attempt.json.result.json').is_file()
        if failure is None:
            assert result['classification'] == 'TRANSPORT_AND_REENTRY_COMPLETED'
            assert c.state.individual_id == start['individual_id']
            assert c.state.environment_sequence == start['environment_sequence'] + 1
            assert c.state.state_version > start['state_version']
            assert c.state.latest_action['status'] == 'executed'
        else:
            assert result['classification'] == ('FAIL' if failure == 'receipt' else 'NOT_TESTABLE')
            assert 'error' in result
            if failure == 'observation': assert c.state.latest_action['status'] == 'executed'
    finally:
        c.shutdown()
