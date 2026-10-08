"""Ordinary-Core native input causality. No Minecraft or body requests."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from unittest.mock import patch

import pytest

from individual.core import ACore
from individual.internal_state import InternalState
from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.operative_content.channel import ContentConfig, ContentCore
from experimental.operative_content.engine import KEY as CONTENT, ContentCapacityError, identity
from experimental.native_body_operands.channel import NativeConfig, NativeCore
from experimental.native_body_operands.engine import KEY, validate_native
from experimental.native_body_operands.runner import create, reopen, observation, capture


def setup(core):
    core.accept_observation(observation(1, 0))
    assert len(core.state.internal_state['l0_state']['operative_test_only']['edges']) == 1
    core.accept_observation(observation(2, 1))
    state = core.state.to_dict()
    graph = state['internal_state']['l0_state']['operative_test_only']
    assert len(graph['edges']) == 2
    return state, graph['edges'][1]


def summary(record):
    local = record['after']['l0_state']
    run = local['content_execution']
    return {'native': local['native_operand_execution']['admitted_native_units'],
            'products': {r: local[CONTENT]['nodes'][r] for r in run['constructed']},
            'inputs': run['input_atoms']}


def test_nbo_actual_core_s1_ablation_reinsertion_and_typed_fields(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        checkpoint, s1 = setup(c)
        raw = observation(3, 2)
        normal = capture(c, raw)
        def screen(state):
            state['l0_state']['operative_test_only']['edges'].remove(s1)
            return state
        screened = capture(c, raw, screen)
        restored = capture(c, raw)
        a, b = summary(normal), summary(screened)
        assert a['native'] and not b['native']
        assert a['products'] != b['products']
        assert summary(restored) == a
        assert c.state.to_dict() == checkpoint
        assert normal['partial']['processing']['expected_outcomes'] != screened['partial']['processing']['expected_outcomes']
        assert set(a['products']) <= set(normal['partial']['processing']['expected_outcomes'])
        units = normal['after']['units']
        nodes = [units[r]['pattern'] for r in a['native']]
        assert {n['code'] for n in nodes if n['type'] == 'NativePort'} == {0, 13, 16}
        assert {n['type'] for n in nodes} == {'NativePort', 'ParameterSlot', 'ParameterDomain', 'ObservedValue', 'ObservedReference'}
        assert {n['name'] for n in nodes if n['type'] == 'ParameterSlot'} == {'slot', 'object_ref'}
        assert {n['schema']['type'] for n in nodes if n['type'] == 'ParameterDomain'} == {'integer', 'string'}
        pool = normal['after']['l0_state'][CONTENT]['nodes']
        assert {pool[r]['unit'] for r in a['inputs']} >= set(a['native'])
        assert {pool[r]['left'] for r in a['products']} == set(a['inputs']) | set(normal['after']['l0_state']['content_execution']['reused_content'])
    finally:
        c.shutdown()


@pytest.mark.parametrize('history', [True, False])
def test_nbo_process_restart_authoritative_restore_and_generic_reuse(tmp_path, history):
    db = tmp_path / 'same-a.db'
    results = []
    for phase in ('create', 'resume'):
        cmd = [sys.executable, '-m', 'experimental.native_body_operands.runner', phase, str(db)]
        if not history:
            cmd.append('--history-off')
        p = subprocess.run(cmd, capture_output=True, encoding='utf-8',
            env={**os.environ, 'PYTHONUTF8': '1'}, timeout=40)
        assert p.returncode == 0, p.stderr
        results.append(json.loads(p.stdout))
    first, second = results
    assert first['pid'] != second['pid'] != os.getpid()
    assert first['lease_released'] and second['lease_released']
    assert first['shutdown']['individual_id'] == second['start']['individual_id']
    assert second['start']['state_version'] == first['shutdown']['state_version'] + 1
    for field in (KEY, CONTENT):
        assert first['shutdown']['internal_state']['l0_state'][field] == second['start']['internal_state']['l0_state'][field]
    old = first['records'][-1]['after']['internal_state']
    final = second['records'][-1]['after']['internal_state']
    typed = set(old['l0_state']['native_operand_execution']['admitted_native_units'])
    atoms = {identity({'type': 'UnitRef', 'unit': k}) for k in typed}
    products = {r for r in old['l0_state']['content_execution']['constructed']
                if old['l0_state'][CONTENT]['nodes'][r]['left'] in atoms}
    reused = set(final['l0_state']['content_execution']['reused_content'])
    assert products and products <= reused
    assert any(final['l0_state'][CONTENT]['nodes'][r]['left'] in products
               for r in final['l0_state']['content_execution']['constructed'])
    with sqlite3.connect(db) as con:
        saved = json.loads(con.execute('SELECT snapshot FROM current_state').fetchone()[0])
        assert saved == second['shutdown']
        assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        if not history:
            assert con.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0


@pytest.mark.parametrize('control', ['remove', 'unify', 'distractor', 'order'])
def test_nbo_provenance_order_distractor_neutrality(tmp_path, control):
    c = create(tmp_path / 'a.db')
    try:
        setup(c)
        baseline = capture(c, observation(3, 2))
        def transform(state):
            graph = state['l0_state']['operative_test_only']
            if control == 'remove':
                graph['evidence'] = {}
                state['l0_state'][KEY]['evidence'] = {k: {} for k in state['l0_state'][KEY]['evidence']}
            elif control == 'unify':
                graph['evidence'] = {k: {'provenance': 'ORIGIN_SUPPLIED'} for k in graph['evidence']}
            elif control == 'distractor':
                row = deepcopy(next(iter(state['relations'].values())))
                row['relation_id'] = 'disconnected'
                state['relations']['disconnected'] = row
            else:
                state['units'] = dict(reversed(list(state['units'].items())))
                graph['edges'].reverse()
            return state
        assert summary(capture(c, observation(3, 2), transform)) == summary(baseline)
    finally:
        c.shutdown()


def test_nbo_arbitrary_origin_names_same_ordinary_constructor(tmp_path):
    outputs = []
    for i, names in enumerate([('root', 'leaf'), ('unrelated:99', 'unrelated:42')]):
        c = create(tmp_path / f'{i}.db', origin=initial(names=names)[0])
        try:
            setup(c)
            outputs.append(summary(capture(c, observation(3, 2))))
        finally:
            c.shutdown()
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize('broken', ['reference', 'slot', 'incidence', 'version', 'domain'])
def test_nbo_invalid_structure_refs_reject_without_commit(tmp_path, broken):
    c = create(tmp_path / 'a.db')
    try:
        before, _ = setup(c)
        def transform(state):
            local = state['l0_state'][KEY]
            if broken == 'version':
                local['version'] = 'wrong'
            elif broken == 'incidence':
                local['incidence'][next(iter(local['incidence']))] = []
            else:
                kind = {'reference': 'ObservedReference', 'slot': 'ParameterSlot', 'domain': 'ParameterDomain'}[broken]
                key = next(k for k, v in state['units'].items()
                           if isinstance(v['pattern'], dict) and v['pattern'].get('type') == kind)
                del state['units'][key]
            return state
        with pytest.raises(ValueError):
            capture(c, observation(3, 2), transform)
        assert c.state.to_dict() == before
    finally:
        c.shutdown()


def test_nbo_capacity_rejects_whole_batch_not_partial(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        before, _ = setup(c)
        def full(state):
            while len(state['units']) + len(state['l0_state'][CONTENT]['nodes']) < c._engine.caps.units:
                k = 'extra-' + str(len(state['units']))
                state['units'][k] = {'unit_id': k, 'pattern': []}
            return state
        with pytest.raises(ContentCapacityError):
            capture(c, observation(3, 2), full)
        assert c.state.to_dict() == before
    finally:
        c.shutdown()


@pytest.mark.parametrize('bad', ['schema', 'code'])
def test_nbo_bad_sensor_declaration_is_not_repaired(tmp_path, bad):
    c = create(tmp_path / 'a.db')
    try:
        before = c.state.to_dict()
        raw = observation(1, 0)
        if bad == 'schema':
            raw['actionSpace'][1]['parameter_schema']['properties']['slot']['maximum'] = 999
        else:
            raw['actionSpace'][0]['code'] = 999
        with pytest.raises(ValueError):
            c.accept_observation(raw)
        assert c.state.to_dict() == before
    finally:
        c.shutdown()


def test_nbo_absent_observed_ref_does_not_invent_one(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        c.accept_observation(observation(1, 0, with_reference=False))
        assert not any(isinstance(v['pattern'], dict) and v['pattern'].get('type') == 'ObservedReference'
                       for v in c.state.internal_state['units'].values())
    finally:
        c.shutdown()


def test_nbo_sampler_binder_body_tripwires(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            setup(c)
            c.accept_observation(observation(3, 2))
        with pytest.raises(RuntimeError):
            c.execute_discrete_action()
        with pytest.raises(RuntimeError):
            c.execute_action('move')
    finally:
        c.shutdown()


def test_nbo_default_and_old_core_cannot_take_over(tmp_path):
    db = tmp_path / 'a.db'
    c = create(db)
    setup(c)
    c.shutdown()
    before = db.read_bytes()
    with pytest.raises(ValueError):
        ACore(db, FakeBridge())
    with pytest.raises(ValueError):
        ContentCore(db, FakeBridge(), config=ContentConfig(str(db)))
    with pytest.raises(ValueError):
        NativeCore(db, FakeBridge(), config=NativeConfig(str(db), version='wrong'))
    with pytest.raises(ValueError):
        NativeCore(db, FakeBridge(), config=NativeConfig(str(tmp_path / 'other.db')))
    assert db.read_bytes() == before
    reopened = reopen(db)
    reopened.shutdown()


def test_nbo_origin_injection_and_old_database_conversion_rejected(tmp_path):
    origin = initial()[0]
    origin['units']['injected'] = {'unit_id': 'injected', 'operand_kind': 'NATIVE_SENSOR',
                                  'pattern': {'type': 'NativePort', 'code': 0}}
    db = tmp_path / 'a.db'
    with pytest.raises(ValueError):
        create(db, origin=origin)
    assert not db.exists()
    from experimental.operative_content.runner import create as old_create
    old = old_create(db)
    old.shutdown()
    before = db.read_bytes()
    with pytest.raises(ValueError):
        reopen(db)
    assert db.read_bytes() == before
