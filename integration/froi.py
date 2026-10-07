"""FROI-1 mechanical integration. The imported GSC-0 rules remain frozen.

History is append-only input material, not a retained materialized closure.
Consumers have only immutable formed facts/supports, never raw-history answers.
"""
from contextlib import closing
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from experimental.gsc0.engine import Caps, Condition, Engine
from experimental.gsc0.model import (Node, Variable, Value, Relation, Binding,
    Equality, PortBinding, Conflict, Witness, Seed, encode)

VERSION = 'FROI-1'
SIGNATURES = (('froi.record', ('node', 'variable')), ('froi.read', ('node',)))
GRAPH_TYPES = (Equality, Binding, PortBinding, Conflict, Witness)
HISTORY_TYPES = ('OBSERVATION_FRAME', 'WORLD_OBSERVATION', 'EXPERIENCE_FORMED',
                 'RECURSIVE_PARTIAL_OUTPUT', 'ACTION_REQUESTED', 'ACTION_EXECUTED', 'ACTION_FAILED')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def load_caps(path=None):
    if path is None:
        return Caps()
    return Caps(**json.loads(Path(path).read_text(encoding='utf-8')))


@dataclass(frozen=True)
class History:
    individual_id: str
    state_version: int
    event_cutoff: int
    events: tuple[str, ...]

    def material(self):
        """Validate raw sources; never use a legacy relation row as history."""
        events = tuple(json.loads(x) for x in self.events)
        frames, experiences, partials, registry = {}, {}, {}, {}
        for event in events:
            if event['individual_id'] != self.individual_id:
                raise ValueError('History crosses individual identity')
            if event['state_version'] > self.state_version or event['event_sequence'] > self.event_cutoff:
                raise ValueError('History crosses its declared cutoff')
            source = 'EVENT:' + event['event_id']
            if source in registry:
                raise ValueError('Duplicate input event identity')
            registry[source] = event
            payload = event['payload']
            kind = event['event_type']
            if kind == 'OBSERVATION_FRAME':
                key = payload['frame_id']
                if key in frames:
                    raise ValueError('Duplicate raw frame identity')
                frames[key] = payload
                registry['FRAME:' + key] = {'event_source': source, 'frame': payload}
            elif kind == 'EXPERIENCE_FORMED':
                key = payload['experience_id']
                if key in experiences:
                    raise ValueError('Duplicate experience identity')
                experiences[key] = (payload, source)
            elif kind == 'RECURSIVE_PARTIAL_OUTPUT':
                key = payload['partial_id']
                if key in partials:
                    raise ValueError('Duplicate partial identity')
                partials[key] = (payload, source)
        # All recorded experiences are included, not an active-memory window.
        from individual.structure import pattern_id
        records = []
        for experience, source in experiences.values():
            a, b = (frames[key] for key in experience['frame_ids'])
            if (experience['causality'] != 'temporal_association_only'
                or a['sequence_id'] >= b['sequence_id']
                or (a['encoding_namespace'], a['body_epoch']) != (b['encoding_namespace'], b['body_epoch'])
                or experience['antecedent'] != pattern_id(a['delta'])
                or experience['outcome'] != pattern_id(b['delta'])
                or experience['root'] != f"{experience['antecedent']}:{experience['action_code']}"):
                raise ValueError('Experience is not a faithfully recorded temporal association')
            records.append((experience, source, (b['encoding_namespace'], b['body_epoch'])))
        return tuple(records), partials, registry

    def origin(self, feedback):
        records, partials, _ = self.material()
        partial, source = partials[feedback['partial_id']]
        experience = partial['experience']
        matches = tuple(scope for item, _, scope in records if item['experience_id'] == experience['experience_id'])
        if len(matches) != 1 or experience['root'] != feedback['next_relation_ref']:
            raise ValueError('Requested reference has no unambiguous actual source')
        return ReferenceOrigin(*matches[0], experience['experience_id'], feedback['partial_id'], source)


def history_from_store(store, state):
    """Read committed input events only. No writes or capacity-based truncation."""
    placeholders = ','.join('?' for _ in HISTORY_TYPES)
    rows = store.connection.execute(
        f'SELECT event_sequence,event_id,individual_id,state_version,event_type,payload FROM events '
        f'WHERE state_version<=? AND event_type IN ({placeholders}) ORDER BY event_sequence',
        (state.state_version, *HISTORY_TYPES)).fetchall()
    cutoff = store.connection.execute('SELECT COALESCE(MAX(event_sequence),0) FROM events WHERE state_version<=?',
                                      (state.state_version,)).fetchone()[0]
    events = tuple(canonical(dict(zip(('event_sequence', 'event_id', 'individual_id', 'state_version',
                                      'event_type', 'payload'), (*row[:5], json.loads(row[5]))))) for row in rows)
    return History(state.individual_id, state.state_version, cutoff, events)


@dataclass(frozen=True)
class ReferenceOrigin:
    namespace: str
    body_epoch: int
    experience_id: str
    partial_id: str
    event_source: str


@dataclass(frozen=True)
class ReadRequest:
    individual_id: str
    source_state_version: int
    frame_json: str
    reference: str
    origin: ReferenceOrigin

    @property
    def frame(self):
        return json.loads(self.frame_json)

    @property
    def scope(self):
        return canonical((self.individual_id, self.origin.namespace, self.origin.body_epoch))

    @property
    def relation(self):
        node = Node(self.reference, namespace=VERSION, scope=self.scope)
        return Relation('read:' + self.frame['frame_id'], 'froi.read', (node,), source=VERSION, scope=self.scope)


@dataclass(frozen=True)
class EncodedInput:
    condition: Condition
    seeds: tuple
    registry_json: str


def encode_input(history, request):
    # Explicit current-state adapter; the historical codec below stays intact.
    if hasattr(history, 'encode_current'):
        return history.encode_current(request)
    if history.individual_id != request.individual_id or history.state_version >= request.source_state_version:
        raise ValueError('History identity/version does not precede this read')
    records, _, registry = history.material()
    nodes, values, seeds = {}, {}, []
    for item, source, (namespace, epoch) in records:
        scope = canonical((history.individual_id, namespace, epoch))
        node = Node(item['root'], namespace=VERSION, scope=scope)
        variable = Variable(item['experience_id'] + ':outcome', 'UnitRef', VERSION, scope)
        value = Value(item['outcome'], 'UnitRef')
        relation = Relation(item['experience_id'], 'froi.record', (node, variable), source=VERSION, scope=scope)
        sources = (source, *('FRAME:' + x for x in item['frame_ids']))
        seeds.extend((Seed(relation, sources), Seed(Binding(variable, value), sources)))
        nodes.update({node.key: node, variable.key: variable})
        values[value.key] = value
    read = request.relation
    nodes[read.ports[0].key] = read.ports[0]
    frame_source = 'CURRENT_FRAME:' + request.frame['frame_id']
    reference_source = 'CURRENT_REFERENCE:' + request.origin.partial_id
    registry[frame_source] = {'frame': request.frame, 'source_state_version': request.source_state_version}
    registry[reference_source] = {'reference': request.reference, 'origin': asdict(request.origin)}
    seeds.append(Seed(read, (frame_source, reference_source)))
    condition = Condition(tuple(sorted(nodes.values(), key=lambda x: encode(x.key))),
                          tuple(sorted(values.values(), key=lambda x: encode(x.key))), SIGNATURES)
    for declaration in (*condition.nodes, *condition.values, *condition.references):
        registry['DECL:' + encode(declaration.key)] = {'source': 'EXTERNAL_FIXED_MECHANISM',
            'codec': VERSION, 'declaration': declaration.key}
    return EncodedInput(condition, tuple(seeds), canonical(registry))


@dataclass(frozen=True)
class OrganizationHandle:
    request: ReadRequest
    history_cutoff: int
    condition: Condition | None
    status: str
    graph: tuple
    relations: tuple
    supports: tuple
    root_witnesses: tuple
    roots: tuple
    input_records: tuple
    registry_json: str
    diagnostic_json: str

    @property
    def complete(self):
        return self.status == 'COMPLETE'

    def graph_content(self):
        return tuple(sorted(((x.key, canonical(asdict(x))) for x in self.graph), key=encode))

    def audit(self):
        content = self.graph_content()
        registry = json.loads(self.registry_json)
        audit = {'codec_version': VERSION, 'individual_id': self.request.individual_id,
            'source_state_version': self.request.source_state_version, 'history_cutoff': self.history_cutoff,
            'current_frame_id': self.request.frame['frame_id'], 'requested_reference': self.request.reference,
            'reference_origin': asdict(self.request.origin), 'status': self.status,
            'closure_complete': self.complete, 'condition': asdict(self.condition) if self.condition else None,
            'graph_content': content, 'graph_digest': sha256(canonical(content).encode()).hexdigest(),
            'direct_supports': self.supports, 'root_witnesses': self.root_witnesses,
            'roots': self.roots, 'input_records': self.input_records,
            'input_registry': registry, 'diagnostic': json.loads(self.diagnostic_json)}
        if 'RUNTIME_SOURCE' in registry:
            audit['runtime_source'] = registry['RUNTIME_SOURCE']
        return audit


def produce(history, request, caps, condition=None):
    """Full frozen closure, never publish a partial graph as COMPLETE."""
    try:
        encoded = encode_input(history, request)
        condition = encoded.condition if condition is None else condition
        if condition.signatures != SIGNATURES:
            raise ValueError('Condition changes the fixed codec signatures')
        result = Engine(condition, caps).run(encoded.seeds)
    except (ValueError, KeyError, TypeError) as error:
        return OrganizationHandle(request, history.event_cutoff, condition, 'INVALID', (), (), (), (), (), (),
            '{}', canonical({'reason': str(error)}))
    registry = json.loads(encoded.registry_json)
    for declaration in (*condition.nodes, *condition.values, *condition.references):
        registry['DECL:' + encode(declaration.key)] = {'source': 'EXTERNAL_FIXED_MECHANISM',
            'codec': VERSION, 'declaration': declaration.key}
    registry_json = canonical(registry)
    diagnostic = {'operations': result.operations, 'rounds': result.closure_rounds, 'limit': result.limit}
    if not result.closure_complete:
        return OrganizationHandle(request, history.event_cutoff, condition, result.status, (), (), (), (), (), (),
            registry_json, canonical(diagnostic))
    state = result.state
    graph = tuple(sorted((x for x in state.facts.values() if isinstance(x, GRAPH_TYPES)), key=lambda x: encode(x.key)))
    roots = state.root_witnesses()
    supports = tuple((x.key, tuple(sorted(((p.rule, p.premises) for p in state.direct_supports(x.key)), key=encode))) for x in graph)
    witnesses = tuple((x.key, tuple(sorted(roots[x.key], key=encode))) for x in graph)
    return OrganizationHandle(request, history.event_cutoff, condition, result.status, graph,
        tuple(x for x in state.facts.values() if isinstance(x, Relation)), supports, witnesses,
        tuple(sorted(state.roots, key=encode)), tuple(sorted(state.input_records, key=encode)),
        registry_json, canonical(diagnostic))


@dataclass(frozen=True)
class ReadResult:
    status: str
    outcomes: tuple
    consumed_keys: tuple
    supports: tuple
    roots: tuple
    conflicts: tuple

    @property
    def succeeded(self):
        return self.status == 'READ_SUCCEEDED'


def consume(handle, request):
    """Only formed Shared/PortBind facts provide read answers. No raw inputs."""
    if handle.request != request:
        return ReadResult('BOUNDARY_MISMATCH', (), (), (), (), ())
    if not handle.complete:
        return ReadResult(handle.status, (), (), (), (), ())
    read_key = request.relation.key
    relations = {x.key: x for x in handle.relations}
    connected, consumed = set(), set()
    for fact in handle.graph:
        if not isinstance(fact, Witness):
            continue
        endpoints = ((fact.left_leaf, fact.left_port, fact.right_leaf, fact.right_port),
                     (fact.right_leaf, fact.right_port, fact.left_leaf, fact.left_port))
        for a, ai, b, bi in endpoints:
            relation = relations.get(b)
            if a == read_key and ai == 0 and bi == 0 and relation is not None and relation.type_id == 'froi.record':
                connected.add(b)
                consumed.add(fact.key)
    outcomes, variables, conflicts = set(), set(), []
    for fact in handle.graph:
        if isinstance(fact, PortBinding) and fact.relation.key in connected and fact.port == 1:
            if fact.variable != fact.relation.ports[1] or fact.value.value_type != 'UnitRef':
                return ReadResult('INVALID', (), (), (), (), ())
            outcomes.add(fact.value.value)
            variables.add(fact.variable)
            consumed.add(fact.key)
    for fact in handle.graph:
        if isinstance(fact, Conflict) and fact.variable in variables:
            consumed.add(fact.key)
            conflicts.append(fact.key)
    support_map, root_map = dict(handle.supports), dict(handle.root_witnesses)
    keys = tuple(sorted(consumed, key=encode))
    return ReadResult('READ_SUCCEEDED' if connected and outcomes else 'UNRESOLVED_REFERENCE',
        tuple(sorted(outcomes)), keys, tuple((k, support_map[k]) for k in keys),
        tuple((k, root_map[k]) for k in keys), tuple(sorted(conflicts, key=encode)))


class OrganizationSession:
    """One production read with committed historical material and frozen limits."""
    test_only = False

    def __init__(self, history, caps):
        self.history, self.caps = history, caps

    def read(self, frame, feedback, state_version):
        try:
            origin = self.history.origin(feedback)
        except (ValueError, KeyError, TypeError) as error:
            return None, ReadResult('INVALID', (), (), (), (), ()), {'reason': str(error)}
        request = ReadRequest(self.history.individual_id, state_version, canonical(frame.to_dict()),
                              feedback['next_relation_ref'], origin)
        handle = produce(self.history, request, self.caps)
        return handle, consume(handle, request), {}


def preflight(database, enabled, caps):
    path = Path(database).resolve()
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            return
        row = db.execute('SELECT snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
        boundary = json.loads(row[0]).get('internal_state', {}).get('l0_state', {}).get('froi_boundary') if row else None
    if boundary is not None and (not enabled or boundary != {'version': VERSION, 'caps': asdict(caps)}):
        raise ValueError('FROI lifetime requires its locked FROI profile/capacities; no legacy fallback')


def resume_detached(engine, checkpoint, handle, *, screen_effect=False):
    """TEST_ONLY exact-boundary entry: no prefix, producer, or EventStore call."""
    if not handle.complete or not checkpoint.requires_read:
        raise ValueError('Detached effect screening requires a COMPLETE read checkpoint')
    checkpoint.verify_handle(handle)
    result = (ReadResult('TEST_ONLY_EFFECT_SCREENED', (), (), (), (), ())
              if screen_effect else consume(handle, checkpoint.request))
    return engine.resume_from_read_checkpoint(checkpoint, handle, result,
        {'category': 'TEST_ONLY', 'effect_screened': screen_effect}, detached=True)


def advance_detached(engine, current, frame, state_version, pending_actions, handle, *, screen_effect=False):
    """Legacy TEST_ONLY preparation convenience, not historical checkpoint recovery.

    Exact post-hoc T3 must use resume_detached with the saved ReadCheckpoint.
    This compatibility entry still prepares a new prefix and therefore cannot
    recover a live frame whose prefix has already generated consequence UUIDs.
    """
    class Preparation:
        test_only = True
        caps = engine.froi_caps
        checkpoint_request = handle.request
        history_cutoff = handle.history_cutoff

    checkpoint = engine.prepare_read_checkpoint(current, frame, state_version, pending_actions,
                                                organization=Preparation())
    return resume_detached(engine, checkpoint, handle, screen_effect=screen_effect)
