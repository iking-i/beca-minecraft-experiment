"""Frozen-in-code CEC0 T1-T6 and negative controls. No A/Minecraft execution."""
import ast
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from experimental.gsc0.model import Witness, encode
from .codec import (canonical, clean_records, control_node, encode_records, produce, query,
                    record_from_events, shape_id)
from .consumer import consume, screen_witnesses
from .fixtures import events, fixture


class CEC0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fixture()
        cls.qc = query(cls.records[0].relation.ports[1])
        cls.qy = query(cls.records[0].relation.ports[2])
        cls.encoded = encode_records(cls.records, (cls.qc, cls.qy))
        cls.organization = produce(cls.encoded)

    def shared(self, a, ai, b, bi):
        return tuple(f for f in self.organization.facts if isinstance(f, Witness) and
                     ((f.left_leaf, f.left_port, f.right_leaf, f.right_port) == (a.key, ai, b.key, bi) or
                      (f.right_leaf, f.right_port, f.left_leaf, f.left_port) == (a.key, ai, b.key, bi)))

    def test_T1_control_identity(self):
        self.assertEqual(self.organization.status, 'COMPLETE', self.organization.statistics_json)
        a, b = (r.relation for r in self.records[:2])
        self.assertNotEqual(a.ports[0], b.ports[0])
        self.assertEqual(a.ports[1], b.ports[1])
        self.assertTrue(self.shared(a, 1, b, 1))

    def test_T2_consequence_identity(self):
        a, b = self.records[0].relation, self.records[2].relation
        self.assertEqual(a.ports[2], b.ports[2])
        self.assertTrue(self.shared(a, 2, b, 2))

    def test_T3_forward_read_all(self):
        read = consume(self.organization, self.qc)
        self.assertEqual(set(read.endpoints), {self.records[i].relation.ports[2] for i in (0, 1)})
        self.assertEqual(len(read.record_keys), 2)

    def test_T4_reverse_read_all(self):
        read = consume(self.organization, self.qy)
        self.assertEqual(set(read.endpoints), {self.records[i].relation.ports[1] for i in (0, 2)})
        self.assertEqual(len(read.record_keys), 2)

    def test_T5_detached_formed_structure_screen(self):
        for q in (self.qc, self.qy):
            original = consume(self.organization, q)
            screened = screen_witnesses(self.organization, original.witness_keys)
            self.assertEqual(screened.input, self.organization.input)
            self.assertEqual(screened.sources, self.organization.sources)
            self.assertEqual(screened.supports, self.organization.supports)
            with patch('experimental.gsc0.engine.Engine.run', side_effect=AssertionError('No recomputation')):
                self.assertFalse(consume(screened, q).endpoints)
                keys = [w for r, w in original.endpoint_evidence[0][1]]
                partial = consume(screen_witnesses(self.organization, keys), q)
            self.assertEqual(len(partial.endpoints), len(original.endpoints) - 1)
            self.assertEqual(len(consume(self.organization, q).endpoints), 2)

    def test_T6_non_prescription(self):
        from . import codec, consumer
        forbidden = {'random', 'reward', 'score', 'selector', 'rank', 'nearest', 'best',
                     'similarity', 'fallback', 'MinecraftBridge', 'ACore', 'execute_action',
                     'select_uniform_action', 'bind_parameters'}
        for module in (codec, consumer):
            tree = ast.parse(Path(module.__file__).read_text(encoding='utf8'))
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            self.assertFalse(names & forbidden)
        for seed in self.encoded.seeds:
            self.assertIn(seed.fact.type_id, ('cec.record', 'cec.query.control', 'cec.query.consequence'))
        for f in self.organization.facts:
            if hasattr(f, 'type_id'):
                self.assertIn(f.type_id, ('cec.record', 'cec.query.control', 'cec.query.consequence'))
        # Erase raw source/producer data from the consumer view: answers are unchanged.
        view = replace(self.organization, sources=(), input=None)
        for q in (self.qc, self.qy):
            self.assertEqual(consume(view, q), consume(self.organization, q))

    def test_negative_nonidentical_control_and_consequence(self):
        a, b = self.records[0].relation, self.records[3].relation
        self.assertNotEqual(a.ports[1], b.ports[1])
        self.assertNotEqual(a.ports[2], b.ports[2])
        self.assertFalse(self.shared(a, 1, b, 1))
        self.assertFalse(self.shared(a, 2, b, 2))
        self.assertNotIn(b.key, consume(self.organization, self.qc).record_keys)
        self.assertNotIn(b.key, consume(self.organization, self.qy).record_keys)

    def test_negative_order_and_source_identity_not_correspondence(self):
        reordered = replace(self.encoded, seeds=tuple(reversed(self.encoded.seeds)))
        changed = produce(reordered)
        self.assertEqual(changed.status, 'COMPLETE')
        self.assertEqual({f.key for f in changed.facts}, {f.key for f in self.organization.facts})
        for q in (self.qc, self.qy):
            self.assertEqual(consume(changed, q).endpoints, consume(self.organization, q).endpoints)
        modified = []
        for r in self.records:
            texts = []
            for text in r.source_events_json:
                e = json.loads(text); e['event_id'] = 'renamed-' + e['event_id']; e['timestamp'] = 'TEST_ONLY-close-time'
                texts.append(canonical(e))
            modified.append(replace(r, source_events_json=tuple(reversed(texts))))
        renamed = produce(encode_records(modified, (self.qc, self.qy)))
        self.assertEqual({f.key for f in renamed.facts}, {f.key for f in self.organization.facts})

    def test_parameter_contamination_rejected(self):
        a = record_from_events(*events(1, 0, 8, 1, {'yaw_delta': 0, 'pitch_delta': 0}), 2)
        b = record_from_events(*events(2, 5, 8, 7, {'yaw_delta': 0.15, 'pitch_delta': 0}), 2)
        with self.assertRaisesRegex(ValueError, 'PARAMETER_CONTAMINATION'):
            encode_records((a, b), (query(a.relation.ports[1]),))

    def test_negative_record_count_does_not_create_query_connection(self):
        extra = record_from_events(*events(5, 11, 12, 15), 2)
        org = produce(encode_records((*self.records, extra), (self.qc, self.qy)))
        self.assertEqual(org.status, 'COMPLETE')
        for q in (self.qc, self.qy):
            self.assertEqual(consume(org, q).endpoints, consume(self.organization, q).endpoints)
            self.assertNotIn(extra.relation.key, consume(org, q).record_keys)

    def test_record_identity_is_not_control_or_consequence_identity(self):
        rows = tuple(replace(r, relation=replace(r.relation, name='opaque-renamed-' + r.relation.name))
                     for r in self.records)
        org = produce(encode_records(rows, (self.qc, self.qy)))
        self.assertEqual(org.status, 'COMPLETE')
        for q in (self.qc, self.qy):
            self.assertEqual(consume(org, q).endpoints, consume(self.organization, q).endpoints)

    def test_identical_nonempty_parameters_allowed(self):
        rows = tuple(record_from_events(*events(i, u, 8, y, {'yaw_delta': 0, 'pitch_delta': 0}), 2)
                     for i, u, y in ((1, 0, 1), (2, 5, 7)))
        self.assertEqual(len(clean_records(rows)), 2)

    def test_catalog_version_and_code_exactness(self):
        self.assertEqual(control_node(2, 3), control_node(2, 3))
        self.assertNotEqual(control_node(2, 3), control_node(3, 3))
        self.assertNotEqual(control_node(2, 3), control_node(2, 4))
        for bad in (-1, True, '3'):
            with self.assertRaises(ValueError): control_node(2, bad)

    def test_missing_and_false_provenance_rejected(self):
        e = events(1, 0, 3, 1)
        for index, key, value in ((0, 'outcome', 'fake'), (1, 'action_code', 4), (2, 'status', 'failed')):
            changed = json.loads(canonical(e)); changed[index]['payload'][key] = value
            with self.assertRaises(ValueError): record_from_events(*changed, 2)

    def test_every_read_path_has_direct_and_raw_root_evidence(self):
        sources = dict(self.organization.sources)
        facts = {f.key:f for f in self.organization.facts}
        support_map = dict(self.organization.supports)
        for q in (self.qc, self.qy):
            read = consume(self.organization, q)
            for _, pairs in read.endpoint_evidence:
                for r, w in pairs:
                    self.assertEqual(facts[r].type_id, 'cec.record')
                    self.assertTrue(any(rule == 'SHARED' for rule, _ in support_map[w]))
                    roots = dict(read.root_witnesses)[w]
                    kinds = {json.loads(sources[root[1]])['event_type'] for root in roots
                             if root[0] == 'Root' and root[1].startswith('EVENT:')}
                    self.assertEqual(kinds, {'EXPERIENCE_FORMED', 'ACTION_REQUESTED', 'ACTION_EXECUTED', 'OBSERVATION_FRAME'})
                    source_frames = [json.loads(sources[root[1]]) for root in roots
                                     if root[0] == 'Root' and root[1].startswith('EVENT:') and json.loads(sources[root[1]])['event_type']=='OBSERVATION_FRAME']
                    self.assertEqual(len(source_frames), 2)

    def test_incomplete_never_read_as_complete(self):
        from experimental.gsc0.engine import Caps
        limited = produce(self.encoded, Caps(structures=1))
        self.assertEqual(limited.status, 'RESOURCE_LIMIT')
        self.assertFalse(limited.facts)
        self.assertEqual(consume(limited, self.qc).status, 'RESOURCE_LIMIT')

    def test_pattern_codec_matches_baseline_helper(self):
        from individual.structure import pattern_id
        delta = events(1, 0, 3, 1)[3]['payload']['delta']
        self.assertEqual(shape_id(delta), pattern_id(delta))


if __name__ == '__main__':
    unittest.main()
