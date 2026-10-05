"""Independent TEST_ONLY specification checks, no Minecraft or A imports."""
from dataclasses import replace
from itertools import combinations_with_replacement
import ast
from pathlib import Path
import unittest
from .model import (Node, Variable, Value, Reference, Relation, Equality, Binding,
                    PortBinding, Conflict, Composite, Observation, Seed, difference,
                    Support, Witness, encode, incidence)
from .engine import Engine, Condition, Caps, RULES, CompositionIndex
from .fixtures import fixture, growth_fixture


def same_closure(test, left, right):
    test.assertTrue(left.closure_complete and right.closure_complete)
    test.assertEqual(left.state.facts, right.state.facts)
    test.assertEqual(left.state.proofs, right.state.proofs)
    test.assertEqual(left.state.roots, right.state.roots)
    test.assertEqual(left.state.input_records, right.state.input_records)
    test.assertEqual(left.state.composition.leaves, right.state.composition.leaves)
    test.assertEqual(left.state.composition.masks, right.state.composition.masks)
    test.assertEqual(left.state.composition.index, right.state.composition.index)


class GSC0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.condition, cls.history, cls.delta, cls.r4 = fixture()
        cls.engine = Engine(cls.condition)
        cls.initial = cls.engine.run(cls.history)
        cls.result = cls.engine.run(cls.delta, previous=cls.initial.state)

    def test_generation(self):
        self.assertTrue(self.initial.closure_complete)
        self.assertNotIn(self.r4.key, self.initial.state.facts)
        self.assertTrue(self.result.closure_complete)
        self.assertIn(self.r4.key, self.result.state.facts)

    def test_history_ablation(self):
        c, h, d, r4 = fixture(remove_history="R2")
        result = Engine(c).run(h + d)
        self.assertTrue(result.closure_complete)
        self.assertNotIn(r4.key, result.state.facts)

    def test_difference_ablation(self):
        for missing in ("D1", "D2"):
            c, h, d, r4 = fixture(remove_difference=missing)
            result = Engine(c).run(h + d)
            self.assertTrue(result.closure_complete)
            self.assertNotIn(r4.key, result.state.facts)

    def test_seed_queue_rule_order(self):
        # Each dimension changes actual enumeration order, not only report IDs.
        seeds = self.history + self.delta
        for seed_order in (seeds, seeds[::-1], seeds[::2] + seeds[1::2]):
            for queue, rules in (("forward", RULES), ("reverse", RULES[::-1]),
                                 ("interleaved", RULES[2:] + RULES[:2])):
                result = Engine(self.condition, queue_order=queue, rule_order=rules).run(seed_order)
                # Unchanged history roots: reconstruct initial and delta in a single
                # call, then compare actual contents/support indices exactly.
                same_closure(self, self.result, result)

    def test_idempotence(self):
        repeated = Engine(self.condition, queue_order="reverse", rule_order=RULES[::-1]).run(previous=self.result.state)
        same_closure(self, self.result, repeated)

    def test_conflict_preservation(self):
        # Small complete conflict fixture uses the same X/Y + D1/D2 mechanism,
        # both relation ports, and an extra Bind(Y,2). It is not a pruned run of
        # the much larger section-13 conflict stress fixture.
        x, y = Variable("X"), Variable("Y")
        values = tuple(Value(i) for i in (1, 2, 3))
        relation = Relation("P", "p", (x, y))
        c = Condition((x, y), values, (("p", ("node", "node")),))
        delta = difference(Observation("O0", ()), Observation("O1", (
            ("D1", Binding(y, values[2]), "D1"), ("D2", Equality(y, x), "D2"),
            ("D3", Binding(y, values[1]), "D3"))))
        result = Engine(c).run((Seed(relation, ("P",)),) + delta)
        self.assertTrue(result.closure_complete, result.limit)
        for variable in (x, y):
            for value in values[1:]:
                self.assertIn(Binding(variable, value).key, result.state.facts)
            self.assertNotIn(Binding(variable, values[0]).key, result.state.facts)
            self.assertIn(Conflict(variable, values[1:]).key, result.state.facts)
        for i, variable in enumerate((x, y)):
            for value in values[1:]:
                self.assertIn(PortBinding(relation, i, variable, value).key, result.state.facts)
        self.assertTrue(any(isinstance(f, Composite) and any(k[0] == "Conflict" for k in f.members)
                            for f in result.state.facts.values()))

    def test_no_semantic_shortcut(self):
        business = {key: f for key, f in self.result.state.facts.items() if isinstance(f, Relation)}
        self.assertEqual(business, {s.fact.key: s.fact for s in self.history})

    def test_resource_limit_atomic_batch(self):
        result = Engine(self.condition, Caps(structures=12)).run(self.history + self.delta)
        self.assertEqual(result.status, "RESOURCE_LIMIT")
        self.assertFalse(result.closure_complete)
        self.assertEqual(result.state.facts, {})  # entire initial batch rejected
        self.assertEqual(result.pending, self.history + self.delta)
        self.assertFalse(result.limit['closure_complete'])

    def test_resource_limit_preserves_history(self):
        before = self.initial.state.canonical_digest()
        result = Engine(self.condition, Caps(structures=len(self.initial.state.facts))).run(self.delta, previous=self.initial.state)
        self.assertEqual(result.status, "RESOURCE_LIMIT")
        self.assertEqual(before, self.initial.state.canonical_digest())
        self.assertEqual(result.state.facts, self.initial.state.facts)
        self.assertEqual(result.state.proofs, self.initial.state.proofs)

    def test_composition_limit_keeps_complete_committed_tiers(self):
        condition, seeds = growth_fixture(4)
        limited = []
        for order in ('forward', 'reverse'):
            result = Engine(condition, Caps(structures=75), queue_order=order).run(seeds)
            self.assertEqual(result.status, 'RESOURCE_LIMIT')
            self.assertFalse(result.closure_complete)
            self.assertIsNotNone(result.state.composition)
            composites = [f for f in result.state.facts.values() if isinstance(f, Composite)]
            self.assertTrue(composites)
            roots = result.state.root_witnesses()
            for fact in composites:
                self.assertTrue(roots[fact.key])
                self.assertTrue(next(result.state.direct_supports(fact.key), None))
            limited.append(result.state.canonical_digest())
        self.assertEqual(*limited)

    def test_workspace_operation_and_round_limits(self):
        for caps in (Caps(workspace_items=1), Caps(operations=1), Caps(rounds=1), Caps(provenance_entries=1)):
            result = Engine(self.condition, caps).run(self.history + self.delta)
            self.assertEqual(result.status, "RESOURCE_LIMIT")
            self.assertFalse(result.closure_complete)
            self.assertEqual(result.pending, self.history + self.delta)

    def test_all_derived_facts_have_finite_root_witness(self):
        roots = self.result.state.root_witnesses()
        self.assertTrue(all(roots.get(key) for key in self.result.state.facts))
        r4_roots = roots[self.r4.key]
        self.assertTrue({("Root", x) for x in ("R1", "R2", "R3", "D1", "D2")} <= r4_roots)

    def test_all_immediate_basic_rule_supports(self):
        state = self.result.state
        # Re-enumerating every applicable rule must introduce no fact/proof.
        for fact, proof in Engine(self.condition).consequences(state):
            self.assertIn(fact.key, state.facts)
            self.assertIn(proof, state.proofs[fact.key])
        # Explicit Eq(X,X) has reflexive, symmetric and transitive direct supports.
        x = Variable("X")
        rules = {p.rule for p in state.proofs[Equality(x, x).key]}
        self.assertTrue({"ALIGN-REFL", "ALIGN-SYM", "ALIGN-TRANS"} <= rules)

    def test_compose_index_against_independent_explicit_proof_graph(self):
        c, seeds = growth_fixture(2)
        result = Engine(c).run(seeds)
        self.assertTrue(result.closure_complete)
        index = result.state.composition
        supports = [({key}, key) for key in index.leaves]
        supports += [(set(f.members), f.key) for f in result.state.facts.values() if isinstance(f, Composite)]
        expected = {}
        eqs = {f.key for f in result.state.facts.values() if isinstance(f, Equality)}
        # Independent all-pairs port inspection, without the engine's bit masks
        # or counting formula; includes overlap and self supports.
        for (s, sk), (t, tk) in combinations_with_replacement(supports, 2):
            if len(s | t) < 2:
                continue
            for lk in s:
                for rk in t:
                    for li, ln in incidence(result.state.facts[lk]):
                        for ri, rn in incidence(result.state.facts[rk]):
                            if Equality(ln, rn).key not in eqs:
                                continue
                            ends = sorted(((lk, li), (rk, ri)), key=lambda p: (encode(p[0]), p[1]))
                            witness = Witness(ends[0][0], ends[0][1], ends[1][0], ends[1][1])
                            key = Composite(tuple(s | t)).key
                            expected.setdefault(key, set()).add(Support("COMPOSE", (sk, tk, witness.key)))
        for key, proofs in expected.items():
            self.assertEqual(set(result.state.direct_supports(key)), proofs)
        n = sum(map(len, expected.values()))
        e = sum(len(p.premises) for proofs in expected.values() for p in proofs)
        self.assertEqual(index.counts(), (n, e))

    def test_connected_subsets_independent_recursive_union_oracle(self):
        c, seeds = growth_fixture(2)
        result = Engine(c).run(seeds)
        index = result.state.composition
        supports = {frozenset((key,)) for key in index.leaves}
        while True:
            expanded = set(supports)
            for s, t in combinations_with_replacement(tuple(supports), 2):
                if any((w.left_leaf in s and w.right_leaf in t) or (w.left_leaf in t and w.right_leaf in s)
                       for w, _, _ in index.index):
                    expanded.add(s | t)
            if expanded == supports:
                break
            supports = expanded
        actual = {frozenset(index.member_keys(m)) for m in index.masks}
        self.assertEqual(actual, supports)

    def test_flatten_and_shared_witness_completeness(self):
        r1, r2, r3 = (s.fact for s in self.history)
        self.assertEqual(Composite((Composite((r1, r2)), r3, r1)), Composite((r3, r2, r1)))
        index = self.result.state.composition
        shared = index.shared(self.r4.key)
        self.assertTrue(any(w.left_leaf == r1.key and w.right_leaf == r2.key for w in shared))
        self.assertTrue(any(w.left_leaf == r2.key and w.right_leaf == r3.key for w in shared))
        for w in shared:
            self.assertIn(w.key, self.result.state.proofs)

    def test_exact_reference_no_similar_identity_alignment(self):
        x, y = Variable("X"), Variable("Y")
        ref = Reference("opaque", x)
        c = Condition((x, y), (Value(3),), (("p", ("reference",)),), (ref,))
        r = Relation("R", "p", (ref,))
        result = Engine(c).run((Seed(r, ("R",)), Seed(Binding(x, Value(3)), ("B",))))
        self.assertTrue(result.closure_complete)
        self.assertIn(PortBinding(r, 0, x, Value(3)).key, result.state.facts)
        self.assertNotIn(Equality(x, y).key, result.state.facts)
        with self.assertRaises(ValueError):
            Engine(c).run((Seed(Relation("Bad", "p", (Reference("opaque", y),)), ("bad",)),))

    def test_identity_type_and_domain_failures(self):
        with self.assertRaises(ValueError): Value(True)
        with self.assertRaises(ValueError): Value(1.0)
        x = Variable("X")
        with self.assertRaises(ValueError): Engine(self.condition).run((Seed(Binding(x, Value(4)), ("bad",)),))
        with self.assertRaises(ValueError): Engine(self.condition).run((Seed(Equality(Node("A"), x), ("bad",)),))
        r1 = self.history[0].fact
        with self.assertRaises(ValueError):
            Engine(self.condition).run((self.history[0], Seed(replace(r1, ports=r1.ports[::-1]), ("bad",))))
        with self.assertRaises(ValueError):
            Engine(replace(self.condition, nodes=(*self.condition.nodes, replace(x, value_type="Other")))).run()

    def test_difference_changed_removed_unobserved_and_scope(self):
        a, b = Variable("V", scope="t0"), Variable("V", scope="t1")
        before = Observation("O0", (("field", Binding(a, Value(1)), "old"),))
        after = Observation("O1", (("field", Binding(b, Value(2)), "new"),))
        delta = difference(before, after)
        self.assertEqual(delta[0].fact.kind, "Changed")
        c = Condition((a, b), (Value(1), Value(2)), ())
        result = Engine(c).run((Seed(Binding(a, Value(1)), ("old",)),) + delta)
        self.assertTrue(result.closure_complete)
        self.assertFalse(any(isinstance(f, Conflict) for f in result.state.facts.values()))
        self.assertEqual(difference(before, Observation("O2", ()))[0].fact.kind, "Removed")
        self.assertEqual(difference(before, Observation("O2", (), False))[0].fact.kind, "Unobserved")
        self.assertEqual(difference(before, before), ())
        removed = Engine(c).run(difference(before, Observation("O2", ())), previous=result.state)
        self.assertIn(Binding(a, Value(1)).key, removed.state.facts)

    def test_input_monotonicity_and_cumulative_envelope(self):
        self.assertTrue(self.initial.state.facts.keys() <= self.result.state.facts.keys())
        limit = Engine(self.condition, Caps(inputs=len(self.history))).run(self.delta, previous=self.initial.state)
        self.assertEqual(limit.status, "RESOURCE_LIMIT")
        self.assertEqual(limit.limit['resource_port'], "inputs")
        self.assertEqual(self.initial.state.facts, limit.state.facts)

    def test_same_fact_new_source_preserves_support_without_fake_difference(self):
        x = Variable('X')
        fact = Binding(x, Value(3))
        c = Condition((x,), (Value(3),), ())
        initial = Engine(c).run((Seed(fact, ('old',)),))
        delta = difference(Observation('O0', (('v', fact, 'old'),)),
                           Observation('O1', (('v', fact, 'new'),)))
        self.assertEqual(len(delta), 1)
        self.assertEqual(delta[0].fact, fact)
        result = Engine(c).run(delta, previous=initial.state)
        self.assertTrue(result.closure_complete)
        self.assertEqual(result.state.facts, initial.state.facts)
        self.assertTrue({('Root', 'old'), ('Root', 'new')} <= result.state.root_witnesses()[fact.key])

    def test_same_value_does_not_unify_and_port_binding_requires_declared_target(self):
        x, y = Variable('X'), Variable('Y')
        value = Value(3)
        relation = Relation('P', 'p', (x,))
        c = Condition((x, y), (value,), (('p', ('node',)),))
        result = Engine(c).run((Seed(relation, ('R',)), Seed(Binding(x, value), ('X3',)),
                                Seed(Binding(y, value), ('Y3',))))
        self.assertTrue(result.closure_complete)
        self.assertNotIn(Equality(x, y).key, result.state.facts)
        with self.assertRaises(ValueError):
            Engine(c).run((Seed(PortBinding(relation, 0, y, value), ('invalid',)),))

    def test_import_isolation(self):
        root = Path(__file__).resolve().parents[2]
        prototype = Path(__file__).parent
        for path in prototype.glob('*.py'):
            for item in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(item, ast.Import):
                    self.assertFalse(any(a.name.split('.')[0] in ('individual', 'minecraft', 'supervisor') for a in item.names))
                if isinstance(item, ast.ImportFrom):
                    self.assertNotIn((item.module or '').split('.')[0], ('individual', 'minecraft', 'supervisor'))
        for folder in ('individual', 'supervisor'):
            for path in (root / folder).glob('*.py'):
                self.assertNotIn('experimental.gsc0', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
