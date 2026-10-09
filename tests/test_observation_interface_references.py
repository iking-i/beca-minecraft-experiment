"""Offline receipt-shaped carrier tests; none are Minecraft execution evidence."""
from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from experimental.observation_interface_references.reference.references import KEY as REF_KEY
from experimental.observation_interface_references.effects.channel import EffectConfig
from experimental.observation_interface_references.effects.engine import KEY
from experimental.observation_interface_references.real.channel import RealEffectCore, BOOTSTRAP


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
        from experimental.observation_interface_references.real.adapter import assignments
        raw = sample(2, 1)
        frame = c._encoder.encode(raw, 2, c._body_epoch)
        # Direct negative admission fixture removes all exact integer-zero
        # evidence. It is not fed into the live run or claimed as real input.
        frame.numeric_channels = {k: v for k, v in frame.numeric_channels.items() if v != 0}
        action_id, record = next(iter(c._native_records.items()))
        experience = {'frame_ids': [c.state.observation_frame['frame_id'], frame.frame_id],
            'action_ids': [action_id], 'action_statuses': ['executed'],
            'action_parameters': [BOOTSTRAP['parameters']]}
        with pytest.raises(ValueError, match='observed|observation'):
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
    from experimental.observation_interface_references.real import live
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


def saved_real():
    import json
    from pathlib import Path
    return json.loads(Path('experimental/operative_body_real/evidence/attempt-3/REPORT.json')
                      .read_text(encoding='utf-8'))['records'][0]['raw_observation']


def test_full_saved_real_observation_admission_is_offline_not_live(tmp_path):
    from individual.internal_state import InternalState
    from experimental.observation_interface_references.reference.references import fact_ref, resolve, observation_ref
    from experimental.native_body_operands.engine import typed_inputs
    c = create(tmp_path / 'offline-real-sample.db')
    try:
        raw = saved_real(); original = deepcopy(raw)
        c.accept_observation(raw)
        assert raw == original and not c._bridge.calls
        frame = c.state.observation_frame
        internal = InternalState.from_dict(c.state.internal_state)
        pool = internal.l0_state[REF_KEY]
        assert len(frame['numeric_channels']) == 376
        assert len(pool['current_source']['references']) == 64
        assert len(pool['catalog']['declarations']) == 47
        assert pool['current_source']['numeric_channels'] == frame['numeric_channels']
        assert len(internal.units) == 3 and not pool['nodes']
        assert not any(u.get('operand_kind') == 'REFERENCE_SENSOR' for u in internal.units.values())
        for channel, value in frame['numeric_channels'].items():
            address = fact_ref(internal, frame['frame_id'], channel)
            assert resolve(internal, address)['value'] == value
        atoms = typed_inputs(pool['current_source'])
        for key, node in atoms.items():
            if node['type'] in ('ObservedValue', 'ObservedReference'):
                assert resolve(internal, observation_ref(internal, key)) == node
        assert c._store.latest_state().to_dict() == c.state.to_dict()
    finally:
        c.shutdown()


@pytest.mark.parametrize('mutation', ['frame', 'channel', 'digest', 'namespace', 'node'])
def test_foreign_and_forged_observation_addresses_reject(tmp_path, mutation):
    from individual.internal_state import InternalState
    from experimental.observation_interface_references.reference.references import fact_ref, resolve
    from experimental.observation_interface_references.reference.engine import value_ref
    c = create(tmp_path / 'forged.db')
    try:
        c.accept_observation(sample(1, 0))
        internal = InternalState.from_dict(c.state.internal_state)
        source = internal.l0_state[REF_KEY]['current_source']
        if mutation in ('namespace', 'node'):
            ref = value_ref(0, internal)
            ref[mutation] = 'foreign'
        else:
            ref = fact_ref(internal, source['frame_id'], next(iter(source['numeric_channels'])))
            ref[{'frame': 'frame_id', 'channel': 'channel_id', 'digest': 'source_digest'}[mutation]] = 'foreign'
        with pytest.raises(ValueError): resolve(internal, ref)
    finally:
        c.shutdown()


def test_old_object_reference_not_current_and_numeric_provenance_retained(tmp_path):
    from individual.internal_state import InternalState
    from experimental.observation_interface_references.reference.references import fact_ref, resolve, observation_ref
    from experimental.native_body_operands.engine import typed_inputs
    c = create(tmp_path / 'stale.db')
    try:
        c.accept_observation(saved_real())
        internal = InternalState.from_dict(c.state.internal_state)
        pool = internal.l0_state[REF_KEY]
        key = next(k for k, v in typed_inputs(pool['current_source']).items() if v['type'] == 'ObservedReference')
        address = observation_ref(internal, key)
        historic = fact_ref(internal, pool['current_source']['frame_id'], next(iter(pool['current_source']['numeric_channels'])))
        pool['current_source'] = deepcopy(pool['current_source'])
        pool['current_source']['references'] = []
        with pytest.raises(ValueError, match='Stale'): resolve(internal, address)
        assert resolve(internal, historic)['type'] == 'ObservedValue'
    finally:
        c.shutdown()


def test_actual_formed_structure_capacity_still_rejects_atomically(tmp_path):
    from individual.internal_state import InternalState
    from experimental.observation_interface_references.reference.engine import validate
    from experimental.operative_content.engine import ContentCapacityError
    c = create(tmp_path / 'capacity.db')
    try:
        c.accept_observation(saved_real())
        internal = InternalState.from_dict(c.state.internal_state)
        for i in range(62):
            name = 'actual-structure-' + str(i)
            internal.units[name] = {'unit_id': name, 'pattern': {'i': i}}
        with pytest.raises(ContentCapacityError): validate(internal)
        assert len(c.state.internal_state['units']) == 3
    finally:
        c.shutdown()


@pytest.mark.parametrize('mutation', ['channel', 'interval', 'current_packet'])
def test_effect_cannot_cross_observation_provenance(tmp_path, mutation):
    from individual.internal_state import InternalState
    from individual.formal_l0 import digest
    from experimental.observation_interface_references.effects.engine import validate
    from experimental.observation_interface_references.effects.channel import validate_state
    c = create(tmp_path / 'cross-frame.db')
    try:
        c.accept_observation(sample(1, 0)); c.bootstrap_once()
        c.accept_observation(sample(2, 1)); c.accept_observation(sample(3, 0))
        state = deepcopy(c.state.to_dict())
        internal = InternalState.from_dict(state['internal_state'])
        if mutation == 'current_packet':
            internal.l0_state[KEY]['current']['frame_id'] = 'foreign:E2'
            state['internal_state'] = internal.to_dict()
            with pytest.raises(ValueError): validate_state(state, c._effect_config)
        elif mutation == 'interval':
            support = next(iter(internal.l0_state[KEY]['supports'].values()))
            support['formation']['frame_ids'] = [c.state.individual_id + ':E1', c.state.individual_id + ':E3']
            with pytest.raises(ValueError): validate(internal)
        else:
            pool = internal.l0_state[KEY]
            key = next(iter(pool['routes']))
            route, support = pool['routes'].pop(key), pool['supports'].pop(key)
            route['trigger']['channel_id'] = '9999999999999999999'
            support['formation']['change_fact']['channel_id'] = route['trigger']['channel_id']
            pool['routes'][digest(route)] = route
            pool['supports'][digest(route)] = support
            with pytest.raises(ValueError): validate(internal)
    finally:
        c.shutdown()


def test_real_unit_cap_rejects_new_observation_without_partial_commit(tmp_path):
    from individual.internal_state import InternalState
    from experimental.operative_content.engine import ContentCapacityError
    c = create(tmp_path / 'unit-limit.db')
    try:
        c.accept_observation(sample(1, 0))
        original = c.state.to_dict()
        internal = InternalState.from_dict(c.state.internal_state)
        while len(internal.units) < 64:
            name = 'formed-' + str(len(internal.units))
            internal.units[name] = {'unit_id': name, 'pattern': {'actual': name}}
        frame = c._encoder.encode(sample(2, 1), 2, c._body_epoch)
        with pytest.raises(ContentCapacityError):
            c._engine.advance(internal.to_dict(), frame, c.state.state_version + 1, [])
        assert c.state.to_dict() == original == c._store.latest_state().to_dict()
    finally:
        c.shutdown()


def test_old_frozen_carrier_database_is_not_silently_migrated(tmp_path):
    import hashlib
    from experimental.operative_body_real.channel import RealEffectCore as OldCore
    from experimental.operative_body_effects.channel import EffectConfig as OldConfig
    path = tmp_path / 'old.db'
    old = OldCore(path, ReceiptBridge(), initialize_lifetime=True,
                  config=OldConfig(str(path), origin_state=initial()[0]))
    old.shutdown()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        RealEffectCore(path, ReceiptBridge(), config=EffectConfig(str(path)))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_persisted_routes_and_ordinary_content_reuse_across_real_processes(tmp_path):
    import os, json, subprocess, sys
    path = tmp_path / 'restart.db'
    module = 'experimental.observation_interface_references.validation'
    outputs = []
    for phase in ('create', 'resume'):
        result = subprocess.run([sys.executable, '-X', 'utf8', '-m', module, phase, str(path)],
                                capture_output=True, encoding='utf-8')
        assert result.returncode == 0, result.stderr
        outputs.append(json.loads(result.stdout))
    first, resumed = outputs
    assert first['pid'] != resumed['pid'] and first['pid'] != os.getpid()
    assert first['individual_id'] == resumed['individual_id']
    assert first['routes'] == resumed['restored_routes']
    assert resumed['state_version'] > first['state_version']
    assert first['calls'] == [{'code': 16, 'parameters': {'slot': 0}}]
    # The frozen carrier also produces no fresh activation in this restart
    # interval. Persisted routes are not commands to replay at resume.
    assert resumed['calls'] == []
    assert first['authoritative'] and resumed['authoritative'] and resumed['reused_content']
