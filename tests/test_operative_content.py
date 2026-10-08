"""Preregistered construction and ordinary Core causal controls; no Minecraft."""
from copy import deepcopy
from dataclasses import replace
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
from experimental.formall0_continuous.runner import FakeBridge, observation
from experimental.formall0_continuous.channel import TestOnlyOperativeConfig
from experimental.formall0_operative.validation import initial
from experimental.operative_content.channel import ContentConfig, ContentCore
from experimental.operative_content.engine import (KEY, VERSION, ContentEngine,
    ContentCapacityError, validate_content, evaluate, identity)
from experimental.operative_content.runner import create, reopen, capture


def child(database, phase, history=True):
    command = [sys.executable, '-m', 'experimental.operative_content.runner', phase, str(database)]
    if not history:
        command.append('--history-off')
    completed = subprocess.run(command, capture_output=True, encoding='utf-8',
        env={**os.environ, 'PYTHONUTF8': '1'}, timeout=40)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def snapshot(database):
    with sqlite3.connect(database) as db:
        return json.loads(db.execute('SELECT snapshot FROM current_state').fetchone()[0])


def setup(core, values=(0, 1)):
    for seq, value in enumerate(values, 1):
        core.accept_observation(observation(seq, value))
    before = core.state.to_dict()
    edges = before['internal_state']['l0_state']['operative_test_only']['edges']
    assert len(edges) == 2
    return before, edges[1]


def execution(record):
    return record['after']['l0_state']['content_execution']


def constructed(record):
    pool = record['after']['l0_state'][KEY]['nodes']
    return {key: pool[key] for key in execution(record)['constructed']}


def mask(state, edge):
    state['l0_state']['operative_test_only']['edges'].remove(edge)
    return state


@pytest.mark.parametrize('history', [True, False])
def test_gc_real_process_persistence_reuse_and_identity(tmp_path, history):
    db = tmp_path / 'same-a.db'
    first = child(db, 'create', history)
    saved = snapshot(db)
    second = child(db, 'resume', history)
    assert first['pid'] != second['pid'] != os.getpid()
    assert first['lease_released'] and second['lease_released']
    assert saved == first['shutdown']
    assert second['start']['individual_id'] == saved['individual_id']
    assert second['start']['state_version'] == saved['state_version'] + 1
    assert saved['internal_state']['l0_state'][KEY] == second['start']['internal_state']['l0_state'][KEY]
    before_s1 = first['records'][0]['after']['internal_state']['l0_state']['operative_test_only']['edges']
    after_s1 = first['records'][1]['after']['internal_state']['l0_state']['operative_test_only']['edges']
    assert len(before_s1) == 1 and len(after_s1) == 2
    t1s = first['records'][2]['after']['internal_state']['l0_state']['content_execution']['constructed']
    used = second['records'][1]['after']['internal_state']['l0_state']['content_execution']
    assert set(t1s) & set(used['reused_content'])
    nodes = second['records'][1]['after']['internal_state']['l0_state'][KEY]['nodes']
    assert any(nodes[ref]['left'] in t1s for ref in used['constructed'])
    assert snapshot(db) == second['shutdown']
    with sqlite3.connect(db) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        if not history:
            assert conn.execute('SELECT COUNT(*) FROM states').fetchone()[0] == 0
            assert conn.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0


def test_gc_s1_only_ablation_reinsertion_and_real_operands(tmp_path):
    core = create(tmp_path / 'a.db')
    try:
        before, s1 = setup(core)
        raw = observation(3, 2)
        normal = capture(core, raw)
        ablated = capture(core, raw, lambda state: mask(state, s1))
        restored = capture(core, raw)
        assert constructed(normal) != constructed(ablated)
        assert constructed(normal) == constructed(restored)
        assert normal['partial']['processing']['expected_outcomes'] != ablated['partial']['processing']['expected_outcomes']
        assert set(execution(normal)['constructed']) <= set(normal['partial']['processing']['expected_outcomes'])
        assert core.state.to_dict() == before == snapshot(core._store.path)
        internal = InternalState.from_dict(normal['after'])
        values = [evaluate(internal, ref) for ref in execution(normal)['constructed']]
        assert all(v['type'] == 'PairValue' for v in values)
        assert any(v['right']['pattern'] for v in values)
        assert all(set(node) == {'type', 'left', 'right'} for node in constructed(normal).values())
    finally:
        core.shutdown()


@pytest.mark.parametrize('change', ['remove', 'swap', 'unify', 'distractor'])
def test_gc_provenance_and_disconnected_neutrality(tmp_path, change):
    core = create(tmp_path / 'a.db')
    try:
        setup(core)
        normal = capture(core, observation(3, 2))
        def transform(state):
            graph = state['l0_state']['operative_test_only']
            if change == 'remove':
                graph['evidence'] = {}
            elif change == 'swap':
                graph['evidence'] = dict(zip(graph['evidence'], reversed(list(graph['evidence'].values()))))
            elif change == 'unify':
                graph['evidence'] = {key: {'provenance': 'OPAQUE'} for key in graph['evidence']}
                state['l0_state'][KEY]['evidence'] = {key: {} for key in state['l0_state'][KEY]['nodes']}
            else:
                relation = deepcopy(next(iter(state['relations'].values())))
                relation['relation_id'] = 'unrelated'
                state['relations']['unrelated'] = relation
            return state
        modified = capture(core, observation(3, 2), transform)
        assert constructed(normal) == constructed(modified)
        assert normal['partial']['processing']['expected_outcomes'] == modified['partial']['processing']['expected_outcomes']
    finally:
        core.shutdown()


def test_gc_different_histories(tmp_path):
    products = []
    # The frozen pattern identity distinguishes direction, not delta magnitude.
    # Opposite directions provide genuinely different structural histories.
    for label, values in [('a', (0, 1)), ('b', (0, -1))]:
        core = create(tmp_path / (label + '.db'))
        try:
            setup(core, values)
            products.append(constructed(capture(core, observation(3, 3))))
        finally:
            core.shutdown()
    assert products[0] != products[1]


def test_gc_all_candidates_no_arbitration(tmp_path):
    core = create(tmp_path / 'a.db')
    try:
        setup(core)
        record = capture(core, observation(3, 2))
        run = execution(record)
        pool = record['after']['l0_state'][KEY]['nodes']
        assert len(run['input_atoms']) > 1
        assert {pool[ref]['left'] for ref in run['constructed']} == set(run['input_atoms']) | set(run['reused_content'])
    finally:
        core.shutdown()


def test_gc_arbitrary_identifier_renaming():
    state, _ = initial()
    internal = InternalState.from_dict(state)
    internal.l0_state[KEY] = {'version': VERSION, 'nodes': {}, 'evidence': {}}
    internal.l0_state['current_pattern'] = next(iter(internal.units))
    mapping = {key: 'renamed:' + str(i) for i, key in enumerate([*internal.units, *internal.relations])}
    def rename(value):
        if isinstance(value, str): return mapping.get(value, value)
        if isinstance(value, list): return [rename(v) for v in value]
        if isinstance(value, dict): return {mapping.get(k, k): rename(v) for k, v in value.items()}
        return value
    outputs = []
    for candidate in (internal, InternalState.from_dict(rename(internal.to_dict()))):
        engine = ContentEngine()
        engine._executing = True
        engine._read_operative_operands(candidate, candidate.l0_state['feedback']['next_relation_ref'])
        nodes = candidate.l0_state[KEY]['nodes']
        outputs.append({(nodes[node['left']]['unit'], nodes[node['right']]['unit'])
                        for node in nodes.values() if node['type'] == 'Pair'})
    assert {(mapping.get(a, a), mapping.get(b, b)) for a, b in outputs[0]} == outputs[1]


def test_gc_capacity_batch_rejects_without_commit(tmp_path):
    core = create(tmp_path / 'a.db')
    try:
        before, _ = setup(core)
        # Isolated engine budget below required batch; no canonical cap edit.
        def lower_budget(state):
            state['l0_state']['locked_caps']['units'] = 9
            return state
        with patch.object(core._engine, '_caps', replace(core._engine.caps, units=9)):
            with pytest.raises(ContentCapacityError):
                capture(core, observation(3, 2), lower_budget)
        assert core.state.to_dict() == before == snapshot(core._store.path)
    finally:
        core.shutdown()


@pytest.mark.parametrize('damage', ['version', 'type', 'reference', 'identity', 'cycle'])
def test_gc_illegal_content_rejected(tmp_path, damage):
    core = create(tmp_path / 'a.db')
    try:
        before, _ = setup(core)
        state = deepcopy(before['internal_state'])
        pool = state['l0_state'][KEY]
        if damage == 'version': pool['version'] = 'wrong'
        else:
            ref = next(iter(pool['nodes']))
            if damage == 'type': pool['nodes'][ref] = {'type': 'Action', 'code': 0}
            elif damage == 'reference':
                node = {'type': 'UnitRef', 'unit': 'missing'}
                pool['nodes'] = {identity(node): node}; pool['evidence'] = {identity(node): {}}
            elif damage == 'identity': pool['nodes'][ref]['unit'] = 'different'
            else: pool['nodes'][ref] = {'type': 'Pair', 'left': ref, 'right': ref}
        with pytest.raises(ValueError): validate_content(InternalState.from_dict(state))
        assert snapshot(core._store.path) == before
    finally:
        core.shutdown()


@pytest.mark.parametrize('mode', ['default', 'old', 'version', 'database'])
def test_gc_mode_mismatch_before_writes(tmp_path, mode):
    db = tmp_path / 'a.db'
    core = create(db)
    setup(core)
    core.shutdown()
    before = snapshot(db)
    with pytest.raises(ValueError):
        if mode == 'default': ACore(db, FakeBridge())
        elif mode == 'old': ACore(db, FakeBridge(), test_only_operative=TestOnlyOperativeConfig(str(db)))
        elif mode == 'version': ContentCore(db, FakeBridge(), config=ContentConfig(str(db), version='wrong'))
        else: ContentCore(db, FakeBridge(), config=ContentConfig(str(tmp_path / 'wrong.db')))
    assert snapshot(db) == before


def test_gc_no_preconstructed_origin_or_body_path(tmp_path):
    state, _ = initial()
    state['l0_state'][KEY] = {'version': VERSION, 'nodes': {}, 'evidence': {}}
    with pytest.raises(ValueError):
        ContentCore(tmp_path / 'bad.db', FakeBridge(), initialize_lifetime=True,
                    config=ContentConfig(str(tmp_path / 'bad.db'), origin_state=state))
    assert not (tmp_path / 'bad.db').exists()
    core = create(tmp_path / 'a.db')
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            setup(core)
            core.accept_observation(observation(3, 2))
            with pytest.raises(RuntimeError): core.execute_discrete_action()
            with pytest.raises(RuntimeError): core.execute_action({})
    finally:
        core.shutdown()


def test_gc_validation_read_is_nonmutating(tmp_path):
    core = create(tmp_path / 'a.db')
    try:
        before, _ = setup(core)
        internal = InternalState.from_dict(before['internal_state'])
        core._engine._read_operative_operands(internal, internal.l0_state['feedback']['next_relation_ref'])
        assert internal.to_dict() == before['internal_state']
    finally:
        core.shutdown()


def test_gc_storage_order_neutrality(tmp_path):
    core = create(tmp_path / 'a.db')
    try:
        setup(core)
        normal = capture(core, observation(3, 2))
        def reorder(state):
            state['relations'] = dict(reversed(list(state['relations'].items())))
            state['units'] = dict(reversed(list(state['units'].items())))
            pool = state['l0_state'][KEY]
            pool['nodes'] = dict(reversed(list(pool['nodes'].items())))
            state['l0_state']['operative_test_only']['edges'].reverse()
            return state
        assert constructed(normal) == constructed(capture(core, observation(3, 2), reorder))
    finally:
        core.shutdown()


def test_gc_t1_is_later_constructor_material_not_a_trace(tmp_path):
    core = create(tmp_path / 'a.db')
    try:
        setup(core)
        core.accept_observation(observation(3, 2))
        checkpoint = core.state.to_dict()
        products = checkpoint['internal_state']['l0_state']['content_execution']['constructed']
        normal = capture(core, observation(4, 3))
        assert set(products) & set(execution(normal)['reused_content'])
        def no_products(state):
            pool = state['l0_state'][KEY]
            # All Pair objects are removed in the isolated material-use control;
            # UnitRefs, operative edges and the current observation stay fixed.
            keep = {k: n for k, n in pool['nodes'].items() if n['type'] == 'UnitRef'}
            pool['nodes'] = keep
            pool['evidence'] = {k: pool['evidence'][k] for k in keep}
            return state
        ablated = capture(core, observation(4, 3), no_products)
        assert constructed(normal) != constructed(ablated)
        assert execution(ablated)['reused_content'] == []
        assert core.state.to_dict() == checkpoint
    finally:
        core.shutdown()
