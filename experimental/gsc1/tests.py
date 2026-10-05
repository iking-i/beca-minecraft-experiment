"""Executable cardinality, causality and isolation checks, without real output."""
import ast
from dataclasses import replace
from pathlib import Path
import unittest
from experimental.gsc0.engine import Engine, Condition, Caps, RULES
from experimental.gsc0.model import Binding, Composite, Seed, Value, Variable, encode
from .fixtures import paired_fixture, close_history
from .grounding import check_grounding
from .model import OutputPort, OutwardSchema


def same_closure(test, a, b):
    test.assertTrue(a.closure_complete and b.closure_complete)
    test.assertEqual(a.state.facts, b.state.facts)
    test.assertEqual(a.state.proofs, b.state.proofs)
    test.assertEqual(a.state.roots, b.state.roots)
    test.assertEqual(a.state.input_records, b.state.input_records)
    test.assertEqual(a.state.composition.leaves, b.state.composition.leaves)
    test.assertEqual(a.state.composition.masks, b.state.composition.masks)
    test.assertEqual(a.state.composition.index, b.state.composition.index)


class GSC1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = paired_fixture()
        cls.initial_a, cls.a = close_history(cls.f, cls.f.history_a)
        cls.initial_b, cls.b = close_history(cls.f, cls.f.history_b)
        cls.ga = check_grounding(cls.a, cls.f.schema)
        cls.gb = check_grounding(cls.b, cls.f.schema)

    def test_two_complete_unique_outputs(self):
        for result, expected in ((self.ga, ('A0', 'B0', 'C0')), (self.gb, ('A1', 'B0', 'C1'))):
            self.assertEqual(result.status, 'COMPLETE_GROUNDED')
            self.assertEqual(tuple(v.value for _, v in result.outward.fields), expected)
            self.assertTrue(all(p.status == 'GROUNDED' and len(p.values) == 1 for p in result.ports))

    def test_tuples_not_present_in_history(self):
        for initial in (self.initial_a, self.initial_b):
            result = check_grounding(initial, self.f.schema)
            self.assertEqual(result.status, 'UNRESOLVED')
            self.assertIsNone(result.outward)
            self.assertTrue(all(not p.values for p in result.ports))
        self.assertTrue(all(isinstance(s.fact, Binding) for s in self.f.history_a + self.f.history_b))

    def test_paired_history_causality_same_actual_current_input(self):
        # Input identity and exact facts/supports are shared, not fixture flags.
        current_before = self.f.current_input
        _, swapped = close_history(self.f, self.f.history_b, current=self.f.current_input)
        same_closure(self, swapped, self.b)
        self.assertEqual(current_before, self.f.current_input)
        self.assertEqual(check_grounding(swapped, self.f.schema), self.gb)
        self.assertNotEqual(self.ga.outward.key, self.gb.outward.key)
        differences = tuple(i for i, (a, b) in enumerate(zip(self.f.history_a, self.f.history_b)) if a != b)
        self.assertEqual(differences, (0, 2))
        self.assertEqual(self.a.state.condition, self.b.state.condition)
        self.assertEqual(self.a.state.input_records & {(s.fact.key, s.sources, s.rule) for s in current_before},
                         self.b.state.input_records & {(s.fact.key, s.sources, s.rule) for s in current_before})

    def test_history_ablation_each_port_both_histories(self):
        for history in (self.f.history_a, self.f.history_b):
            for index in range(3):
                _, closed = close_history(self.f, history[:index] + history[index + 1:])
                result = check_grounding(closed, self.f.schema)
                self.assertEqual(result.status, 'UNRESOLVED')
                self.assertIsNone(result.outward)
                self.assertEqual(result.ports[index].values, ())
                self.assertTrue(all(p.status == 'GROUNDED' for i, p in enumerate(result.ports) if i != index))

    def test_current_input_ablation_each_port_both_histories(self):
        for history in (self.f.history_a, self.f.history_b):
            for index in range(3):
                current = self.f.current_input[:index] + self.f.current_input[index + 1:]
                _, closed = close_history(self.f, history, current=current)
                result = check_grounding(closed, self.f.schema)
                self.assertEqual(result.status, 'UNRESOLVED')
                self.assertIsNone(result.outward)
                self.assertEqual(result.ports[index].values, ())

    def test_conflict_retains_both_values_without_output(self):
        extra = Seed(Binding(self.f.sources[1], Value('B1', 'TypeB')), ('H1-conflict',))
        _, closed = close_history(self.f, self.f.history_a + (extra,))
        self.assertTrue(closed.closure_complete, closed.limit)
        result = check_grounding(closed, self.f.schema)
        self.assertEqual(result.status, 'CONFLICT')
        self.assertIsNone(result.outward)
        self.assertEqual({v.value for v in result.ports[1].values}, {'B0', 'B1'})
        self.assertEqual(len(result.ports[1].evidence), 2)
        self.assertTrue(all(e.input_roots and e.direct_supports for e in result.ports[1].evidence))

    def test_mixed_conflict_and_missing_preserves_both_assessments(self):
        extra = Seed(Binding(self.f.sources[1], Value('B1', 'TypeB')), ('H1-conflict',))
        _, closed = close_history(self.f, self.f.history_a[:2] + (extra,))
        result = check_grounding(closed, self.f.schema)
        self.assertEqual(result.status, 'CONFLICT')
        self.assertEqual(tuple(p.status for p in result.ports), ('GROUNDED', 'CONFLICT', 'UNRESOLVED'))
        self.assertIsNone(result.outward)

    def test_duplicate_proofs_not_duplicate_values(self):
        seed = replace(self.f.history_a[0], sources=('H0-second-source',))
        _, closed = close_history(self.f, self.f.history_a + (seed,))
        result = check_grounding(closed, self.f.schema)
        self.assertTrue(result.complete)
        self.assertEqual(result.outward, self.ga.outward)
        self.assertIn(('Root', 'H0-second-source'), result.ports[0].evidence[0].input_roots)

    def test_order_independence(self):
        for history, expected_closure, expected_grounding in (
                (self.f.history_a, self.a, self.ga), (self.f.history_b, self.b, self.gb)):
            all_seeds = history + self.f.current_input
            for seeds in (all_seeds, all_seeds[::-1], all_seeds[::2] + all_seeds[1::2]):
                for queue, rules in (('forward', RULES), ('reverse', RULES[::-1]),
                                     ('interleaved', RULES[2:] + RULES[:2])):
                    closed = Engine(self.f.condition, queue_order=queue, rule_order=rules).run(seeds)
                    same_closure(self, expected_closure, closed)
                    self.assertEqual(check_grounding(closed, self.f.schema), expected_grounding)

    def test_idempotence(self):
        for closed, grounded in ((self.a, self.ga), (self.b, self.gb)):
            repeated = Engine(self.f.condition, queue_order='reverse', rule_order=RULES[::-1]).run(previous=closed.state)
            same_closure(self, closed, repeated)
            self.assertEqual(check_grounding(repeated, self.f.schema), grounded)
            self.assertEqual(check_grounding(closed, self.f.schema), grounded)

    def test_upstream_resource_limit_even_if_every_binding_present(self):
        limited = Engine(self.f.condition, Caps(structures=200)).run(self.f.history_a + self.f.current_input)
        self.assertEqual(limited.status, 'RESOURCE_LIMIT')
        for port, (_, value) in zip(self.f.schema.ports, self.ga.outward.fields):
            self.assertIn(Binding(port.variable, value).key, limited.state.facts)
        result = check_grounding(limited, self.f.schema)
        self.assertEqual(result.status, 'RESOURCE_LIMIT')
        self.assertIsNone(result.outward)
        self.assertEqual(result.ports, ())

    def test_invalid_upstream_and_schema(self):
        for closed in (None, self.a.state, replace(self.a, status='INVALID')):
            self.assertEqual(check_grounding(closed, self.f.schema).status, 'INVALID')
        p = self.f.schema.ports[0]
        for schema in (None, OutwardSchema('empty', ()), OutwardSchema('dup', (p, p)),
                       OutwardSchema('type', (replace(p, value_type='Other'),)),
                       OutwardSchema('unknown', (OutputPort('x', Variable('unknown'), 'Int'),))):
            self.assertEqual(check_grounding(self.a, schema).status, 'INVALID')

    def test_all_lineage_roots_and_immediate_supports_retained(self):
        for closed, grounded in ((self.a, self.ga), (self.b, self.gb)):
            roots = closed.state.root_witnesses()
            self.assertTrue(all(roots.get(key) for key in closed.state.facts))
            for i, p in enumerate(grounded.ports):
                (evidence,) = p.evidence
                self.assertEqual(set(evidence.direct_supports), set(closed.state.direct_supports(evidence.binding_key)))
                self.assertEqual(evidence.input_roots, roots[evidence.binding_key])
                self.assertTrue({('Root', f'H{i}'), ('Root', f'D{i}')} <= evidence.input_roots)
                self.assertTrue(any(s.rule == 'PROP-ALIAS' for s in evidence.direct_supports))
                for support in evidence.direct_supports:
                    self.assertTrue(all(k in closed.state.facts or k in closed.state.roots for k in support.premises))

    def test_generated_composites_and_all_saturated_supports(self):
        for closed in (self.a, self.b):
            for i, port in enumerate(self.f.schema.ports):
                binding = next(f for f in closed.state.facts.values()
                               if isinstance(f, Binding) and f.variable == port.variable)
                history = self.f.history_a if closed is self.a else self.f.history_b
                key = Composite((history[i].fact, self.f.current_input[i].fact, binding)).key
                self.assertIn(key, closed.state.facts)
                self.assertTrue(set(closed.state.direct_supports(key)))
            for fact, support in Engine(self.f.condition).consequences(closed.state):
                self.assertIn(fact.key, closed.state.facts)
                self.assertIn(support, closed.state.proofs[fact.key])

    def test_checker_read_only_no_cache_or_old_value_reuse(self):
        before = self.a.state.canonical_digest()
        check_grounding(self.a, self.f.schema)
        self.assertEqual(before, self.a.state.canonical_digest())
        missing = check_grounding(self.initial_a, self.f.schema)
        self.assertIsNone(missing.outward)
        self.assertEqual(check_grounding(self.a, self.f.schema), self.ga)

    def test_no_output_insertion_into_gsc0(self):
        self.assertFalse(any(k[0] == 'GroundedOutwardStructure' for k in self.a.state.facts))
        self.assertFalse(any(k[0] == 'GroundedOutwardStructure' for k in self.b.state.facts))

    def test_no_selector_default_filling_or_execution_in_checker(self):
        source = Path(__file__).with_name('grounding.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        forbidden = {'max', 'min', 'choice', 'choices', 'sample', 'random', 'rank', 'select', 'execute', 'sleep'}
        for item in ast.walk(tree):
            if isinstance(item, ast.Call):
                name = item.func.id if isinstance(item.func, ast.Name) else item.func.attr if isinstance(item.func, ast.Attribute) else ''
                self.assertNotIn(name, forbidden)
            if isinstance(item, ast.Subscript):
                self.assertFalse(isinstance(item.value, ast.Attribute) and item.value.attr == 'values')
        # Exact tuple unpacking is the sole output-value extraction.
        self.assertIn('(unique_value,) = port.values', source)

    def test_production_import_isolation(self):
        root = Path(__file__).resolve().parents[2]
        for path in Path(__file__).parent.glob('*.py'):
            for item in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                modules = [a.name for a in item.names] if isinstance(item, ast.Import) else [item.module or ''] if isinstance(item, ast.ImportFrom) else []
                self.assertTrue(all(m.split('.')[0] not in ('individual', 'supervisor', 'minecraft') for m in modules))
        for folder in ('individual', 'supervisor', 'minecraft', 'bridge'):
            for path in (root / folder).rglob('*'):
                if path.is_file() and path.suffix in ('.py', '.js', '.mjs') and 'node_modules' not in path.parts:
                    self.assertNotIn('experimental.gsc1', path.read_text(encoding='utf-8'))

    def test_three_distinct_values_are_all_preserved(self):
        variable = Variable('out', 'T', 'gsc1', 'q')
        values = tuple(Value(str(n), 'T') for n in range(3))
        c = Condition((variable,), values, ())
        seeds = tuple(Seed(Binding(variable, v), (f'V{i}',)) for i, v in enumerate(values))
        result = check_grounding(Engine(c).run(seeds),
                                 OutwardSchema('O', (OutputPort('p', variable, 'T'),)))
        self.assertEqual(result.status, 'CONFLICT')
        self.assertEqual(set(result.ports[0].values), set(values))
        self.assertEqual(len(result.ports[0].evidence), 3)
        self.assertIsNone(result.outward)

    def test_same_name_old_scope_is_not_reused(self):
        old = Variable('p', 'T', 'gsc1', 'old')
        new = Variable('p', 'T', 'gsc1', 'new')
        value = Value('v', 'T')
        closed = Engine(Condition((old, new), (value,), ())).run((Seed(Binding(old, value), ('old-value',)),))
        result = check_grounding(closed, OutwardSchema('O', (OutputPort('p', new, 'T'),)))
        self.assertEqual(result.status, 'UNRESOLVED')
        self.assertIsNone(result.outward)

    def test_malformed_binding_is_invalid_not_ignored_or_repaired(self):
        state = self.a.state.clone()
        bad = Binding(self.f.schema.ports[0].variable, Value('B0', 'TypeB'))
        state.facts[bad.key] = bad
        result = check_grounding(replace(self.a, state=state), self.f.schema)
        self.assertEqual(result.status, 'INVALID')
        self.assertIsNone(result.outward)


if __name__ == '__main__':
    unittest.main()
