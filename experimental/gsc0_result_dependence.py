"""Independent TEST_ONLY persisted-result counterfactual; production rules untouched.

Run: python -m experimental.gsc0_result_dependence
No A, FormalL0, Minecraft, SQLite, or existing report is imported or written.
"""
from dataclasses import asdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import unittest

from experimental.gsc0.engine import Condition, Engine
from experimental.gsc0.model import (
    Variable, Value, Relation, Equality, Binding, PortBinding, Conflict,
    Witness, Composite, Observation, Seed, Support, encode, difference,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'GSC0_RECURSIVE_RESULT_DEPENDENCE_VALIDATION.json'
GRAPH_TYPES = (Equality, Binding, PortBinding, Conflict, Witness)


class AblationUndefined(Exception):
    pass


def guard():
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    return {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths if p}


def cases():
    """Finite predeclared inputs, with new future graph facts in both cases."""
    x = Variable('X', namespace='rrd-single')
    one, two, three = (Value(i) for i in (1, 2, 3))
    condition = Condition((x,), (one, two, three), (('p', ('node',)),))
    history = (Seed(Relation('R', 'p', (x,)), ('H-R',)),
               Seed(Binding(x, one), ('H-1',)),
               Seed(Binding(x, one), ('H-observed',), 'OBSERVED'))
    old_two = difference(Observation('H0', ()),
                         Observation('H1', (('v', Binding(x, two), 'H-2'),)))
    future = difference(Observation('I0', (('v', Binding(x, two), 'H-2'),)),
                        Observation('I1', (('v', Binding(x, three), 'I-3'),)))
    yield 'conflict_and_difference', condition, history + old_two, future

    x, y = (Variable(n, namespace='rrd-alias') for n in ('X', 'Y'))
    value = Value(1)
    condition = Condition((x, y), (value,), (('p', ('node',)),))
    history = (Seed(Relation('R', 'p', (x,)), ('H-R',)),
               Seed(Equality(y, x), ('H-Eq',)),
               Seed(Binding(y, value), ('H-Bind',)))
    future = difference(Observation('I0', ()), Observation('I1', (
        ('r', Relation('R-future', 'p', (y,)), 'I-R'),)))
    yield 'alias_and_future_relation', condition, history, future


def input_only(previous, history):
    """Canonical non-derived State, built from exact input_records and declarations.

    Dual input/derived facts stay, with ONLY their original input support.
    All derivation-only facts and all Composite/cache material are removed.
    No root or input_record is removed. Ambiguous/inconsistent carriers stop.
    """
    declarations = (*previous.condition.nodes, *previous.condition.values,
                    *previous.condition.references)
    supplied = tuple(Seed(d, ('DECL:' + encode(d.key),)) for d in declarations) + history
    expected_records = {(s.fact.key, s.sources, s.rule) for s in history}
    if previous.input_records != expected_records:
        raise AblationUndefined('input_records do not exactly describe the supplied H')
    external = {}
    originals = {}
    for seed in supplied:
        if seed.rule not in ('INPUT', 'OBSERVED') and not seed.rule.startswith('DIFF-'):
            raise AblationUndefined('Unrecognized external input rule')
        if previous.facts.get(seed.fact.key) != seed.fact:
            raise AblationUndefined('Original material missing or changed in COMPLETE state')
        proof = Support(seed.rule, tuple(('Root', s) for s in seed.sources))
        if proof not in previous.proofs.get(seed.fact.key, ()):
            raise AblationUndefined('Original direct support cannot be identified')
        originals[seed.fact.key] = seed.fact
        external.setdefault(seed.fact.key, set()).add(proof)
    roots = {p for supports in external.values() for s in supports for p in s.premises}
    if roots != previous.roots:
        raise AblationUndefined('Roots include unexplained external material')
    # Unknown non-input/non-Composite facts cannot silently be classified as O-G0-1.
    removed = {k: f for k, f in previous.facts.items() if k not in originals}
    if any(not isinstance(f, GRAPH_TYPES + (Composite,)) for f in removed.values()):
        raise AblationUndefined('Unclassified non-input structure')
    clone = previous.clone()
    clone.facts = dict(originals)
    clone.proofs = external
    clone.composition = None
    assert clone.roots == previous.roots
    assert clone.input_records == previous.input_records
    overlap = {k for k in originals if previous.proofs.get(k, set()) - external[k]}
    inventory = {
        'declarations': sorted({d.key for d in declarations}, key=encode),
        'original_seed_keys': sorted({s.fact.key for s in history}, key=encode),
        'dual_input_derived_keys': sorted(overlap, key=encode),
        'removed_graph_facts': [k for k, f in removed.items() if isinstance(f, GRAPH_TYPES)],
        'removed_composite_count': sum(isinstance(f, Composite) for f in removed.values()),
        'removed_derived_explicit_supports': sum(map(len, previous.proofs.values())) - sum(map(len, external.values())),
        'roots_preserved': sorted(clone.roots, key=encode),
        'input_records_preserved': sorted(clone.input_records, key=encode),
    }
    return clone, inventory


def full_compare(left, right):
    """Actual content/support comparisons, never digest-only comparisons."""
    a, b = left.state, right.state
    graph = lambda s: {k: f for k, f in s.facts.items() if isinstance(f, GRAPH_TYPES)}
    relevant = lambda s: {k: f for k, f in s.facts.items() if not isinstance(f, Composite)}
    def index(s):
        c = s.composition
        return None if c is None else (c.leaves, c.masks, c.index)
    # All ordinary supports are explicit; all COMPOSE direct supports are fully
    # determined by this lossless predicate index. Do not expand cyclic trees.
    result = {
        'condition': a.condition == b.condition,
        'status': left.status == right.status,
        'canonical_relevant_facts': relevant(a) == relevant(b),
        'graph_projection': graph(a) == graph(b),
        'all_facts_including_auxiliary': a.facts == b.facts,
        'explicit_direct_supports': a.proofs == b.proofs,
        'lossless_compose_support_index': index(a) == index(b),
        'root_witnesses': a.root_witnesses() == b.root_witnesses(),
        'input_roots': a.roots == b.roots,
        'input_records': a.input_records == b.input_records,
    }
    result['structural_equal'] = all(result.values())
    result['different_relevant_keys'] = sorted(
        {k for k in relevant(a).keys() | relevant(b).keys() if relevant(a).get(k) != relevant(b).get(k)}, key=encode)
    result['different_support_keys'] = sorted(
        {k for k in a.proofs.keys() | b.proofs.keys() if a.proofs.get(k) != b.proofs.get(k)}, key=encode)
    return result


def snapshot(result, baseline, future):
    state = result.state
    roots = state.root_witnesses()
    future_roots = {('Root', s) for seed in future for s in seed.sources} - baseline.roots
    graph = {k: f for k, f in state.facts.items() if isinstance(f, GRAPH_TYPES)}
    relevant = {k: f for k, f in state.facts.items() if not isinstance(f, Composite)}
    new = {k for k in relevant if k not in baseline.facts}
    attributable = {k for k in new if roots.get(k, set()) & future_roots}
    return {
        'status': result.status, 'closure_complete': result.closure_complete,
        'operations': result.operations, 'rounds': result.closure_rounds, 'limit': result.limit,
        'stats': result.stats(),
        'graph_type_counts': {t.__name__: sum(isinstance(f, t) for f in graph.values()) for t in GRAPH_TYPES},
        'canonical_relevant_facts': [
            {'key': k, 'type': type(relevant[k]).__name__, 'content': asdict(relevant[k]),
             'all_direct_supports': [{'rule': p.rule, 'premises': p.premises} for p in sorted(
                 state.direct_supports(k), key=lambda p: (p.rule, encode(p.premises)))],
             'root_witnesses': sorted(roots.get(k, ()), key=encode)} for k in sorted(relevant, key=encode)],
        'graph_projection_keys': sorted(graph, key=encode),
        'future_exclusive_roots': sorted(future_roots, key=encode),
        'new_relevant_structures_relative_to_same_full_S_t': sorted(new, key=encode),
        'future_I_attributable_new_relevant_structures': sorted(attributable, key=encode),
        'future_I_attributable_new_graph_structures': sorted(attributable & graph.keys(), key=encode),
        'old_graph_structures_gaining_future_root_support': sorted(
            {k for k in graph if k in baseline.facts and roots.get(k, set()) & future_roots}, key=encode),
    }


def experiment(label, condition, history, future):
    initial = Engine(condition).run(history)
    if not initial.closure_complete:
        return {'case': label, 'classification': 'UNRESOLVED', 'reason': 'H did not yield COMPLETE',
                'initial': initial.stats()}, None
    before = initial.state.canonical_digest()
    try:
        ablated, inventory = input_only(initial.state, history)
    except AblationUndefined as error:
        return {'case': label, 'classification': 'ABLATION_NOT_WELL_DEFINED', 'reason': str(error)}, None
    history_before, future_before = tuple(history), tuple(future)
    results = {
        'A_FULL_PREVIOUS': Engine(condition).run(future, previous=initial.state),
        'B_DERIVED_ABLATION': Engine(condition).run(future, previous=ablated),
        'C_FRESH_RECOMPUTE': Engine(condition).run(history + future),
    }
    a, b, c = results.values()
    comparisons = {name: full_compare(l, r) for name, l, r in (('A_B', a, b), ('A_C', a, c), ('B_C', b, c))}
    complete = all(r.closure_complete for r in results.values())
    classification = 'UNRESOLVED'
    aux_control = None
    if complete:
        if comparisons['A_B']['structural_equal'] and comparisons['A_C']['structural_equal']:
            classification = 'DERIVED_RESULT_NOT_CAUSALLY_NECESSARY'
        elif comparisons['A_B']['structural_equal']:
            classification = 'PERSISTED_NON_DERIVED_STATE_MATTERS'
        else:
            # A/B also differ in dependent Composite cache. If the auxiliary-only
            # intervention changes A, do not falsely attribute that change to O_t.
            aux = initial.state.clone()
            aux.facts = {k: f for k, f in aux.facts.items() if not isinstance(f, Composite)}
            aux.proofs = {k: p for k, p in aux.proofs.items() if k in aux.facts}
            aux.composition = None
            probe = Engine(condition).run(future, previous=aux)
            aux_control = {'status': probe.status, 'A_aux_only': full_compare(a, probe)}
            if probe.closure_complete and aux_control['A_aux_only']['structural_equal']:
                classification = 'PRIOR_DERIVED_RESULT_CAUSALLY_RELEVANT'
    assert before == initial.state.canonical_digest(), 'Original S_t mutated'
    assert history == history_before and future == future_before
    snapshots = {k: snapshot(v, initial.state, future) for k, v in results.items()}
    attribution_equal = len({encode(v['future_I_attributable_new_graph_structures']) for v in snapshots.values()}) == 1
    difference_keys = comparisons['A_B']['different_relevant_keys'] + comparisons['A_B']['different_support_keys']
    report = {
        'case': label, 'classification': classification,
        'condition': asdict(condition), 'caps': asdict(Engine(condition).caps),
        'H': [asdict(s) for s in history], 'I': [asdict(s) for s in future],
        'initial': initial.stats(), 'ablation_inventory': inventory,
        'original_S_t_unchanged': before == initial.state.canonical_digest(),
        'same_Condition_H_I': True, 'comparisons': comparisons, 'arms': snapshots,
        'future_attribution_equal': attribution_equal, 'auxiliary_only_control': aux_control,
        'first_observed_difference': None if not difference_keys else {
            'key': difference_keys[0], 'kind': difference_keys[0][0],
            'meaning': 'First canonical-key difference, not a temporal first-divergence trace'},
    }
    return report, (initial, ablated, results, report)


class ControlTests(unittest.TestCase):
    data = []

    def setUp(self):
        self.assertEqual(len(self.data), 2, 'Use the validation entry to populate both actual experiments')

    def test_complete_three_arms(self):
        for _, _, arms, _ in self.data:
            self.assertTrue(all(r.closure_complete for r in arms.values()))

    def test_original_history_not_mutated(self):
        for _, _, _, report in self.data:
            self.assertTrue(report['original_S_t_unchanged'])

    def test_roots_records_condition_preserved(self):
        for initial, ablated, _, _ in self.data:
            self.assertEqual(initial.state.condition, ablated.condition)
            self.assertEqual(initial.state.roots, ablated.roots)
            self.assertEqual(initial.state.input_records, ablated.input_records)

    def test_ablation_is_nontrivial(self):
        for _, _, _, report in self.data:
            self.assertTrue(report['ablation_inventory']['removed_graph_facts'])
            self.assertGreater(report['ablation_inventory']['removed_derived_explicit_supports'], 0)

    def test_original_seed_supports_kept_only(self):
        for _, ablated, _, _ in self.data:
            for proofs in ablated.proofs.values():
                for p in proofs:
                    self.assertTrue(p.rule in ('INPUT', 'OBSERVED') or p.rule.startswith('DIFF-'))
                    self.assertTrue(all(k in ablated.roots for k in p.premises))

    def test_new_future_graph_formation_exists(self):
        for _, _, _, report in self.data:
            for arm in report['arms'].values():
                self.assertTrue(arm['future_I_attributable_new_graph_structures'])

    def test_classification_matches_actual_comparisons(self):
        for _, _, _, report in self.data:
            if report['classification'] == 'DERIVED_RESULT_NOT_CAUSALLY_NECESSARY':
                self.assertTrue(all(v['structural_equal'] for v in report['comparisons'].values()))
                self.assertTrue(report['future_attribution_equal'])
            self.assertNotEqual(report['classification'], 'ABLATION_NOT_WELL_DEFINED')

    def test_report_encoding_is_lossless(self):
        for _, _, _, report in self.data:
            encoded = compact_case(deepcopy(report))
            keys = encoded['key_table']
            for name, arm in encoded['arms'].items():
                table = arm['canonical_relevant_facts']
                if isinstance(table, dict):
                    table = encoded['arms'][table['same_actual_evidence_as']]['canonical_relevant_facts']
                decoded = [{'key': keys[r['key_id']], 'type': r['type'], 'content': r['content'],
                            'all_direct_supports': [{'rule': p['rule'], 'premises': [keys[k] for k in p['premise_key_ids']]}
                                                    for p in r['all_direct_supports']],
                            'root_witnesses': [keys[k] for k in r['root_key_ids']]} for r in table]
                self.assertEqual(encode(decoded), encode(report['arms'][name]['canonical_relevant_facts']))
                for field, ids in arm.items():
                    if field.endswith('_key_ids'):
                        self.assertEqual(encode([keys[k] for k in ids]), encode(report['arms'][name][field[:-8]]))


def compact_case(report):
    """Lossless key interning and equal-table reuse, AFTER actual comparisons.

    No fact/proof is dropped from the experiment. A single evidence table may
    represent B/C only when their actual facts and direct supports equal A.
    """
    if 'arms' not in report:
        return report
    keys, positions = [], {}
    def key_id(key):
        token = encode(key)
        if token not in positions:
            positions[token] = len(keys)
            keys.append(key)
        return positions[token]
    for arm_name, arm in report['arms'].items():
        records = arm['canonical_relevant_facts']
        compared = report['comparisons'].get('A_B' if arm_name == 'B_DERIVED_ABLATION' else 'A_C', {})
        if arm_name != 'A_FULL_PREVIOUS' and all(compared.get(k) for k in (
                'canonical_relevant_facts', 'explicit_direct_supports', 'root_witnesses')):
            arm['canonical_relevant_facts'] = {'same_actual_evidence_as': 'A_FULL_PREVIOUS',
                                               'verified_by_content_not_digest': True}
        else:
            arm['canonical_relevant_facts'] = [
                {'key_id': key_id(r['key']), 'type': r['type'], 'content': r['content'],
                 'all_direct_supports': [{'rule': p['rule'], 'premise_key_ids': [key_id(k) for k in p['premises']]}
                                         for p in r['all_direct_supports']],
                 'root_key_ids': [key_id(k) for k in r['root_witnesses']]} for r in records]
        for field in ('graph_projection_keys', 'future_exclusive_roots',
                      'new_relevant_structures_relative_to_same_full_S_t',
                      'future_I_attributable_new_relevant_structures',
                      'future_I_attributable_new_graph_structures',
                      'old_graph_structures_gaining_future_root_support'):
            arm[field + '_key_ids'] = [key_id(k) for k in arm.pop(field)]
    report['key_table'] = keys
    report['encoding'] = 'key_ids index key_table; exact-equal B/C evidence tables refer to A; no sampling/truncation'
    return report


def main():
    before = guard()
    reports, data = [], []
    for args in cases():
        report, record = experiment(*args)
        reports.append(report)
        if report['classification'] == 'ABLATION_NOT_WELL_DEFINED':
            break
        if record is not None:
            data.append(record)
    ControlTests.data = data
    if len(data) == 2:
        tested = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ControlTests))
        tests = {'run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors)}
    else:
        tests = {'run': 0, 'failures': 0, 'errors': 0, 'reason': 'Cannot certify counterfactual controls'}
    after = guard()
    changed = [p for p, h in before.items() if after.get(p) != h]
    assert not changed, f'Existing tracked files changed: {changed}'
    classes = {r['classification'] for r in reports}
    outcome = next(iter(classes)) if len(classes) == 1 else 'UNRESOLVED'
    if tests['run'] != 8 or tests['failures'] or tests['errors']:
        outcome = 'ABLATION_NOT_WELL_DEFINED' if outcome == 'ABLATION_NOT_WELL_DEFINED' else 'UNRESOLVED'
    payload = {
        'scope': 'TEST_ONLY fixed-domain GSC-0; no production rule edits',
        'classification': outcome, 'baseline_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
        'tests': tests, 'cases': [compact_case(r) for r in reports],
        'guard': {'existing_tracked_files': len(before), 'changed': changed},
        'comparison_policy': 'Actual fact contents, explicit supports, lossless COMPOSE index, roots and future attribution; operations/rounds excluded from structural equality',
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'classification': outcome, 'tests': tests,
                      'cases': [{ 'case': r['case'], 'classification': r['classification'],
                                 'initial': r.get('initial'), 'arm_work': {k: {'operations': v['operations'], 'rounds': v['rounds'], 'status': v['status']} for k, v in r.get('arms', {}).items()}}
                                for r in reports], 'report': str(REPORT)}, ensure_ascii=True))
    return 0 if outcome not in ('UNRESOLVED', 'ABLATION_NOT_WELL_DEFINED') else 1


if __name__ == '__main__':
    raise SystemExit(main())
