"""Fixed in-memory FormalL0 witness; no detached answer or graph executor."""
from copy import deepcopy
import ast
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import types
import textwrap
from unittest.mock import patch
from uuid import UUID

from .engine import TestOnlyFormalL0Engine as FormalL0Engine
from individual.formal_l0 import FormalL0Engine as FrozenFormalL0Engine, FormalLimits, digest
from individual.formal_boundary import boundary_for
from individual.internal_state import InternalState
from individual.observation import ObservationFrame

BASE_COMMIT = '0cd29715e59ec480a4d7acc8fb64de27a9763ec2'
CRITERIA = tuple(f'FA_T{i}' for i in range(1, 11))


def frame(sequence, value):
    return ObservationFrame(f'TEST_ONLY:E{sequence}', sequence, f'test:{sequence}',
                            'FORMALL0-OPERATIVE-TEST_ONLY', 0, {}, {}, {},
                            {'1': value}, {})


def initial(caps=None, names=('opaque:origin', 'opaque:operand')):
    """Origin scaffold only. No later relation identity or S1 is supplied."""
    caps = caps or FormalLimits()
    internal = InternalState()
    for i, name in enumerate(names):
        unit = f'U-origin-{i}'
        internal.units[unit] = {'unit_id': unit, 'pattern': [], 'observations': 0,
                              'first_frame_id': 'ORIGIN', 'last_sequence': 0}
        internal.relations[name] = {'relation_id': name, 'antecedent': unit,
            'action_code': -1, 'outcomes': {unit: {'unit_id': unit,
                'evidence_count': 0, 'evidence_refs': []}}, 'evidence_count': 0,
            'last_sequence': 0, 'evidence_refs': []}
    edge = {'source': names[0], 'target': names[1]}
    internal.l0_state.update(boundary_for({}, caps, {}))
    internal.l0_state.update(profile='formal_l0', active_layer='L0', process_id=None,
        previous_frame=None, previous_unit=None,
        feedback={'next_relation_ref': names[0]}, pending_consequences=[],
        operative_test_only={'schema': 'FORMALL0-OPERATIVE-TEST_ONLY-1', 'edges': [edge],
            'evidence': {digest(edge): {'provenance': 'ORIGIN_SUPPLIED',
                                      'state_version': 0, 'supports': {'initialization': True}}}})
    return internal.to_dict(), edge


def advance(engine, state, sequence, value):
    internal, observed, journal = engine.advance(state, frame(sequence, value), sequence, ())
    partials = [p for kind, p in journal if kind == 'RECURSIVE_PARTIAL_OUTPUT']
    return internal.to_dict(), partials[0] if partials else None, journal


def witness(names=('opaque:origin', 'opaque:operand')):
    engine = FormalL0Engine(test_only_operative_adoption=True)
    origin, s0 = initial(names=names)
    first, _, _ = advance(engine, origin, 1, 0)
    committed, partial, journal = advance(engine, first, 2, 1)
    graph = committed['l0_state']['operative_test_only']
    newly_formed = [e for e in graph['edges'] if e != s0]
    if len(newly_formed) != 1:
        raise AssertionError('Fixed witness did not form exactly one first edge')
    s1, = newly_formed
    later, reentry, _ = advance(engine, committed, 3, 2)
    reused, reuse, _ = advance(engine, later, 4, 3)
    repeated, repeat, _ = advance(engine, reused, 5, 4)
    return {'engine': engine, 'origin': origin, 's0': s0, 'first': first,
        'committed': committed, 'formation_partial': partial, 'formation_journal': journal,
        's1': s1, 'later': later, 'reentry': reentry, 'reused': reused,
        'reuse': reuse, 'repeated': repeated, 'repeat': repeat}


def edge_ablation(state, edge):
    ablated = deepcopy(state)
    ablated['l0_state']['operative_test_only']['edges'].remove(edge)
    return ablated


def operands(partial):
    p = partial['processing']
    return {key: p[key] for key in ('expected_outcomes', 'same_context_as_prediction',
                                   'outcome_previously_observed', 'operative_dependencies')}


def default_equivalence():
    """Execute immutable base source and current interpreter at the same boundary."""
    source = subprocess.check_output(['git', 'show', BASE_COMMIT + ':individual/formal_l0.py'],
                                     encoding='utf-8')
    baseline = types.ModuleType('individual._formal_operative_baseline')
    baseline.__package__ = 'individual'
    baseline.__file__ = str(Path('individual/formal_l0.py').resolve())
    # dataclass resolves its owning module; temporary registration is removed afterwards.
    import sys
    sys.modules[baseline.__name__] = baseline
    try:
        exec(compile(source, baseline.__file__, 'exec'), baseline.__dict__)
        base_engine = baseline.FormalL0Engine(caps=baseline.FormalLimits())
        candidates = [FrozenFormalL0Engine(), FormalL0Engine(), FormalL0Engine(test_only_operative_adoption=False)]
        start = InternalState().to_dict()
        for candidate in candidates:
            old, new = deepcopy(start), deepcopy(start)
            for sequence, value in enumerate((0, 1, 1, 0, 2, 3, 3, 0), 1):
                with patch.object(baseline, 'uuid4', side_effect=(UUID(int=i) for i in range(1, 100))), \
                        patch('individual.formal_boundary.uuid4', return_value=UUID(int=1000)):
                    expected = base_engine.advance(old, frame(sequence, value), sequence, ())
                with patch('individual.formal_l0.uuid4', side_effect=(UUID(int=i) for i in range(1, 100))), \
                        patch('individual.formal_boundary.uuid4', return_value=UUID(int=1000)):
                    actual = candidate.advance(new, frame(sequence, value), sequence, ())
                if (expected[0].to_dict(), expected[1].to_dict(), expected[2]) != (
                        actual[0].to_dict(), actual[1].to_dict(), actual[2]):
                    return False
                old, new = expected[0].to_dict(), actual[0].to_dict()
        return True
    finally:
        del sys.modules[baseline.__name__]


def preserved_transition_identity():
    """Copied enabled transition and both hooks equal the saved implementation AST."""
    saved = ast.parse(Path(__file__).with_name('history').joinpath('formal_l0_pre_isolation.py.txt').read_text(encoding='utf-8'))
    original = next(n for n in saved.body if isinstance(n, ast.ClassDef) and n.name == 'FormalL0Engine')
    migrated = ast.parse(inspect.getsource(inspect.getmodule(FormalL0Engine)))
    isolated = next(n for n in migrated.body if isinstance(n, ast.ClassDef) and n.name == 'TestOnlyFormalL0Engine')
    for before, after in (('advance', '_advance_operative'),
                          ('_read_operative_operands', '_read_operative_operands'),
                          ('_form_operative_dependencies', '_form_operative_dependencies')):
        expected = next(n for n in original.body if isinstance(n, ast.FunctionDef) and n.name == before)
        actual = next(n for n in isolated.body if isinstance(n, ast.FunctionDef) and n.name == after)
        expected.name = actual.name
        if ast.dump(expected, include_attributes=False) != ast.dump(actual, include_attributes=False):
            return False
    return True


def migration_equivalence():
    """Full transition equivalence oracle, never an answer source for the witness."""
    import sys
    saved = Path(__file__).with_name('history') / 'formal_l0_pre_isolation.py.txt'
    prior = types.ModuleType('individual._operative_pre_isolation_oracle')
    prior.__package__ = 'individual'
    prior.__file__ = str(Path('individual/formal_l0.py').resolve())
    sys.modules[prior.__name__] = prior
    try:
        exec(compile(saved.read_text(encoding='utf-8'), str(saved), 'exec'), prior.__dict__)
        old_engine = prior.FormalL0Engine(test_only_operative_adoption=True)
        new_engine = FormalL0Engine(test_only_operative_adoption=True)
        start, _ = initial()
        old, new = deepcopy(start), deepcopy(start)
        for sequence, value in enumerate((0, 1, 2, 3, 4, 5, 5, 0), 1):
            with patch.object(prior, 'uuid4', side_effect=(UUID(int=i) for i in range(1, 100))):
                expected = old_engine.advance(old, frame(sequence, value), sequence, ())
            with patch('experimental.formall0_operative.engine.uuid4', side_effect=(UUID(int=i) for i in range(1, 100))):
                actual = new_engine.advance(new, frame(sequence, value), sequence, ())
            if (expected[0].to_dict(), expected[1].to_dict(), expected[2]) != (
                    actual[0].to_dict(), actual[1].to_dict(), actual[2]):
                return False
            old, new = expected[0].to_dict(), actual[0].to_dict()
        return True
    finally:
        del sys.modules[prior.__name__]


def read_has_no_audit_or_side_executor_access():
    """Check executable AST accesses/calls, excluding descriptive docstrings."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(FormalL0Engine._read_operative_operands)))
    forbidden = {'evidence', 'provenance', 'ORIGIN_SUPPLIED', 'INTERNALLY_FORMED',
                 'operative_handoff', 'consume', 'Mechanism', 'sampler', 'binder'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            return False
        if isinstance(node, ast.Name) and node.id in forbidden:
            return False
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value in forbidden:
            return False
        if isinstance(node, ast.Call) and any(isinstance(a, ast.Constant) and a.value in forbidden for a in node.args):
            return False
    return True


def run_validation():
    w = witness()
    engine, s0, s1 = w['engine'], w['s0'], w['s1']
    origin_ablated = edge_ablation(w['first'], s0)
    _, no_origin, _ = advance(engine, origin_ablated, 2, 1)
    s1_ablated = edge_ablation(w['committed'], s1)
    _, no_s1, _ = advance(engine, s1_ablated, 3, 2)
    restored = InternalState.from_dict(json.loads(json.dumps(w['committed']))).to_dict()
    _, restored_read, _ = advance(engine, restored, 3, 2)
    _, calculation, _ = advance(engine, w['later'], 4, 3)
    _, ablated_calculation, _ = advance(engine, edge_ablation(w['later'], s1), 4, 3)
    neutral = []
    for mode in ('removed', 'unified', 'swapped'):
        state = deepcopy(w['committed'])
        evidence = state['l0_state']['operative_test_only']['evidence']
        if mode == 'removed':
            evidence.clear()
        else:
            for key, e in evidence.items():
                e['provenance'] = ('NEUTRAL' if mode == 'unified' else
                    'INTERNALLY_FORMED' if key == digest(s0) else 'ORIGIN_SUPPLIED')
        _, p, _ = advance(engine, state, 3, 2)
        neutral.append(operands(p) == operands(w['reentry']))
    proof = w['committed']['l0_state']['operative_test_only']['evidence'][digest(s1)]
    formed_relation = w['formation_partial']['experience']['root']
    source = inspect.getsource(FormalL0Engine._advance_operative)
    no_side_executor = read_has_no_audit_or_side_executor_access()
    criteria = (
        s0 in w['formation_partial']['processing']['operative_dependencies']['dependencies']
        and operands(w['formation_partial']) != operands(no_origin)
        and 'U-origin-1' not in no_origin['processing']['expected_outcomes'],
        s1 not in w['origin']['l0_state']['operative_test_only']['edges']
        and formed_relation not in w['first']['relations']
        and s1['target'] == formed_relation and s1['source'] == s0['target']
        and proof['supports']['experience_id'] == w['formation_partial']['experience']['experience_id']
        and proof['supports']['integration_id'] == w['committed']['latest_integration']['integration_id'],
        restored == w['committed'] and operands(restored_read) == operands(w['reentry']),
        set(s0) == set(s1) == {'source', 'target'}
        and s0 in w['reentry']['processing']['operative_dependencies']['dependencies']
        and s1 in w['reentry']['processing']['operative_dependencies']['dependencies']
        and no_side_executor,
        w['committed']['l0_state']['feedback']['next_relation_ref'] == s0['source']
        and s1['target'] in w['reentry']['processing']['operative_dependencies']['relations'],
        w['reentry']['processing']['expected_outcomes'] != no_s1['processing']['expected_outcomes']
        and s1['target'] not in no_s1['processing']['operative_dependencies']['relations']
        and calculation['processing']['outcome_previously_observed'] is True
        and ablated_calculation['processing']['outcome_previously_observed'] is None,
        all(neutral),
        all(s1 in p['processing']['operative_dependencies']['dependencies'] for p in
            (w['reentry'], w['reuse'], w['repeat']))
        and w['reused']['l0_state']['operative_test_only'] == w['repeated']['l0_state']['operative_test_only'],
        default_equivalence(),
        no_side_executor and 'super().advance' not in source
        and source.index('_read_operative_operands') < source.index('expected =')
        and source.index('expected =') < source.index("partial ="),
    )
    focused_checks = dict(zip(CRITERIA, ('PASS' if x else 'FAIL' for x in criteria)))
    acceptance = dict(focused_checks)
    # An isolated validator cannot certify the separate mandatory full regression.
    acceptance['FA_T9'] = 'NOT_ESTABLISHED' if criteria[8] else 'FAIL'
    return {'classification': 'NOT_ESTABLISHED' if all(criteria) else 'FAIL',
        'focused_classification': 'PASS' if all(criteria) else 'FAIL',
        'focused_checks': focused_checks, 'criteria': acceptance,
        'full_regression_required': True,
        'base_commit': BASE_COMMIT, 'scope': 'TEST_ONLY synthetic numeric frames, real FormalL0 / InternalState',
        'representation': 'l0_state.operative_test_only; source/target ordinary relation references',
        'S0': s0, 'S1': s1, 'S1_evidence': proof,
        'canonical_test_states': {key: w[key] for key in
            ('origin', 'first', 'committed', 'later', 'reused', 'repeated')},
        'S1_only_ablated_state': edge_ablation(w['later'], s1),
        'trace': {'origin_adopted': operands(w['formation_partial']), 'origin_ablated': operands(no_origin),
            'reentry': operands(w['reentry']), 'S1_ablated': operands(no_s1),
            'calculation': operands(calculation), 'calculation_ablated': operands(ablated_calculation),
            'reuse': operands(w['reuse']), 'repeat': operands(w['repeat'])},
        'provenance_neutrality': neutral,
        'formation_rule': 'all executed terminal relation operands -> this advance newly inserted experience relation',
        'default_equivalence_boundary': 'full InternalState, ObservationFrame and journal; eight input rounds; same UUID streams including formal_condition_id',
        'default_behavior_equivalence': criteria[8], 'specialized_consumer_required': False,
        'preserved_transition_ast_identity': preserved_transition_identity(),
        'migration_full_transition_equivalence': migration_equivalence(),
        'independent_graph_executor': False, 'minecraft_run': False, 'real_a_created': False,
        'body_changed': False, 'sampler_binder_changed': False,
        'nonclaims': ['production A adoption', 'Minecraft behavioral authorship', 'action/parameter authorship',
            'autonomous goals', 'behavioral causal closure', 'L1/upward recursion', 'universal Perfect Recursion']}


if __name__ == '__main__':
    print(json.dumps(run_validation(), indent=2))
