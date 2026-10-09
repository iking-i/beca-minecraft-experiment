"""Offline receipt-shaped carrier tests; none are Minecraft execution evidence."""
from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from experimental.body_interface_references.references import KEY as REF_KEY
from experimental.operative_body_effects.channel import EffectConfig
from experimental.operative_body_effects.engine import KEY
from experimental.operative_body_real.channel import RealEffectCore, BOOTSTRAP


class ReceiptBridge(FakeBridge):
    def __init__(self, mismatch=False):
        self.calls = []
        self.core = None
        self.mismatch = mismatch

    def call(self, method, args=None):
        assert method == 'perform'
        self.calls.append(deepcopy(args))
        start = self.core.state.observation_frame['timestamp']
        end = (datetime.fromisoformat(start) + timedelta(milliseconds=10)).isoformat()
        return {'code': -1 if self.mismatch else args['code'], 'parameters': deepcopy(args['parameters']),
                'started_at': start, 'finished_at': end, 'before': {}, 'after': {},
                'result': {'input_sent': 1, 'effect_acknowledged': 0},
                'effect_attribution': 'temporal_observation_only'}


def create(path, bridge=None):
    b = bridge or ReceiptBridge()
    core = RealEffectCore(path, b, initialize_lifetime=True,
        config=EffectConfig(str(path), origin_state=initial()[0]))
    b.core = core
    return core


def test_actual_owned_request_receipt_enters_ordinary_integration(tmp_path):
    c = create(tmp_path / 'native.db')
    try:
        c.accept_observation(sample(1, 0))
        action = c.bootstrap_once()
        assert c._bridge.calls == [BOOTSTRAP]
        c.accept_observation(sample(2, 1))
        pool = c.state.internal_state['l0_state'][REF_KEY]
        records = [e['supports']['record'] for e in pool['evidence'].values()
                   if e['supports'].get('kind') == 'RECORDED_NATIVE_EXECUTION_INCIDENCE']
        assert len(records) == 1
        assert records[0]['source'] == 'OFFLINE_RECEIPT_ADAPTER_TEST'
        assert records[0]['action_id'] == action['action_id']
        assert c.state.internal_state['l0_state'][KEY]['routes']
        assert len(c._bridge.calls) == 1  # formation is not activation
        c.accept_observation(sample(3, 0))
        c.accept_observation(sample(4, 1))
        assert c._bridge.calls == [BOOTSTRAP, {'code': 16, 'parameters': {'slot': 1}}]
        generated = c.state.latest_action['action_id']
        c.accept_observation(sample(5, 1))
        import json
        row = c._store.connection.execute("SELECT payload FROM events WHERE event_type='EXPERIENCE_FORMED' ORDER BY event_sequence DESC LIMIT 1").fetchone()
        assert generated in json.loads(row[0])['action_ids']
        assert c._store.latest_state().to_dict() == c.state.to_dict()
        assert not c._native_records
    finally:
        c.shutdown()


@pytest.mark.parametrize('key', ['typedExecutionReceipts', 'nativeExecutionRecords'])
def test_no_injected_receipt_artifact(tmp_path, key):
    c = create(tmp_path / 'inject.db')
    try:
        raw = sample(1, 0); raw[key] = [{}]
        with pytest.raises(ValueError, match='caller-supplied'): c.accept_observation(raw)
        assert not c._bridge.calls
    finally:
        c.shutdown()


def test_unobserved_parameter_cannot_become_sensor_material(tmp_path):
    c = create(tmp_path / 'missing.db')
    try:
        c.accept_observation(sample(1, 0)); c.bootstrap_once()
        from individual.internal_state import InternalState
        from experimental.operative_body_real.adapter import assignments
        raw = sample(2, 1)
        frame = c._encoder.encode(raw, 2, c._body_epoch)
        # Direct negative admission fixture removes all exact integer-zero
        # evidence. It is not fed into the live run or claimed as real input.
        frame.numeric_channels = {k: v for k, v in frame.numeric_channels.items() if v != 0}
        action_id, record = next(iter(c._native_records.items()))
        experience = {'frame_ids': [c.state.observation_frame['frame_id'], frame.frame_id],
            'action_ids': [action_id], 'action_statuses': ['executed'],
            'action_parameters': [BOOTSTRAP['parameters']]}
        with pytest.raises(ValueError, match='not current observed'):
            assignments(InternalState.from_dict(c.state.internal_state), frame, record, experience)
        assert len(c._bridge.calls) == 1
    finally:
        c.shutdown()


def test_foreign_action_identity_rejected(tmp_path):
    c = create(tmp_path / 'identity.db')
    try:
        c.accept_observation(sample(1, 0)); c.bootstrap_once()
        record = next(iter(c._native_records.values()))
        record['before_frame_id'] = 'foreign:E1'
        with pytest.raises(ValueError, match='live experience'): c.accept_observation(sample(2, 1))
        assert len(c._bridge.calls) == 1
    finally:
        c.shutdown()


def test_bootstrap_and_failure_never_retry(tmp_path):
    c = create(tmp_path / 'failure.db', ReceiptBridge(mismatch=True))
    try:
        c.accept_observation(sample(1, 0))
        with pytest.raises(ValueError, match='mismatch'): c.bootstrap_once()
        with pytest.raises(ValueError, match='once'): c.bootstrap_once()
        assert len(c._bridge.calls) == 1
        assert c.state.latest_action['status'] == 'failed'
    finally:
        c.shutdown()


def test_ablation_removes_real_receipt_based_activation(tmp_path):
    c = create(tmp_path / 'ablation.db')
    try:
        c.accept_observation(sample(1, 0)); c.bootstrap_once()
        c.accept_observation(sample(2, 1)); c.accept_observation(sample(3, 0))
        state = deepcopy(c.state.internal_state)
        frame = c._encoder.encode(sample(4, 1), 4, c._body_epoch)
        a = c._engine.advance(state, deepcopy(frame), c.state.state_version + 1, [])[0]
        ablated = deepcopy(state)
        ablated['l0_state'][KEY]['routes'] = {}
        ablated['l0_state'][KEY]['supports'] = {}
        b = c._engine.advance(ablated, deepcopy(frame), c.state.state_version + 1, [])[0]
        restored = c._engine.advance(state, deepcopy(frame), c.state.state_version + 1, [])[0]
        assert a.l0_state[KEY]['current']['operations']
        assert not b.l0_state[KEY]['current']['operations']
        assert a.l0_state[KEY]['current']['operations'] == restored.l0_state[KEY]['current']['operations']
    finally:
        c.shutdown()


def test_collector_records_startup_failure_and_closes_owned_core(tmp_path, monkeypatch):
    from experimental.operative_body_real import live
    class Unavailable(ReceiptBridge):
        alive = True
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.closed = False
        def launch(self):
            pass
        def drain_events(self):
            return []
        def call(self, method, args=None, timeout=None):
            assert method in ('start', 'status')
            return {'connected': False, 'state': 'disconnected',
                    'lastError': {'code': 'TEST_OFFLINE', 'message': 'No real carrier'}}
        def close(self):
            self.closed = True
    monkeypatch.setattr(live, 'MinecraftBridge', Unavailable)
    directory = tmp_path / 'collector'
    report = live.run(directory, 1)
    assert report['classification'] == 'NOT_TESTABLE'
    assert report['bootstrap'] is None
    assert not report['records']
    assert report['shutdown_state']['state_version'] > report['final_committed_state']['state_version']
    assert (directory / 'REPORT.json').is_file()


def test_wire_required_order_is_semantically_canonical_not_filtered(tmp_path):
    c = create(tmp_path / 'wire-order.db')
    try:
        raw = sample(1, 0)
        for entry in raw['actionSpace']:
            entry['parameter_schema']['required'].reverse()
        original = deepcopy(raw)
        c.accept_observation(raw)
        assert raw == original
        pool = c.state.internal_state['l0_state'][REF_KEY]
        assert len(pool['catalog']['declarations']) == 47
        for entry in pool['catalog']['declarations']:
            assert entry['parameter_schema']['required'] == sorted(entry['parameter_schema']['required'])
        assert len(c.state.internal_state['units']) < 64
    finally:
        c.shutdown()
