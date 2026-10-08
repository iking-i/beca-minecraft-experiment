"""History-formed exact operand edges, ordinary Core causality, no body execution."""
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
from individual.formal_l0 import digest
from experimental.formall0_continuous.runner import FakeBridge
from experimental.native_body_operands.channel import NativeCore, NativeConfig
from experimental.native_body_operands.engine import KEY as NATIVE
from experimental.operative_content.engine import KEY as CONTENT, identity, ContentCapacityError
from experimental.typed_operative_connection.channel import ConnectionCore, ConnectionConfig
from experimental.typed_operative_connection.engine import KEY, connection, value_ref
from experimental.typed_operative_connection.runner import create, reopen, setup, sample, capture


def materials(state):
    return {k: deepcopy(u['pattern']) for k, u in state['units'].items()
            if u.get('operand_kind') == 'NATIVE_SENSOR'}


def products(record):
    local = record['after']['l0_state']
    return {r: local[CONTENT]['nodes'][r] for r in local['content_execution']['constructed']}


def formed(state):
    g = state['l0_state'][KEY]
    return {r: e for r, e in g['edges'].items()
            if g['evidence'][r]['provenance'] == 'EXPERIENCE_FORMED'}


@pytest.mark.parametrize('values', [(0, 1), (20, 64)])
def test_two_real_histories_same_material_different_relation_content(tmp_path, values):
    a, b = create(tmp_path / 'a.db'), create(tmp_path / 'b.db')
    try:
        setup(a, values); setup(b, tuple(reversed(values)))
        sa, sb = a.state.internal_state, b.state.internal_state
        assert materials(sa) == materials(sb)
        ea, eb = formed(sa), formed(sb)
        assert list(ea.values()) == [connection(value_ref(values[0]), value_ref(values[1]))]
        assert list(eb.values()) == [connection(value_ref(values[1]), value_ref(values[0]))]
        # Only actual history-formed typed relations/supports vary, not input or other state.
        def replace(state):
            state['l0_state'][KEY] = deepcopy(sb['l0_state'][KEY])
            return state
        pa = capture(a, sample(3, values[1]))
        pb = capture(a, sample(3, values[1]), replace)
        expected = deepcopy(pa['before']); expected['l0_state'][KEY] = deepcopy(sb['l0_state'][KEY])
        assert pb['before'] == expected
        assert pa['after']['l0_state']['native_operand_execution'] == pb['after']['l0_state']['native_operand_execution']
        assert products(pa) != products(pb)
        assert pa['partial']['processing']['expected_outcomes'] != pb['partial']['processing']['expected_outcomes']
        for p in (pa, pb):
            assert set(products(p)) <= set(p['partial']['processing']['expected_outcomes'])
            assert len(p['after']['l0_state']['typed_connection_execution']['connections']) == 2
    finally:
        a.shutdown(); b.shutdown()


def test_s1_only_ablation_reinsert_and_no_early_use(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        records = setup(c)
        state = c.state.to_dict()
        s1, = formed(state['internal_state'])
        formation = records[-1]['after']['internal_state']['l0_state']
        assert s1 not in formation['typed_connection_execution']['connections']
        support = formation[KEY]['evidence'][s1]['supports']
        assert support['integration_id'] == records[-1]['after']['internal_state']['latest_integration']['integration_id']
        assert support['change_facts'] == records[-1]['after']['internal_state']['detected_changes']['changes']
        normal = capture(c, sample(3, 1))
        def screen(s):
            del s['l0_state'][KEY]['edges'][s1]
            return s
        ablated = capture(c, sample(3, 1), screen)
        restored = capture(c, sample(3, 1))
        assert len(products(normal)) == 2 and len(products(ablated)) == 1
        assert products(restored) == products(normal)
        new_products = set(products(normal)) - set(products(ablated))
        product, = new_products
        assert normal['after']['l0_state'][CONTENT]['evidence'][product]['direct_supports'] == {
            'connection_refs': [s1], 'unit_refs': [value_ref(0), value_ref(1)]}
        expected = deepcopy(normal['before']); del expected['l0_state'][KEY]['edges'][s1]
        assert ablated['before'] == expected
        assert c.state.to_dict() == state
    finally:
        c.shutdown()


@pytest.mark.parametrize('history', [True, False])
def test_actual_process_restart_same_authoritative_a_and_saved_products(tmp_path, history):
    db = tmp_path / 'same.db'
    records = []
    for phase in ('create', 'resume'):
        cmd = [sys.executable, '-m', 'experimental.typed_operative_connection.runner', phase, str(db)]
        if not history: cmd.append('--history-off')
        r = subprocess.run(cmd, env={**os.environ, 'PYTHONUTF8': '1'},
                           capture_output=True, encoding='utf-8', timeout=40)
        assert r.returncode == 0, r.stderr
        records.append(json.loads(r.stdout))
    a, b = records
    assert a['pid'] != b['pid'] != os.getpid()
    assert a['lease_released'] and b['lease_released']
    assert a['shutdown']['individual_id'] == b['start']['individual_id']
    assert b['start']['state_version'] == a['shutdown']['state_version'] + 1
    for key in (KEY, CONTENT, NATIVE):
        assert a['shutdown']['internal_state']['l0_state'][key] == b['start']['internal_state']['l0_state'][key]
    final = b['records'][-1]['after']['internal_state']['l0_state']
    old = a['records'][-1]['after']['internal_state']['l0_state']['content_execution']['constructed']
    assert set(old) <= set(final['content_execution']['reused_content'])
    assert not final['content_execution']['new_nodes']
    assert a['shutdown']['internal_state']['l0_state'][KEY] == final[KEY]
    with sqlite3.connect(db) as con:
        assert json.loads(con.execute('SELECT snapshot FROM current_state').fetchone()[0]) == b['shutdown']
        if not history: assert con.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0


@pytest.mark.parametrize('change', ['provenance', 'unify', 'order', 'distractor'])
def test_same_interpreter_origin_formed_and_audit_neutral(tmp_path, change):
    c = create(tmp_path / 'a.db')
    try:
        setup(c)
        baseline = capture(c, sample(3, 1))
        def edit(s):
            g = s['l0_state'][KEY]
            if change == 'provenance': g['evidence'] = {}
            elif change == 'unify': g['evidence'] = {k: {'provenance': 'ORIGIN_SUPPLIED'} for k in g['edges']}
            elif change == 'order': g['edges'] = dict(reversed(list(g['edges'].items())))
            else:
                edge = connection('disconnected-left', 'disconnected-right')
                for u in (edge['source'], edge['target']): s['units'][u] = {'unit_id': u, 'pattern': []}
                g['edges'][digest(edge)] = edge
            return s
        assert products(capture(c, sample(3, 1), edit)) == products(baseline)
    finally: c.shutdown()


def test_renamed_origin_refs_not_special_interpreter(tmp_path):
    from experimental.formall0_operative.validation import initial
    origin = initial()[0]
    mapping = {'U-origin-0': 'arbitrary:left', 'U-origin-1': 'arbitrary:right'}
    origin['units'] = {mapping[k]: {**u, 'unit_id': mapping[k]} for k, u in origin['units'].items()}
    for row in origin['relations'].values():
        row['antecedent'] = mapping[row['antecedent']]
        row['outcomes'] = {mapping[k]: {**u, 'unit_id': mapping[k]} for k,u in row['outcomes'].items()}
    c = create(tmp_path / 'a.db', origin=origin,
               origin_edges=(connection('arbitrary:left', 'arbitrary:right'),))
    try:
        setup(c)
        r = capture(c, sample(3, 1))
        expected = connection(value_ref(0), value_ref(1))
        assert expected in formed(c.state.internal_state).values()
        assert digest(expected) in r['after']['l0_state']['typed_connection_execution']['connections']
    finally: c.shutdown()


def test_two_changed_channels_all_actual_transitions_no_product_pairing(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        c.accept_observation(sample(1, 0))
        raw = sample(2, 1)
        raw['position']['z'] = 20
        c.accept_observation(raw)
        actual = set(tuple((e['source'], e['target'])) for e in formed(c.state.internal_state).values())
        # Self z also changes the already encoded entity-relative z: retain it too.
        assert actual == {(value_ref(0), value_ref(1)), (value_ref(0), value_ref(20)),
                          (value_ref(0), value_ref(-20))}
        assert (value_ref(1), value_ref(20)) not in actual
        raw3 = sample(3, 1); raw3['position']['z'] = 20
        p = capture(c, raw3)
        assert len(products(p)) == 4
    finally: c.shutdown()


@pytest.mark.parametrize('control', ['unchanged', 'gap'])
def test_no_observed_transition_no_formed_connection(tmp_path, control):
    c = create(tmp_path / 'a.db')
    try:
        c.accept_observation(sample(1, 0))
        raw = sample(2, 0 if control == 'unchanged' else 1)
        if control == 'gap': raw['encoding'] = {'protocol_version': 'different-namespace'}
        c.accept_observation(raw)
        assert not formed(c.state.internal_state)
    finally: c.shutdown()


@pytest.mark.parametrize('bad', ['dangling', 'identity', 'version', 'capacity', 'content_capacity'])
def test_invalid_connection_whole_transition_rejects_without_commit(tmp_path, bad):
    c = create(tmp_path / 'a.db')
    try:
        setup(c); before = c.state.to_dict()
        def edit(s):
            g = s['l0_state'][KEY]
            if bad == 'version': g['version'] = 'wrong'
            elif bad == 'identity': g['edges']['wrong-id'] = next(iter(g['edges'].values()))
            elif bad == 'dangling':
                e = connection(value_ref(0), 'absent')
                g['edges'][digest(e)] = e
            elif bad == 'capacity':
                while len(s['relations']) + len(s['l0_state']['operative_test_only']['edges']) + len(g['edges']) < c._engine.caps.relations:
                    key = 'unused-relation-' + str(len(s['relations']))
                    s['relations'][key] = {'relation_id': key, 'outcomes': {}}
            else:
                while len(s['units']) + len(s['l0_state'][CONTENT]['nodes']) < c._engine.caps.units:
                    key = 'unused-unit-' + str(len(s['units']))
                    s['units'][key] = {'unit_id': key, 'pattern': []}
            return s
        raw = sample(3, 0) if bad == 'capacity' else sample(3, 1)
        with pytest.raises(ValueError): capture(c, raw, edit)
        assert c.state.to_dict() == before
    finally: c.shutdown()


def test_non_admitted_new_scalar_endpoint_rejects_no_invention(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        setup(c)
        # Material 2 is not admitted under the frozen first-observed increased pattern.
        before = c.state.to_dict()
        with pytest.raises(ValueError, match='endpoint is not admitted'):
            c.accept_observation(sample(3, 2))
        assert c.state.to_dict() == before
    finally: c.shutdown()


def test_foreign_default_native_version_database_and_origin_refusal(tmp_path):
    db = tmp_path / 'a.db'
    c = create(db); setup(c); c.shutdown()
    before = db.read_bytes()
    for call in (lambda: ACore(db, FakeBridge()),
                 lambda: NativeCore(db, FakeBridge(), config=NativeConfig(str(db))),
                 lambda: ConnectionCore(db, FakeBridge(), config=ConnectionConfig(str(db), version='wrong')),
                 lambda: ConnectionCore(db, FakeBridge(), config=ConnectionConfig(str(tmp_path / 'other.db')))):
        with pytest.raises(ValueError): call()
    assert db.read_bytes() == before
    reopened = reopen(db); reopened.shutdown()
    with pytest.raises(ValueError):
        create(tmp_path / 'invalid.db', origin_edges=(connection('missing', 'U-origin-1'),))
    assert not (tmp_path / 'invalid.db').exists()


def test_sampler_binder_body_tripwires(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            setup(c); c.accept_observation(sample(3, 1))
        with pytest.raises(RuntimeError): c.execute_discrete_action()
        with pytest.raises(RuntimeError): c.execute_action('move')
    finally: c.shutdown()


def test_absent_sensor_successor_does_not_fill_value(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        raw = sample(1, 0); raw['time'] = {'timeOfDay': 5}
        c.accept_observation(raw)
        c.accept_observation(sample(2, 0))
        assert not formed(c.state.internal_state)
    finally: c.shutdown()


def test_no_missing_database_restart_or_old_mode_conversion(tmp_path):
    db = tmp_path / 'absent.db'
    with pytest.raises(ValueError): reopen(db)
    assert not db.exists()
    from experimental.native_body_operands.runner import create as old_create
    old = old_create(db); old.shutdown()
    data = db.read_bytes()
    with pytest.raises(ValueError): reopen(db)
    assert db.read_bytes() == data


def test_canonical_transition_cannot_erase_persisted_connection(tmp_path):
    c = create(tmp_path / 'a.db')
    try:
        setup(c); before = c.state.to_dict()
        edited = deepcopy(before['internal_state'])
        ref, = formed(edited)
        del edited['l0_state'][KEY]['edges'][ref]
        with pytest.raises(ValueError, match='erase committed'):
            c._transition('TEST_ONLY_INVALID_ERASURE', {}, internal_state=edited)
        assert c.state.to_dict() == before
    finally: c.shutdown()
