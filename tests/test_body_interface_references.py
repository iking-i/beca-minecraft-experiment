from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from individual.core import ACore
from individual.internal_state import InternalState
from individual.formal_l0 import digest
from individual.action_space import DEFINITIONS
from experimental.operative_content.engine import ContentCapacityError, identity
from experimental.body_interface_references.references import KEY, body_ref, resolve, validate_catalog
from experimental.body_interface_references.engine import validate, evaluate, connection, value_ref, unit_ref
from experimental.body_interface_references.runner import create, setup, sample, supplied_receipt, binding_values
from experimental.body_interface_references.channel import ReferenceCore, ReferenceConfig
from experimental.formall0_continuous.runner import FakeBridge


@pytest.fixture
def core(tmp_path):
    c = create(tmp_path/'reference.db')
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            setup(c)
            yield c
    finally:
        c.shutdown('TEST_ONLY_reference_test_close')


def advance_copy(core, edit=None):
    current = deepcopy(core.state.internal_state)
    if edit:
        edit(current)
    frame = core._encoder.encode(sample(4, 1), core.state.environment_sequence + 1, core._body_epoch)
    return core._engine.advance(current, frame, core.state.state_version + 1, [])


def test_complete_catalog_and_all_exact_addresses(core):
    internal = InternalState.from_dict(core.state.internal_state)
    pool = validate(internal)
    assert len(pool['catalog']['declarations']) == len(internal.body_capabilities['actions']) == 47
    assert len(internal.units) == 10 and len(pool['nodes']) == 10
    assert not any(isinstance(u['pattern'], dict) and u['pattern'].get('type') in
                   ('NativePort', 'ParameterSlot', 'ParameterDomain') for u in internal.units.values())
    for code, d in DEFINITIONS.items():
        assert resolve(internal, body_ref(pool['catalog'], 'port', code))['code'] == code
        for name, schema in d['parameters'].items():
            slot = resolve(internal, body_ref(pool['catalog'], 'slot', code, name))
            assert resolve(internal, slot['domain'])['schema'] == schema
            assert resolve(internal, slot['port'])['code'] == code


def test_normal_operands_and_later_saved_content_reuse(core):
    before = deepcopy(core.state.internal_state)
    pool = before['l0_state'][KEY]
    assert {n['kind'] for n in pool['nodes'].values() if n['type'] == 'BodyRef'} == {'port', 'slot', 'domain'}
    internal, _, journal = advance_copy(core)
    execution = internal.l0_state['body_reference_execution']
    assert execution['reused_content']
    assert all(ref in pool['nodes'] for ref in execution['reused_content'])
    partial = next(p for kind, p in journal if kind == 'RECURSIVE_PARTIAL_OUTPUT')
    assert set(execution['constructed']) <= set(partial['processing']['expected_outcomes'])
    nested = [ref for ref in execution['constructed'] if
              internal.l0_state[KEY]['nodes'][ref]['left'] in execution['reused_content']]
    assert nested and evaluate(internal, nested[0])['left']['type'] == 'PairValue'
    assert core.state.internal_state == before


def test_edge_only_ablation_and_restore_changes_actual_construction(core):
    state = core.state.internal_state
    pool = state['l0_state'][KEY]
    slot = body_ref(pool['catalog'], 'slot', 16, 'slot')
    edge = digest(connection(slot, value_ref(1)))
    assert pool['evidence'][edge]['supports']['kind'] == 'EXACT_ENDPOINT_COMPOSITION'
    def remove(s):
        del s['l0_state'][KEY]['edges'][edge]
    rows = [advance_copy(core), advance_copy(core, remove), advance_copy(core)]
    sets = [set(r[0].l0_state['body_reference_execution']['constructed']) for r in rows]
    assert sets[0] == sets[2] and sets[0] != sets[1]
    assert [binding_values(r[0], executed_only=True) for r in rows] == [[0, 1], [0], [0, 1]]
    assert edge in core.state.internal_state['l0_state'][KEY]['edges']


@pytest.mark.parametrize('bad', ['code', 'slot', 'domain', 'catalog', 'version', 'namespace', 'epoch', 'bool_code', 'extra'])
def test_invalid_or_foreign_reference_rejected(core, bad):
    internal = InternalState.from_dict(core.state.internal_state)
    ref = body_ref(internal.l0_state[KEY]['catalog'], 'slot', 16, 'slot')
    if bad == 'code': ref['code'] = 999
    elif bad == 'slot': ref['slot'] = 'invented'
    elif bad == 'domain': ref.update(kind='domain', slot='yaw_delta')
    elif bad == 'catalog': ref['catalog_id'] = 'foreign'
    elif bad == 'version': ref['catalog_version'] = 999
    elif bad == 'namespace': ref['namespace'] = 'foreign'
    elif bad == 'epoch': ref['body_epoch'] += 1
    elif bad == 'bool_code': ref['code'] = True
    else: ref['value'] = 0
    with pytest.raises(ValueError): resolve(internal, ref)


def test_forged_domain_and_content_identity_rejected(core):
    internal = InternalState.from_dict(core.state.internal_state)
    catalog = deepcopy(internal.l0_state[KEY]['catalog'])
    entry = next(e for e in catalog['declarations'] if e['code'] == 16)
    entry['parameter_schema']['properties']['slot']['maximum'] = 1000
    with pytest.raises(ValueError): validate_catalog(catalog)
    node = next(iter(internal.l0_state[KEY]['nodes'].values()))
    node['fake'] = True
    with pytest.raises(ValueError): validate(internal)


def test_current_scope_change_does_not_silently_rebind(core):
    before = core.state.to_dict()
    raw = sample(4, 1)
    raw['encoding']['protocol_version'] = 'foreign-namespace'
    with pytest.raises(ValueError): core.accept_observation(raw)
    assert core.state.to_dict() == before
    assert core._store.latest_state().to_dict() == before


def test_invalid_receipt_and_domain_reject_atomically(tmp_path):
    for index, change in enumerate(('wrong_port', 'wrong_type', 'out_of_range')):
        c = create(tmp_path/f'bad-{index}.db')
        try:
            c.accept_observation(sample(1, 0))
            raw = sample(2, 10 if change == 'out_of_range' else 1)
            receipt = supplied_receipt(c, raw, value=10 if change == 'out_of_range' else 0)
            if change == 'wrong_port': receipt['code'] = 8
            if change == 'wrong_type': receipt['assignments'][0]['operand_ref'] = receipt['assignments'][0]['slot_ref']
            raw['typedExecutionReceipts'] = [receipt]
            before = c.state.to_dict()
            with pytest.raises(ValueError): c.accept_observation(raw)
            assert c.state.to_dict() == before == c._store.latest_state().to_dict()
        finally:
            c.shutdown()


def test_shared_64_capacity_counts_real_refs_pairs_and_units(core):
    internal = InternalState.from_dict(core.state.internal_state)
    pool = validate(internal)
    ref = unit_ref('U-origin-0')
    atom = identity(ref)
    pool['nodes'][atom] = ref
    pool['node_evidence'][atom] = {}
    last = atom
    while len(internal.units) + len(pool['nodes']) < 64:
        node = {'type': 'Pair', 'left': last, 'right': atom}
        last = identity(node)
        pool['nodes'][last] = node
        pool['node_evidence'][last] = {}
    validate(internal)
    node = {'type': 'Pair', 'left': last, 'right': atom}
    pool['nodes'][identity(node)] = node
    pool['node_evidence'][identity(node)] = {}
    with pytest.raises(ContentCapacityError): validate(internal)
    assert core._engine.caps.units == 64


def test_full_observed_batch_overflow_does_not_truncate(core):
    raw = sample(4, 1)
    raw['nearbyEntities'] = [{'id': i, 'type_id': 1, 'position': {'x': 100+i, 'y': 64, 'z': 0},
                              'entity_ref': f'opaque-{i}'} for i in range(70)]
    before = core.state.to_dict()
    with pytest.raises(ContentCapacityError): core.accept_observation(raw)
    assert core.state.to_dict() == before == core._store.latest_state().to_dict()


def test_ordinary_construction_batch_overflow_rejects(core):
    def pad(s):
        pool = s['l0_state'][KEY]
        atom = identity(unit_ref('U-origin-0'))
        pool['nodes'][atom] = unit_ref('U-origin-0')
        pool['node_evidence'][atom] = {}
        last = atom
        while len(s['units']) + len(pool['nodes']) < 60:
            node = {'type': 'Pair', 'left': last, 'right': atom}
            last = identity(node); pool['nodes'][last] = node; pool['node_evidence'][last] = {}
    before = core.state.to_dict()
    with pytest.raises(ContentCapacityError, match='Pair batch'): advance_copy(core, pad)
    assert core.state.to_dict() == before


def test_relation_capacity_is_not_bypassed(core):
    internal = InternalState.from_dict(core.state.internal_state)
    pool = validate(internal)
    for source in (0, 1, 2):
        for target in DEFINITIONS:
            edge = connection(body_ref(pool['catalog'], 'port', source), body_ref(pool['catalog'], 'port', target))
            pool['edges'][digest(edge)] = edge
    with pytest.raises(ContentCapacityError, match='relation capacity'): validate(internal)


def test_invalid_first_observation_receipt_not_silently_accepted(tmp_path):
    c = create(tmp_path/'first.db')
    try:
        raw = sample(1, 0)
        raw['typedExecutionReceipts'] = [supplied_receipt(c, raw)]
        raw['typedExecutionReceipts'][0]['assignments'][0]['slot_ref']['code'] = 999
        before = c.state.to_dict()
        with pytest.raises(ValueError): c.accept_observation(raw)
        assert c.state.to_dict() == before == c._store.latest_state().to_dict()
    finally:
        c.shutdown()


def test_stale_observation_reference_and_missing_unit_reject(core):
    internal = InternalState.from_dict(core.state.internal_state)
    observed = next((r for r, u in internal.units.items() if isinstance(u['pattern'], dict)
                     and u['pattern'].get('type') == 'ObservedReference'))
    internal.l0_state[KEY]['current_source']['references'] = []
    with pytest.raises(ValueError, match='Stale'): resolve(internal, unit_ref(observed))
    with pytest.raises(ValueError): resolve(internal, unit_ref('missing'))


@pytest.mark.parametrize('edit', ['provenance', 'order', 'unrelated'])
def test_no_hidden_selector_or_provenance_privilege(core, edit):
    def change(s):
        pool = s['l0_state'][KEY]
        if edit == 'provenance': pool['evidence'] = {}
        elif edit == 'order': pool['edges'] = dict(reversed(list(pool['edges'].items())))
        else: s['units']['unrelated'] = {'unit_id': 'unrelated', 'pattern': []}
    row = advance_copy(core, change)[0]
    assert binding_values(row) == [0, 1]
    baseline = advance_copy(core)[0]
    assert row.l0_state['body_reference_execution']['constructed'] == baseline.l0_state['body_reference_execution']['constructed']


def test_different_parameter_and_reference_shapes(tmp_path):
    c = create(tmp_path/'shapes.db')
    try:
        c.accept_observation(sample(1, 0))
        raw = sample(2, 1)
        raw['typedExecutionReceipts'] = [supplied_receipt(c, raw, code=8, name='yaw_delta')]
        c.accept_observation(raw); c.accept_observation(sample(3, 1))
        pool = validate(InternalState.from_dict(c.state.internal_state))
        assert {n['code'] for n in pool['nodes'].values() if n['type'] == 'BodyRef'} == {8}
        assert len(pool['catalog']['declarations']) == 47
        assert binding_values(InternalState.from_dict(c.state.internal_state)) == [0, 1]
    finally:
        c.shutdown()


def test_separate_process_authoritative_restore_and_reuse(tmp_path):
    db = tmp_path/'restart.db'
    root = Path(__file__).resolve().parents[1]
    results = []
    for phase in ('create', 'resume'):
        done = subprocess.run([sys.executable, '-X', 'utf8', '-m',
            'experimental.body_interface_references.runner', phase, str(db)], cwd=root,
            capture_output=True, text=True, encoding='utf-8', check=True)
        results.append(json.loads(done.stdout))
    a, b = results
    assert a['pid'] != b['pid']
    assert a['end']['individual_id'] == b['start']['individual_id'] == b['end']['individual_id']
    assert a['end']['internal_state'][ 'l0_state'][KEY] == b['start']['internal_state']['l0_state'][KEY]
    assert b['end']['state_version'] > a['end']['state_version']
    saved = a['end']['internal_state']['l0_state'][KEY]['nodes']
    reused = b['end']['internal_state']['l0_state']['body_reference_execution']['reused_content']
    assert reused and all(ref in saved for ref in reused)
    with pytest.raises(ValueError): ACore(db, FakeBridge())
    with pytest.raises(ValueError): ReferenceCore(db, FakeBridge(), config=ReferenceConfig(str(db),version='bad'))


def test_no_body_dispatch_or_fallback(core):
    assert binding_values(InternalState.from_dict(core.state.internal_state)) == [0, 1]
    with patch.object(core._bridge, 'call', side_effect=AssertionError('must not perform')):
        for method in (core.execute_action, core.execute_discrete_action):
            with pytest.raises(RuntimeError): method()


def test_incomplete_interface_and_provisioning_mismatch_reject(core):
    from experimental.body_interface_references.channel import validate_state
    before = core.state.to_dict()
    raw = sample(4, 1)
    raw['actionSpace'].pop()
    with pytest.raises(ValueError, match='Complete'): core.accept_observation(raw)
    assert core.state.to_dict() == before
    corrupt = deepcopy(before)
    corrupt['internal_state']['body_capabilities']['actions'].pop()
    with pytest.raises(ValueError, match='provisioned'): validate_state(corrupt, core._reference_config)


def test_native_origin_answer_injection_rejected_before_db_write(tmp_path):
    from experimental.formall0_operative.validation import initial
    origin = initial()[0]
    origin['units']['U-origin-0']['pattern'] = {'type': 'NativePort', 'catalog_version': 2, 'code': 16}
    db = tmp_path/'forbidden-origin.db'
    with pytest.raises(ValueError, match='observed input'):
        ReferenceCore(db, FakeBridge(), initialize_lifetime=True,
                      config=ReferenceConfig(str(db), origin_state=origin))
    assert not db.exists()
