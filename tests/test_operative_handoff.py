"""Isolated structural execution tests; no Minecraft or formal individual."""
from dataclasses import replace
from unittest.mock import patch
import ast
import inspect
import pytest
from experimental.operative_handoff.mechanism import Mechanism
from experimental.operative_handoff.model import Edge, Input, Node
from experimental.operative_handoff.runtime import Runtime, form
from experimental.operative_handoff.validation import fixture, run_validation, static_checks, witness


def test_all_eight_frozen_criteria():
    report = run_validation()
    assert report['classification'] == 'PASS'
    assert list(report['criteria'].values()) == ['PASS'] * 8


def test_origin_edge_causes_actual_participation():
    r, a, b, c = fixture()
    inp = Input(frozenset((a,)))
    assert r.advance(inp).participating == (a, b)
    masked = Runtime((a, b, c), ())
    assert masked.advance(inp).participating == (a,)


def test_no_direct_edge_input_and_commit_before_use():
    r, a, b, c, initial, first, before, processing, committed = witness()
    assert set(Input.__dataclass_fields__) == {'active', 'observed'}
    assert Edge(b, c) not in initial.edges | before.edges
    assert c not in processing.participating
    assert committed.history[-1].formed == (Edge(b, c),)
    assert r.advance(Input(frozenset((a,)))).participating == (a, b, c)


def test_same_mechanism_called_for_origin_and_later_edges():
    m = Mechanism()
    r, a, b, c = fixture()
    r.mechanism = m
    with patch.object(m, 'advance', wraps=m.advance) as calls:
        r.advance(Input(frozenset((a,))))
        r.advance(Input(frozenset((a,)), frozenset((c,))))
        r.advance(Input(frozenset((a,))))
    assert calls.call_count == 3
    assert calls.call_args.args[1] == frozenset((Edge(a, b), Edge(b, c)))


def test_edge_only_ablation_preserves_every_other_state_field():
    r, a, b, c, *_, committed = witness()
    masked = replace(committed, edges=committed.edges - {Edge(b, c)})
    assert replace(masked, edges=committed.edges) == committed
    inp = Input(frozenset((a,)))
    normal = Runtime.from_state(committed).advance(inp)
    screened = Runtime.from_state(masked).advance(inp)
    assert normal.dependencies == (Edge(a, b), Edge(b, c))
    assert screened.dependencies == (Edge(a, b),)
    assert c in normal.participating and c not in screened.participating


def test_executor_cannot_receive_or_read_audit():
    assert tuple(inspect.signature(Mechanism.advance).parameters) == ('self', 'nodes', 'edges', 'active')
    assert static_checks() == {'audit_fields_read': [], 'forbidden_domain_tokens': [],
                               'edge_execution_loop_count': 1}


@pytest.mark.parametrize('mode', ['removed', 'unified', 'swapped', 'malformed'])
def test_provenance_has_no_execution_privilege(mode):
    r, a, b, c, *_, state = witness()
    if mode == 'removed':
        audit = ()
    else:
        audit = tuple(replace(e, provenance=(state.audit[::-1][i].provenance if mode == 'swapped'
                                            else mode)) for i, e in enumerate(state.audit))
    inp = Input(frozenset((a,)))
    assert Runtime.from_state(replace(state, audit=audit)).advance(inp) == r.advance(inp)


def test_normal_reentry_and_reuse_never_reform_edge():
    r, a, b, c, *_, state = witness()
    with patch('experimental.operative_handoff.runtime.form', side_effect=AssertionError('No reformation')):
        first = r.advance(Input(frozenset((a,))))
        second = r.advance(Input(frozenset((a,))))
    assert first == second and first.participating == (a, b, c)
    assert r.state.edges == state.edges and r.state.audit == state.audit


def test_formation_does_not_execute_mechanism():
    _, a, b, c, *_, state = witness()
    with patch.object(Mechanism, 'advance', side_effect=AssertionError('No execution in formation')):
        assert form(replace(state, edges=state.edges - {Edge(b, c)}), frozenset((c,))) == (Edge(b, c),)


def test_no_prior_participation_or_no_observed_material_no_formation():
    r, a, b, c = fixture()
    r.advance(Input(observed=frozenset((c,))))
    assert r.state.edges == frozenset((Edge(a, b),))
    r, a, b, c = fixture()
    r.advance(Input(frozenset((a,))))
    r.advance(Input(frozenset((a,))))
    assert r.state.edges == frozenset((Edge(a, b),))


def test_arbitrary_identity_renaming_and_all_frontiers_no_selector():
    r, a, b, c, *_, state = witness(('opaque:7', 'opaque:19', 'opaque:2'))
    assert r.advance(Input(frozenset((a,)))).participating == (a, b, c)
    d, e = Node('opaque:d'), Node('opaque:e')
    r = Runtime((a, b, c, d, e), (Edge(a, b), Edge(a, d)))
    r.advance(Input(frozenset((a,))))
    r.advance(Input(frozenset((a,)), frozenset((c, e))))
    assert r.state.history[-1].formed == tuple(sorted((Edge(b, c), Edge(b, e), Edge(d, c), Edge(d, e))))


def test_disconnected_graph_does_not_participate():
    r, a, b, c, *_, state = witness()
    x, y = Node('x'), Node('y')
    extended = replace(state, nodes=state.nodes | {x, y}, edges=state.edges | {Edge(x, y)})
    assert Runtime.from_state(extended).advance(Input(frozenset((a,)))) == r.advance(Input(frozenset((a,))))


@pytest.mark.parametrize('kind', ['active', 'observed', 'edge'])
def test_undeclared_endpoint_rejected_without_commit(kind):
    r, a, b, c = fixture()
    state = r.state
    x = Node('missing')
    with pytest.raises(ValueError):
        if kind == 'edge':
            Mechanism().advance(state.nodes, {Edge(a, x)}, {a})
        else:
            r.advance(Input(**{kind: frozenset((x,))}))
    assert r.state == state


def test_module_isolation():
    from pathlib import Path
    for path in Path('experimental/operative_handoff').glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.level or node.module in {'dataclasses', 'collections', 'pathlib'}
            if isinstance(node, ast.Import):
                assert all(n.name in {'ast', 'inspect', 'json'} for n in node.names)
