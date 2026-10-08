"""Isolated real FormalL0 advances; no Core initialization/body/database run."""
import ast
from copy import deepcopy
import inspect
import json
from unittest.mock import patch

import pytest

from experimental.formall0_operative.validation import (advance, default_equivalence,
    edge_ablation, frame, initial, operands, read_has_no_audit_or_side_executor_access,
    migration_equivalence, preserved_transition_identity, run_validation, witness)
from individual.core import ACore
from experimental.formall0_operative.engine import TestOnlyFormalL0Engine as FormalL0Engine
from individual.formal_l0 import FormalLimits, digest
from individual.internal_state import InternalState


def test_focused_checks_do_not_certify_the_separate_full_regression():
    report = run_validation()
    assert report['focused_classification'] == 'PASS', report['focused_checks']
    assert list(report['focused_checks'].values()) == ['PASS'] * 10
    assert report['classification'] == 'NOT_ESTABLISHED'
    assert report['criteria']['FA_T9'] == 'NOT_ESTABLISHED'
    assert report['full_regression_required']


def test_origin_edge_changes_actual_operands():
    w = witness()
    _, ablated, _ = advance(w['engine'], edge_ablation(w['first'], w['s0']), 2, 1)
    assert 'U-origin-1' in w['formation_partial']['processing']['expected_outcomes']
    assert 'U-origin-1' not in ablated['processing']['expected_outcomes']


def test_s1_formed_from_actual_experience_and_not_executed_in_formation_round():
    w = witness()
    assert w['s1']['target'] not in w['first']['relations']
    assert w['s1'] not in w['first']['l0_state']['operative_test_only']['edges']
    assert w['s1'] not in w['formation_partial']['processing']['operative_dependencies']['dependencies']
    assert w['s1'] in w['reentry']['processing']['operative_dependencies']['dependencies']
    evidence = w['committed']['l0_state']['operative_test_only']['evidence'][digest(w['s1'])]
    assert evidence['supports']['frame_ids'] == w['formation_partial']['experience']['frame_ids']
    assert evidence['supports']['partial_id'] == w['formation_partial']['partial_id']
    assert evidence['supports']['integration_id'] == w['committed']['latest_integration']['integration_id']


def test_real_internal_state_json_reentry_identity():
    w = witness()
    restored = InternalState.from_dict(json.loads(json.dumps(w['committed']))).to_dict()
    assert restored == w['committed']
    _, p, _ = advance(w['engine'], restored, 3, 2)
    assert operands(p) == operands(w['reentry'])


def test_only_s1_removed_and_actual_comparison_changes():
    w = witness()
    ablated = edge_ablation(w['later'], w['s1'])
    reinstated = deepcopy(ablated)
    reinstated['l0_state']['operative_test_only']['edges'].insert(1, w['s1'])
    assert reinstated == w['later']
    _, p, _ = advance(w['engine'], w['later'], 4, 3)
    _, negative, _ = advance(w['engine'], ablated, 4, 3)
    assert p['processing']['outcome_previously_observed'] is True
    assert negative['processing']['outcome_previously_observed'] is None
    assert p['processing']['expected_outcomes'] != negative['processing']['expected_outcomes']


@pytest.mark.parametrize('mode', ['removed', 'unified', 'swapped', 'malformed'])
def test_audit_provenance_is_not_executable(mode):
    w = witness()
    # Reuse executes an existing edge without writing new formation audit records.
    state = deepcopy(w['later'])
    evidence = state['l0_state']['operative_test_only']['evidence']
    if mode == 'removed':
        evidence.clear()
    elif mode == 'malformed':
        state['l0_state']['operative_test_only']['evidence'] = 'not an executable object'
    else:
        for key, value in evidence.items():
            value['provenance'] = ('NEUTRAL' if mode == 'unified' else
                'INTERNALLY_FORMED' if key == digest(w['s0']) else 'ORIGIN_SUPPLIED')
    _, p, _ = advance(w['engine'], state, 4, 3)
    assert operands(p) == operands(w['reuse'])


def test_repeated_use_does_not_call_formation():
    w = witness()
    state = w['later']
    with patch.object(w['engine'], '_form_operative_dependencies', side_effect=AssertionError('No reformation')):
        for sequence in (4, 5):
            state, p, _ = advance(w['engine'], state, sequence, sequence - 1)
            assert w['s1'] in p['processing']['operative_dependencies']['dependencies']
    assert state['l0_state']['operative_test_only'] == w['later']['l0_state']['operative_test_only']


def test_disconnected_input_does_not_change_operand_path():
    w = witness()
    state = deepcopy(w['committed'])
    for name in ('unrelated:a', 'unrelated:b'):
        state['relations'][name] = {'relation_id': name, 'outcomes': {'unrelated:value': {'unit_id': 'unrelated:value'}}}
    state['l0_state']['operative_test_only']['edges'].append({'source': 'unrelated:a', 'target': 'unrelated:b'})
    _, p, _ = advance(w['engine'], state, 3, 2)
    assert operands(p) == operands(w['reentry'])


def test_no_prior_experience_means_no_formed_edge():
    state, s0 = initial()
    state, partial, journal = advance(FormalL0Engine(test_only_operative_adoption=True), state, 1, 0)
    assert partial is None and not any(k == 'EXPERIENCE_FORMED' for k, _ in journal)
    assert state['l0_state']['operative_test_only']['edges'] == [s0]


@pytest.mark.parametrize('defect', ['missing_endpoint', 'missing_entry', 'duplicate_edge', 'wrong_schema', 'missing_edges'])
def test_invalid_graph_rejected_without_fallback_or_input_mutation(defect):
    w = witness()
    state = deepcopy(w['committed'])
    graph = state['l0_state']['operative_test_only']
    if defect == 'missing_endpoint':
        del state['relations'][w['s1']['target']]
    elif defect == 'missing_entry':
        state['l0_state']['feedback']['next_relation_ref'] = 'absent'
    elif defect == 'duplicate_edge':
        graph['edges'].append(deepcopy(w['s1']))
    elif defect == 'wrong_schema':
        graph['schema'] = 'invalid'
    else:
        del graph['edges']
    original = deepcopy(state)
    with pytest.raises(ValueError):
        advance(w['engine'], state, 3, 2)
    assert state == original


def test_all_eligible_terminals_form_no_first_selector():
    state, s0 = initial()
    other = 'opaque:other'
    state['relations'][other] = deepcopy(state['relations'][s0['target']])
    state['relations'][other]['relation_id'] = other
    state['l0_state']['operative_test_only']['edges'].append({'source': s0['source'], 'target': other})
    engine = FormalL0Engine(test_only_operative_adoption=True)
    state, _, _ = advance(engine, state, 1, 0)
    result, p, _ = advance(engine, state, 2, 1)
    target = p['experience']['root']
    formed = [e for e in result['l0_state']['operative_test_only']['edges'] if e['target'] == target]
    assert {e['source'] for e in formed} == {s0['target'], other}


def test_identity_renaming_not_fixture_branch():
    w = witness(('ordinary:97', 'ordinary:3'))
    assert w['s1']['source'] == 'ordinary:3'
    assert w['s1'] in w['reentry']['processing']['operative_dependencies']['dependencies']


def test_shared_capacity_rejects_new_edge_batch_without_eviction():
    caps = FormalLimits(relations=4)
    state, s0 = initial(caps)
    engine = FormalL0Engine(caps, test_only_operative_adoption=True)
    state, _, _ = advance(engine, state, 1, 0)
    result, p, journal = advance(engine, state, 2, 1)
    assert p['experience']['root'] in result['relations']
    assert result['l0_state']['operative_test_only']['edges'] == [s0]
    limits = [v for k, v in journal if k == 'CURRENT_LIMIT_ENCOUNTER']
    assert any(v['auditor_metadata']['semantic_code'] == 'TEST_ONLY_OPERATIVE_CAPACITY' for v in limits)
    assert len(result['relations']) + len(result['l0_state']['operative_test_only']['edges']) == caps.relations
    advance(engine, result, 3, 2)  # No invalid over-cap state left for reentry.


def test_default_off_matches_immutable_base_full_state_frame_and_journal():
    assert default_equivalence()


def test_default_off_rejects_experimental_state():
    state, _ = initial()
    with pytest.raises(ValueError, match='explicit opt-in'):
        advance(FormalL0Engine(), state, 1, 0)


def test_core_cannot_write_experimental_state_without_touching_a_database():
    core = ACore.__new__(ACore)
    core._closed = False
    state, _ = initial()
    with pytest.raises(ValueError, match='cannot be persisted'):
        core._transition('TEST', {}, internal_state=state)


def test_no_independent_executor_consumer_body_or_post_processing():
    ordinary = inspect.getsource(FormalL0Engine._advance_operative)
    assert read_has_no_audit_or_side_executor_access()
    assert 'super().advance' not in ordinary
    assert ordinary.index('_read_operative_operands') < ordinary.index('expected =') < ordinary.index('partial =')
    tree = ast.parse(inspect.getsource(inspect.getmodule(FormalL0Engine)))
    assert not any(isinstance(n, ast.ImportFrom) and (n.module or '').startswith('experimental') for n in ast.walk(tree))
    assert not FormalL0Engine()._test_only_operative_adoption


def test_option_type_is_explicit():
    with pytest.raises(ValueError):
        FormalL0Engine(test_only_operative_adoption='yes')


def test_isolated_transition_and_hooks_equal_preserved_implementation_ast():
    assert preserved_transition_identity()


def test_isolation_preserves_full_enabled_state_frame_and_journal():
    assert migration_equivalence()


def test_enabled_advance_cannot_delegate_then_attach_an_answer():
    from individual.formal_l0 import FormalL0Engine as FrozenEngine
    state, _ = initial()
    with patch.object(FrozenEngine, 'advance', side_effect=AssertionError('No production advance in opt-in')):
        w_engine = FormalL0Engine(test_only_operative_adoption=True)
        first, _, _ = advance(w_engine, state, 1, 0)
        committed, _, _ = advance(w_engine, first, 2, 1)
        _, p, _ = advance(w_engine, committed, 3, 2)
    assert len(p['processing']['operative_dependencies']['dependencies']) == 2


def test_default_off_delegates_to_frozen_engine_without_experimental_transition():
    state = InternalState().to_dict()
    engine = FormalL0Engine()
    with patch.object(engine, '_advance_operative', side_effect=AssertionError('No opt-in')):
        advance(engine, state, 1, 0)


def test_production_engine_and_all_world_entry_frozen_sources_are_unchanged():
    import hashlib
    from pathlib import Path
    frozen = json.loads(Path('WORLD_ENTRY_FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in frozen['component_hashes'].items():
        assert hashlib.sha256(Path(name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected
    from individual.formal_l0 import FormalL0Engine as FrozenEngine
    assert 'test_only_operative_adoption' not in inspect.signature(FrozenEngine).parameters
