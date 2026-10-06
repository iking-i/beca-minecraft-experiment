"""Independent Successor-0 controls; no formal A or Minecraft execution."""
from dataclasses import replace
import inspect
import unittest
from unittest.mock import patch
from experimental.successor0.consumer import consume
from experimental.successor0.engine import form
from experimental.successor0.model import Bind, Demand, Port, RequireBound, Transfer, Value
from experimental.successor0.validation import CRITERIA, fixture, run_validation, support_ablation


class Successor0Tests(unittest.TestCase):
    def test_ten_acceptance_conditions(self):
        report = run_validation()
        for criterion in CRITERIA:
            with self.subTest(criterion=criterion):
                self.assertEqual(report["criteria"][criterion], "PASS")
        self.assertEqual(report["status"], "PASS")

    def test_exact_identity_not_type_matching(self):
        h, r = fixture()
        h = h - {Transfer("m", "q")} | {Port("other", "T", "test"), Transfer("m", "other")}
        self.assertEqual(form(h, r).status, "UNRESOLVED")

    def test_multiple_producers_never_selects(self):
        h, r = fixture()
        for material in (list(h | {Transfer("u", "q")}), list(reversed(list(h | {Transfer("u", "q")})))):
            self.assertEqual(form(material, r).status, "INVALID_FIXTURE")

    def test_cycle_rejected(self):
        h, r = fixture()
        self.assertEqual(form(h | {Transfer("q", "u")}, r).status, "INVALID_FIXTURE")

    def test_invalid_transfer_type(self):
        h, r = fixture()
        h = h - {Port("m", "T", "test")} | {Port("m", "other", "test")}
        self.assertEqual(form(h, r).status, "INVALID_FIXTURE")

    def test_invalid_scope(self):
        h, _ = fixture()
        self.assertEqual(form(h, RequireBound("q", "T", "other")).status, "INVALID_FIXTURE")

    def test_invalid_seed_type(self):
        h, r = fixture()
        h = h - {Value("V", "T", "test")} | {Value("V", "other", "test")}
        self.assertEqual(form(h, r).status, "INVALID_FIXTURE")

    def test_conflict_preserved_no_arbitration(self):
        h, r = fixture()
        result = form(h | {Value("W", "T", "test"), Bind("u", "W")}, r)
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertTrue({Bind("u", "V"), Bind("u", "W")} <= result.organization.facts)
        self.assertNotIn(Bind("q", "V"), result.organization.facts)
        self.assertEqual(consume(result.organization, "q").status, "UNRESOLVED")

    def test_already_bound_requirement(self):
        h, r = fixture()
        result = form(h | {Bind("q", "V")}, r)
        self.assertEqual(consume(result.organization, "q").value, "V")

    def test_input_order_idempotent_registration(self):
        h, r = fixture()
        a = form(h, r)
        b = form(list(reversed(list(h))) * 2, r)
        self.assertEqual(a.organization, b.organization)
        self.assertEqual(a.organization.identity, b.organization.identity)

    def test_consumer_does_not_recompute(self):
        h, r = fixture()
        s = form(h, r).organization
        with patch("experimental.successor0.engine.form", side_effect=AssertionError("recompute")):
            self.assertEqual(consume(s, "q").value, "V")
            self.assertEqual(consume(support_ablation(s), "q").status, "UNRESOLVED")
            self.assertEqual(consume(None, "q").status, "UNRESOLVED")
        self.assertEqual(tuple(inspect.signature(consume).parameters), ("organization_handle", "q"))

    def test_all_necessary_support_edges_consumed(self):
        h, r = fixture()
        s = form(h, r).organization
        for edge in s.supports:
            with self.subTest(edge=edge):
                screened = replace(s, supports=s.supports - {edge})
                self.assertEqual(consume(screened, "q").status, "UNRESOLVED")

    def test_status_not_complete_is_not_success(self):
        h, r = fixture()
        s = form(h, r).organization
        for status in ("UNRESOLVED", "RESOURCE_LIMIT", "INVALID_FIXTURE"):
            self.assertEqual(consume(replace(s, status=status), "q").status, "UNRESOLVED")

    def test_wrong_query_unresolved(self):
        h, r = fixture()
        self.assertEqual(consume(form(h, r).organization, "m").status, "UNRESOLVED")

    def test_missing_fact_unresolved(self):
        h, r = fixture()
        s = form(h, r).organization
        self.assertEqual(consume(replace(s, facts=s.facts - {Bind("m", "V")}), "q").status, "UNRESOLVED")

    def test_every_derived_fact_has_direct_support(self):
        h, r = fixture()
        s = form(h, r).organization
        for fact in s.facts:
            self.assertTrue(any(e.conclusion == fact for e in s.supports))
        self.assertTrue(all(e.premises <= s.facts for e in s.supports))


if __name__ == "__main__":
    unittest.main()
