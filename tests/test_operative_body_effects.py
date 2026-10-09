from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from individual.internal_state import InternalState
from individual.formal_l0 import digest
from experimental.formall0_operative.validation import initial
from experimental.formall0_continuous.runner import FakeBridge
from experimental.body_interface_references.runner import sample, supplied_receipt, binding_values
from experimental.body_interface_references.references import KEY as REF_KEY
from experimental.operative_body_effects.engine import KEY, validate
from experimental.operative_body_effects.channel import EffectCore, EffectConfig


class RecordingBridge(FakeBridge):
    def __init__(self, failure=None):
        super().__init__()
        self.calls = []
        self.failure = failure

    def call(self, method, args=None):
        assert method == 'perform'
        self.calls.append(deepcopy(args))
        if self.failure == 'timeout':
            raise TimeoutError('synthetic uncertain transport')
        return {'code': args['code'] if self.failure != 'mismatch' else -1,
                'parameters': deepcopy(args['parameters']), 'started_at': 'mock:start',
                'finished_at': 'mock:end', 'result': {'input_sent': 1, 'effect_acknowledged': 0},
                'effect_attribution': 'temporal_observation_only'}


def create(path, bridge=None, cells=None, names=None):
    state = initial(names=names)[0] if names else initial()[0]
    return EffectCore(path, bridge or RecordingBridge(), initialize_lifetime=True,
                      config=EffectConfig(str(path), origin_state=state, cells=cells))


def learn(core, receivers=((16, 'slot'),), change=1):
    core.accept_observation(sample(1, 0))
    raw = sample(2, change)
    receipts = []
    for i, (code, name) in enumerate(receivers):
        r = supplied_receipt(core, raw, code=code, name=name)
        r['execution_id'] += str(i)
        receipts.append(r)
    raw['typedExecutionReceipts'] = receipts
    core.accept_observation(raw)


def current_read(core, value, edit=None):
    state = deepcopy(core.state.internal_state)
    if edit:
        edit(state)
    frame = core._encoder.encode(sample(3, value), core.state.environment_sequence + 1, core._body_epoch)
    return core._engine.advance(state, frame, core.state.state_version + 1, [])


@pytest.fixture
def core(tmp_path):
    c = create(tmp_path / 'effect.db')
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler forbidden')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder forbidden')):
            learn(c)
            yield c
    finally:
        c.shutdown('TEST_ONLY_effect_test_close')


def test_route_forms_but_formation_round_does_not_execute(core):
    pool = core.state.internal_state['l0_state'][KEY]
    assert len(pool['routes']) == 1
    assert not pool['current']['effects']
    assert core._bridge.calls == []
    assert binding_values(InternalState.from_dict(core.state.internal_state)) == [0, 1]
    assert core._store.latest_state().to_dict() == core.state.to_dict()


def test_fresh_occurrence_forms_operation_inside_normal_operands(core):
    core.accept_observation(sample(3, 0))
    assert core._bridge.calls == []
    before_version = core.state.state_version
    state = deepcopy(core.state.internal_state)
    frame = core._encoder.encode(sample(4, 1), core.state.environment_sequence + 1, core._body_epoch)
    after, _, journal = core._engine.advance(state, frame, before_version + 1, [])
    packet = after.l0_state[KEY]['current']
    assert packet['body_status'] == 'READY'
    operation, = packet['operations']
    assert operation['expression'] == {'code': 16, 'parameters': {'slot': 1}}
    partial = next(p for kind, p in journal if kind == 'RECURSIVE_PARTIAL_OUTPUT')
    assert digest(operation) in partial['processing']['expected_outcomes']
    assert set(packet['effects']) <= set(partial['processing']['expected_outcomes'])
    core.accept_observation(sample(4, 1))
    assert core._bridge.calls == [operation['expression']]
    assert core.state.individual_id == core._store.latest_state().individual_id
    assert core.state.latest_action['status'] == 'executed'
    assert binding_values(InternalState.from_dict(core.state.internal_state)) == [0, 1]
    core._dispatch_current_effect()
    assert len(core._bridge.calls) == 1
    core.accept_observation(sample(5, 1))
    assert not core._pending_actions
    assert len(core._bridge.calls) == 1


def test_route_only_ablation_restore_actual_operation(core):
    core.accept_observation(sample(3, 0))
    original = deepcopy(core.state.internal_state)
    target = next(ref for ref, route in original['l0_state'][KEY]['routes'].items()
                  if route['trigger']['kind'] == 'increased')
    def ablate(s):
        del s['l0_state'][KEY]['routes'][target]
        del s['l0_state'][KEY]['supports'][target]
    rows = [current_read(core, 1), current_read(core, 1, ablate), current_read(core, 1)]
    ops = [r[0].l0_state[KEY]['current']['operations'] for r in rows]
    assert ops[0] == ops[2] and ops[0] and not ops[1]
    assert core.state.internal_state == original


def test_stable_input_and_historical_pairs_do_not_activate(core):
    core.accept_observation(sample(3, 1))
    assert core.state.internal_state['l0_state'][REF_KEY]['nodes']
    assert not core.state.internal_state['l0_state'][KEY]['current']['effects']
    assert not core._bridge.calls


def test_wrong_channel_cannot_activate(core):
    raw = sample(3, 0); raw['health'] = 0
    core.accept_observation(raw)
    raw = sample(4, 0); raw['health'] = 1
    core.accept_observation(raw)
    assert core.state.internal_state['l0_state'][KEY]['current']['effects'] == {}
    assert not core._bridge.calls


def test_missing_support_and_forged_receiver_reject(core):
    internal = InternalState.from_dict(core.state.internal_state)
    route = next(iter(internal.l0_state[KEY]['routes']))
    del internal.l0_state[KEY]['supports'][route]
    with pytest.raises(ValueError): validate(internal)
    internal = InternalState.from_dict(core.state.internal_state)
    r = internal.l0_state[KEY]['routes'].pop(route)
    support = internal.l0_state[KEY]['supports'].pop(route)
    r['receiver']['code'] = 999
    internal.l0_state[KEY]['routes'][digest(r)] = r
    internal.l0_state[KEY]['supports'][digest(r)] = support
    with pytest.raises(ValueError): validate(internal)


@pytest.mark.parametrize('failure', ['timeout', 'mismatch'])
def test_failure_never_retries(tmp_path, failure):
    bridge = RecordingBridge(failure)
    c = create(tmp_path / 'uncertain.db', bridge)
    try:
        learn(c); c.accept_observation(sample(3, 0)); c.accept_observation(sample(4, 1))
        assert c.state.latest_action['status'] == 'failed'
        c._dispatch_current_effect()
        assert len(bridge.calls) == 1
        assert list(c.state.internal_state['l0_state'][KEY]['attempts'].values())[0]['status'] == 'failed'
    finally:
        c.shutdown()


def test_no_external_action_entry(core):
    for method in (core.execute_action, core.execute_discrete_action):
        with pytest.raises(RuntimeError): method(16, {'slot': 1})
    assert core._bridge.calls == []


@pytest.mark.parametrize('receivers,status', [(((8, 'yaw_delta'),), 'INCOMPLETE'),
    (((16, 'slot'), (35, 'hand')), 'CONCURRENT_PHYSICAL_OPERATIONS')])
def test_no_filler_or_physical_order(tmp_path, receivers, status):
    c = create(tmp_path / 'conflict.db')
    try:
        learn(c, receivers)
        c.accept_observation(sample(3, 0)); c.accept_observation(sample(4, 1))
        assert c.state.internal_state['l0_state'][KEY]['current']['body_status'] == status
        assert not c._bridge.calls
    finally:
        c.shutdown()


def test_internal_cell_same_occurrence_rule(tmp_path):
    c = create(tmp_path / 'cell.db', cells={'opaque-cell': {'value_type': 'integer', 'value': 0}})
    try:
        learn(c, receivers=())
        assert c.state.internal_state['l0_state'][KEY]['routes']
        c.accept_observation(sample(3, 0)); c.accept_observation(sample(4, 1))
        assert c.state.internal_state['l0_state'][KEY]['cells']['opaque-cell']['value'] == 1
        assert not c._bridge.calls
    finally:
        c.shutdown()


def test_different_histories_same_current_materials(tmp_path):
    operations = []
    for i, change in enumerate((1, 2)):
        c = create(tmp_path / f'history-{i}.db')
        try:
            learn(c, change=change)
            c.accept_observation(sample(3, 0))
            after, _, _ = current_read(c, 1)
            operations.append(after.l0_state[KEY]['current']['operations'])
        finally:
            c.shutdown()
    assert operations[0] and not operations[1]


def test_port_identity_follows_formed_history_not_fixed_code(tmp_path):
    outputs = []
    for index, (code, name) in enumerate(((16, 'slot'), (35, 'hand'))):
        c = create(tmp_path / f'port-{index}.db', names=('arbitrary-origin', 'arbitrary-dependency'))
        try:
            learn(c, receivers=((code, name),))
            c.accept_observation(sample(3, 0)); c.accept_observation(sample(4, 1))
            outputs.append(c._bridge.calls)
        finally:
            c.shutdown()
    assert outputs == [[{'code': 16, 'parameters': {'slot': 1}}],
                       [{'code': 35, 'parameters': {'hand': 1}}]]


def test_shared_capacity_still_64(core):
    from experimental.operative_content.engine import ContentCapacityError
    internal = InternalState.from_dict(core.state.internal_state)
    while len(internal.units) + len(internal.l0_state[REF_KEY]['nodes']) < 64:
        key = f'opaque-capacity-{len(internal.units)}'
        internal.units[key] = {'unit_id': key, 'pattern': []}
    validate(internal)
    internal.l0_state[KEY]['cells']['extra'] = {'value_type': 'integer', 'value': 0}
    with pytest.raises(ContentCapacityError): validate(internal)


def test_conflicting_values_never_choose(tmp_path):
    c = create(tmp_path / 'values-conflict.db')
    try:
        raw = sample(1, 0); raw['health'] = 0; c.accept_observation(raw)
        raw = sample(2, 1); raw['health'] = 2
        raw['typedExecutionReceipts'] = [supplied_receipt(c, raw)]
        c.accept_observation(raw)
        raw = sample(3, 0); raw['health'] = 0; c.accept_observation(raw)
        raw = sample(4, 1); raw['health'] = 2; c.accept_observation(raw)
        packet = c.state.internal_state['l0_state'][KEY]['current']
        assert packet['body_status'] == 'CONFLICTING_ACTIVATIONS'
        assert len(packet['effects']) == 2
        assert not c._bridge.calls
    finally:
        c.shutdown()


def test_provenance_and_unconnected_route_do_not_choose(core):
    core.accept_observation(sample(3, 0))
    plain = current_read(core, 1)[0]
    def edit(s):
        for support in s['l0_state'][KEY]['supports'].values():
            support['formation']['provenance'] = 'UNIFORM_SWAPPED_LABEL'
        s['units']['opaque-unrelated'] = {'unit_id': 'opaque-unrelated', 'pattern': []}
    changed = current_read(core, 1, edit)[0]
    assert plain.l0_state[KEY]['current']['operations'] == changed.l0_state[KEY]['current']['operations']


def test_forged_operation_packet_rejected(core):
    core.accept_observation(sample(3, 0))
    after, frame, _ = current_read(core, 1)
    state = {**core.state.to_dict(), 'internal_state': after.to_dict(), 'observation_frame': frame.to_dict()}
    from experimental.operative_body_effects.channel import validate_state
    validate_state(state, core._effect_config)
    state['internal_state']['l0_state'][KEY]['current']['operations'][0]['expression']['parameters']['slot'] = 0
    with pytest.raises(ValueError, match='activated endpoints'):
        validate_state(state, core._effect_config)


def test_default_core_cannot_adopt_effect_database(core):
    from individual.core import ACore
    with pytest.raises(ValueError): ACore(core._store.path, RecordingBridge())


def test_restart_restores_routes_and_does_not_replay_saved_effect(tmp_path):
    from experimental.operative_body_effects.runner import run
    db = tmp_path / 'restart.db'
    records = []
    for phase in ('create', 'resume'):
        command = [sys.executable, '-X', 'utf8', '-m', 'experimental.operative_body_effects.runner', phase, str(db)]
        done = subprocess.run(command, text=True, encoding='utf-8', capture_output=True)
        assert done.returncode == 0, done.stderr
        records.append(json.loads(done.stdout))
    a, b = records
    assert a['pid'] != b['pid']
    assert a['end']['individual_id'] == b['start']['individual_id'] == b['end']['individual_id']
    assert a['end']['internal_state']['l0_state'][KEY]['routes'] == b['start']['internal_state']['l0_state'][KEY]['routes']
    assert b['end']['state_version'] > a['end']['state_version']
    assert not b['calls']
