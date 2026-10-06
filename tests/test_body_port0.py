"""New BPC-0 controls only; does not import or revalidate Successor-0."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from experimental.body_port0.prototype import (
    BodyPort, Sample, Member, Shared, Organization, Pattern, RecordingBody,
    catalog_port, bootstrap, encode_execution, form, consume)


def witness(code=36, identity='receipt-a', scope='test-epoch-1'):
    body = RecordingBody(Sample(1, scope, ((101, 2),)))
    receipt = bootstrap(body, code, ((101, 5),), identity)
    material, current = encode_execution(receipt)
    return body, receipt, material, current


class BodyPort0Tests(unittest.TestCase):
    def test_new_connection_and_complete_expression(self):
        _, receipt, m, c = witness()
        edge = Shared(frozenset((c, receipt.port)))
        self.assertNotIn(edge, m.facts)
        s = form(m)
        self.assertIn(edge, s.facts)
        self.assertEqual(consume(s, c), {'code': 36, 'parameters': {}})

    def test_necessary_input_connection_ablation(self):
        _, e, m, c = witness()
        m = replace(m, facts=m.facts - {Member(e.identity, e.port)})
        self.assertIsNone(consume(form(m), c))

    def test_formed_organization_ablation(self):
        _, _, m, c = witness()
        self.assertIsNotNone(consume(form(m), c))
        self.assertIsNone(consume(None, c))

    def test_formed_link_ablation_without_recomputation(self):
        _, e, m, c = witness()
        s = form(m)
        screened = replace(s, facts=s.facts - {Shared(frozenset((c, e.port)))})
        with patch('experimental.body_port0.prototype.form', side_effect=AssertionError('recompute')):
            self.assertIsNone(consume(screened, c))

    def test_every_necessary_support_ablation(self):
        _, _, m, c = witness()
        s = form(m)
        for edge in s.supports:
            if edge.rule != 'INPUT' or isinstance(edge.conclusion, (BodyPort, Sample)):
                with self.subTest(edge=edge):
                    self.assertIsNone(consume(replace(s, supports=s.supports - {edge}), c))

    def test_no_sampler_or_binder_even_on_missing_expression(self):
        with patch('individual.formal_l0.select_uniform_action', side_effect=AssertionError('sampler')), \
                patch('individual.action_space.bind_parameters', side_effect=AssertionError('binder')):
            body, _, m, c = witness()
            expression = consume(form(m), c)
            body.execute(expression, ((101, 8),))
            self.assertIsNone(consume(None, c))

    def test_second_execution_uses_formed_expression(self):
        body, _, m, c = witness()
        expression = consume(form(m), c)
        with patch('experimental.body_port0.prototype.bootstrap', side_effect=AssertionError('bootstrap again')):
            before, after = body.execute(expression, ((101, 8),))
        self.assertEqual(len(body.commands), 2)
        self.assertEqual(body.commands[-1][0].code, expression['code'])
        self.assertEqual((before.sequence, after.sequence), (2, 3))

    def test_renewed_experience_reenters_formation(self):
        from experimental.body_port0.prototype import Execution
        body, _, m, c = witness()
        expression = consume(form(m), c)
        before, after = body.execute(expression, ((101, 8),))
        record = Execution('second-receipt', catalog_port(expression['code']), before, after,
                           source='TEST_ONLY_FORMED_CONNECTION')
        renewed, nc = encode_execution(record)
        accumulated = Organization(m.facts | renewed.facts, m.supports | renewed.supports, False)
        self.assertNotEqual(c, nc)
        self.assertEqual(consume(form(accumulated), nc), expression)

    def test_changed_history_changes_port_same_internal_structure(self):
        _, _, a, ca = witness(36)
        _, _, b, cb = witness(46)
        self.assertEqual(ca, cb)
        self.assertEqual(consume(form(a), ca)['code'], 36)
        self.assertEqual(consume(form(b), cb)['code'], 46)

    def test_conflicting_ports_no_external_arbitration(self):
        _, _, a, c = witness(36)
        _, _, b, _ = witness(46, 'receipt-b')
        s = form(Organization(a.facts | b.facts, a.supports | b.supports, False))
        self.assertIsNone(consume(s, c))

    def test_disconnected_distractor_changes(self):
        _, e, a, c = witness()
        for count in (1, 10, 100):
            facts, supports = set(a.facts), set(a.supports)
            for i in range(count):
                _, _, d, _ = witness(46, f'd-{i}', f'other-scope-{i}')
                facts.update(d.facts)
                supports.update(d.supports)
            s = form(Organization(frozenset(facts), frozenset(supports), False))
            edge = Shared(frozenset((c, e.port)))
            self.assertEqual(consume(s, c), consume(form(a), c))
            self.assertEqual({p for p in s.supports if p.conclusion == edge},
                             {p for p in form(a).supports if p.conclusion == edge})

    def test_port_identity_native_not_translation_table(self):
        from individual.action_space import DEFINITIONS, CATALOG_DATA
        for code, d in DEFINITIONS.items():
            if d.get('formal_enabled') and not d['parameters']:
                p = catalog_port(code)
                self.assertEqual(p, BodyPort(CATALOG_DATA['version'], code))
        self.assertEqual(set(BodyPort.__dataclass_fields__), {'version', 'code'})

    def test_required_parameters_not_filled_or_defaulted(self):
        with self.assertRaises(ValueError):
            catalog_port(34)

    def test_incomplete_or_wrong_query_no_expression(self):
        _, _, m, c = witness()
        self.assertIsNone(consume(m, c))
        self.assertIsNone(consume(form(m), Pattern('absent', c.changes)))

    def test_sampling_gap_and_unexecuted_history_rejected(self):
        _, e, _, _ = witness()
        for bad in (replace(e, completed=False), replace(e, source='unattributed'),
                    replace(e, after=replace(e.after, sequence=7)),
                    replace(e, after=replace(e.after, scope='changed')), replace(e, parameters=(('x', 1),))):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                encode_execution(bad)

    def test_prebuilt_shared_answer_rejected(self):
        _, e, m, c = witness()
        with self.assertRaises(ValueError):
            form(replace(m, facts=m.facts | {Shared(frozenset((c, e.port)))}))

    def test_general_incidence_rule_not_body_specific(self):
        from experimental.body_port0.prototype import Support
        a, b = Pattern('a', ()), Pattern('b', ())
        ma, mb = Member('g', a), Member('g', b)
        facts = frozenset((a, b, ma, mb))
        proofs = frozenset(Support(f, 'INPUT', frozenset()) for f in facts)
        self.assertIn(Shared(frozenset((a, b))), form(Organization(facts, proofs, False)).facts)


if __name__ == '__main__':
    unittest.main()
