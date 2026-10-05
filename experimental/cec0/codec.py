"""TEST_ONLY mechanical encoding. Directly imports the frozen GSC-0 implementation."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from experimental.gsc0.engine import Caps, Condition, Engine
from experimental.gsc0.model import Node, Relation, Seed, encode

VERSION = 'CEC-0-TEST_ONLY-v1'
SIGNATURES = (('cec.record', ('node', 'node', 'node')),
              ('cec.query.control', ('node',)), ('cec.query.consequence', ('node',)))
CATALOG = json.loads((Path(__file__).resolve().parents[2] / 'minecraft/action-space.json').read_text(encoding='utf8'))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def shape_id(delta):
    """The baseline pattern_id serialization, checked against the actual helper in tests."""
    shape = [(c['channel_id'], c['kind']) for c in delta['changes']]
    return 'U-' + sha256(json.dumps(shape, separators=(',', ':')).encode()).hexdigest()[:20]


def control_node(action_space_version, code):
    if type(action_space_version) is not int or type(code) is not int or code < 0:
        raise ValueError('Exact numeric catalog identity required')
    return Node(canonical((action_space_version, code)), VERSION, 'catalog', 'control')


def unit_node(identity, scope, role):
    if role not in ('context', 'consequence') or not isinstance(identity, str):
        raise ValueError('Invalid opaque unit endpoint')
    return Node(identity, VERSION, scope, role)


@dataclass(frozen=True)
class Record:
    relation: Relation
    parameters_json: str
    source_events_json: tuple

    @property
    def sources(self):
        return tuple('EVENT:' + json.loads(x)['event_id'] for x in self.source_events_json)


def record_from_events(experience, requested, executed, before, after, action_space_version):
    events = (experience, requested, executed, before, after)
    if [e['event_type'] for e in events] != ['EXPERIENCE_FORMED', 'ACTION_REQUESTED',
            'ACTION_EXECUTED', 'OBSERVATION_FRAME', 'OBSERVATION_FRAME']:
        raise ValueError('Missing exact source event kinds')
    if len({e['event_id'] for e in events}) != 5 or len({e['individual_id'] for e in events}) != 1:
        raise ValueError('Duplicate or cross-individual source')
    x, req, done, a, b = (e['payload'] for e in events)
    code = x['action_code']
    if x['causality'] != 'temporal_association_only':
        raise ValueError('Only temporal association evidence is legal')
    if x['frame_ids'] != [a['frame_id'], b['frame_id']] or a['sequence_id'] >= b['sequence_id']:
        raise ValueError('Before/after frame boundary mismatch')
    if (a['encoding_namespace'], a['body_epoch']) != (b['encoding_namespace'], b['body_epoch']):
        raise ValueError('Carrier sampling gap')
    if x['antecedent'] != shape_id(a['delta']) or x['outcome'] != shape_id(b['delta']):
        raise ValueError('Outcome/context not the recorded pattern')
    if x['root'] != f"{x['antecedent']}:{code}":
        raise ValueError('Recorded temporal root mismatch')
    if x['action_ids'] != [req['action_id']] or done['action_id'] != req['action_id']:
        raise ValueError('Ambiguous or missing actual control')
    if x['action_statuses'] != ['executed'] or req['status'] != 'requested' or done['status'] != 'executed':
        raise ValueError('No acknowledged executed control')
    if req['action_code'] != code or done['action_code'] != code:
        raise ValueError('Control code differs from action record')
    if req['method'] != 'perform' or done['method'] != 'perform':
        raise ValueError('No formal numeric carrier request')
    p = req['args']['parameters']
    if req['args']['code'] != code or done['args'] != req['args'] or x['action_parameters'] != [p]:
        raise ValueError('Parameter evidence mismatch')
    definitions = {d['code']: d for d in CATALOG['actions']}
    if action_space_version != CATALOG['version'] or code not in definitions or not definitions[code].get('formal_enabled', True):
        raise ValueError('Control not in the frozen formal numeric catalog')
    schema = definitions[code]['parameters']
    if not isinstance(p, dict) or set(p) - set(schema):
        raise ValueError('Unknown parameter fields')
    for key, s in schema.items():
        if key not in p and s.get('optional'):
            continue
        v = p.get(key)
        ok = ((s['type']=='integer' and type(v) is int) or
              (s['type']=='number' and type(v) in (int, float)) or
              (s['type']=='string' and type(v) is str and bool(v)))
        if not ok or ('minimum' in s and v < s['minimum']) or ('maximum' in s and v > s['maximum']):
            raise ValueError('Parameter outside frozen carrier schema')
    if not before['event_sequence'] < requested['event_sequence'] < executed['event_sequence'] < experience['event_sequence']:
        raise ValueError('Action/source order mismatch')
    if not executed['event_sequence'] < after['event_sequence']:
        raise ValueError('Consequence did not follow the control')
    scope = canonical((experience['individual_id'], a['encoding_namespace'], a['body_epoch']))
    endpoints = (unit_node(x['antecedent'], scope, 'context'), control_node(action_space_version, code),
                 unit_node(x['outcome'], scope, 'consequence'))
    relation = Relation(x['experience_id'], 'cec.record', endpoints, VERSION, scope)
    return Record(relation, canonical(p), tuple(canonical(e) for e in events))


def clean_records(records):
    """One parameter stratum only. Never silently pool different parameter content."""
    records = tuple(records)
    if len({r.parameters_json for r in records}) > 1:
        raise ValueError('PARAMETER_CONTAMINATION')
    if len({r.relation.key for r in records}) != len(records):
        raise ValueError('Duplicate experience identity')
    scopes = {r.relation.scope for r in records}
    if len(scopes) > 1:
        raise ValueError('History crosses individual/encoding/epoch scope')
    return records


def query(endpoint):
    if endpoint.kind not in ('control', 'consequence'):
        raise ValueError('Only exact control/consequence queries')
    return Relation('query:' + encode(endpoint.key), 'cec.query.' + endpoint.kind,
                    (endpoint,), VERSION, 'query')


@dataclass(frozen=True)
class Input:
    condition: Condition
    seeds: tuple
    queries: tuple
    sources: tuple


def encode_records(records, queries):
    records = clean_records(records)
    queries = tuple(queries)
    nodes = {n.key: n for r in records for n in r.relation.ports}
    for q in queries:
        if q != query(q.ports[0]):
            raise ValueError('Query must preserve exact endpoint identity')
        nodes[q.ports[0].key] = q.ports[0]
    sources = {}
    for r in records:
        for text in r.source_events_json:
            e = json.loads(text); key = 'EVENT:' + e['event_id']
            if key in sources and sources[key] != text:
                raise ValueError('Conflicting provenance identity')
            sources[key] = text
    sources.update(('QUERY:' + encode(q.key), canonical({'category': 'TEST_ONLY_EXACT_QUERY', 'key': q.key})) for q in queries)
    condition = Condition(tuple(sorted(nodes.values(), key=lambda n: encode(n.key))), (), SIGNATURES)
    seeds = tuple(Seed(r.relation, r.sources) for r in records) + tuple(
        Seed(q, ('QUERY:' + encode(q.key),)) for q in queries)
    return Input(condition, seeds, queries, tuple(sorted(sources.items())))


@dataclass(frozen=True)
class Organization:
    status: str
    facts: tuple
    supports: tuple
    roots: tuple
    sources: tuple
    input: Input
    statistics_json: str


def produce(encoded, caps=None):
    result = Engine(encoded.condition, caps or Caps()).run(encoded.seeds)
    # Incomplete graphs cannot be consumed as formed COMPLETE organizations.
    if not result.closure_complete:
        return Organization(result.status, (), (), (), encoded.sources, encoded,
                            canonical({'operations': result.operations, 'rounds': result.closure_rounds, 'limit': result.limit}))
    from experimental.gsc0.model import Composite
    state = result.state
    facts = tuple(sorted((f for f in state.facts.values() if not isinstance(f, Composite)), key=lambda f: encode(f.key)))
    witnesses = state.root_witnesses()
    supports = tuple((f.key, tuple((s.rule, s.premises) for s in sorted(state.direct_supports(f.key), key=lambda s: encode((s.rule, s.premises))))) for f in facts)
    roots = tuple((f.key, tuple(sorted(witnesses[f.key], key=encode))) for f in facts)
    return Organization(result.status, facts, supports, roots, encoded.sources, encoded,
                        canonical({'operations': result.operations, 'rounds': result.closure_rounds,
                                   'facts_including_composites': len(state.facts)}))
