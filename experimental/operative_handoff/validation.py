"""Fixed OH-T1 through OH-T8 witness and edge-only counterfactual."""
from dataclasses import asdict, replace
import ast
import inspect
import json
from .mechanism import Mechanism
from .model import Edge, Input, Node
from .runtime import Runtime

CRITERIA = tuple(f'OH_T{i}' for i in range(1, 9))
CLAIM = ('Within the frozen minimal TEST_ONLY scope, an origin-supplied operative edge '
         'and a later internally formed edge of the same structural kind entered the same '
         'non-privileged generic execution mechanism; the formed edge became an ordinary '
         'recursive dependency, survived normal reentry, and was causally necessary under edge ablation.')
NONCLAIMS = ('behavioral causal closure', 'action authorship', 'parameter authorship',
             'goal authorship', 'survival authorship', 'Minecraft behavior',
             'L1/upward recursion', 'universal Perfect Recursion proof',
             'all formed structures executable', 'formal-runtime adoption')


def fixture(names=('A', 'B', 'C')):
    a, b, c = map(Node, names)
    return Runtime((a, b, c), (Edge(a, b),)), a, b, c


def witness(names=('A', 'B', 'C')):
    runtime, a, b, c = fixture(names)
    initial = runtime.state
    first = runtime.advance(Input(frozenset((a,))))
    before_formation = runtime.state
    formation_processing = runtime.advance(Input(frozenset((a,)), frozenset((c,))))
    committed = runtime.state
    return runtime, a, b, c, initial, first, before_formation, formation_processing, committed


def static_checks():
    tree = ast.parse(inspect.getsource(Mechanism))
    attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    forbidden = {'provenance', 'audit', 'formed_version', 'support', 'history'}
    source = inspect.getsource(Mechanism).lower()
    return {'audit_fields_read': sorted(attributes & forbidden),
            'forbidden_domain_tokens': [x for x in ('creator', 'internal', 'bootstrap',
                'bodyport', 'minecraft', 'reward', 'goal', 'survival', 's0', 's1') if x in source],
            'edge_execution_loop_count': sum(isinstance(n, ast.For) and
                isinstance(n.iter, ast.Subscript) and isinstance(n.iter.value, ast.Name) and
                n.iter.value.id == 'outgoing' for n in ast.walk(tree))}


def trace(p):
    return {'participating': [n.identity for n in p.participating],
            'dependencies': [[e.source.identity, e.target.identity] for e in p.dependencies]}


def run_validation():
    runtime, a, b, c, initial, first, before, formation_processing, committed = witness()
    s0, s1 = Edge(a, b), Edge(b, c)
    current = Input(frozenset((a,)))
    canonical = runtime.advance(current)
    after_use = runtime.state
    reuse = runtime.advance(current)
    ablated_state = replace(committed, edges=committed.edges - {s1})
    ablated = Runtime.from_state(ablated_state).advance(current)
    neutral_state = replace(committed, audit=())
    neutral = Runtime.from_state(neutral_state).advance(current)
    equal_labels = replace(committed, audit=tuple(replace(e, provenance='NEUTRAL') for e in committed.audit))
    unified = Runtime.from_state(equal_labels).advance(current)
    checks = static_checks()
    expected = (a, b, c)
    outcomes = (
        first.participating == (a, b) and first.dependencies == (s0,),
        s1 not in initial.edges and s1 not in before.edges and s1 in committed.edges
        and committed.history[-1].formed == (s1,) and formation_processing.participating == (a, b),
        type(s0) is type(s1) and checks['edge_execution_loop_count'] == 1
        and not checks['audit_fields_read'] and not checks['forbidden_domain_tokens'],
        canonical.participating == expected and canonical.dependencies == (s0, s1),
        canonical == Runtime.from_state(committed).advance(current),
        ablated.participating == (a, b) and ablated.dependencies == (s0,)
        and ablated_state.nodes == committed.nodes and ablated_state.audit == committed.audit
        and ablated_state.history == committed.history and canonical != ablated,
        canonical == neutral == unified,
        reuse == canonical and runtime.state.edges == after_use.edges == committed.edges
        and runtime.state.audit == after_use.audit == committed.audit
        and runtime.state.history[-1].formed == (),
    )
    return {'classification': 'PASS' if all(outcomes) else 'FAIL',
            'criteria': dict(zip(CRITERIA, ('PASS' if x else 'FAIL' for x in outcomes))),
            'scope': 'minimal TEST_ONLY temporal-frontier formation and structural dependency execution',
            'fixture': {'nodes': ['A', 'B', 'C'], 'S0': ['A', 'B'],
                        'formation_input': {'active': ['A'], 'observed': ['C']},
                        'later_input': {'active': ['A'], 'observed': []}},
            'S1': asdict(next(e for e in committed.audit if e.edge == s1)),
            'S0': asdict(next(e for e in committed.audit if e.edge == s0)),
            'committed_edge_collection': [[e.source.identity, e.target.identity] for e in sorted(committed.edges)],
            'formation_history': [{'version': cycle.version,
                'input': {'active': sorted(n.identity for n in cycle.input.active),
                          'observed': sorted(n.identity for n in cycle.input.observed)},
                'processing': trace(cycle.processing),
                'formed': [[e.source.identity, e.target.identity] for e in cycle.formed]}
                for cycle in committed.history],
            'mechanism': {'file': 'experimental/operative_handoff/mechanism.py',
                          'symbol': 'Mechanism.advance',
                          'line': inspect.getsourcelines(Mechanism.advance)[1],
                          'execution_input_fields': ['nodes', 'edges', 'active'],
                          'same_edge_collection': True,
                          'same_execution_path': True, 'static_checks': checks},
            'traces': {'origin': trace(first), 'formation_cycle': trace(formation_processing),
                       'canonical': trace(canonical), 'edge_ablation': trace(ablated),
                       'provenance_removed': trace(neutral), 'provenance_unified': trace(unified),
                       'repeated_reuse': trace(reuse)},
            'edge_ablation_held_fixed': ['nodes', 'S0', 'input', 'history', 'audit', 'previous processing', 'M'],
            'claim': CLAIM, 'nonclaims': NONCLAIMS,
            'minecraft_run': False, 'new_a_created': False, 'formal_runtime_changed': False}


if __name__ == '__main__':
    print(json.dumps(run_validation(), indent=2))
