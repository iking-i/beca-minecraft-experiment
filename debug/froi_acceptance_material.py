"""EXPERIMENTER evidence only. No runtime imports this module; no EventStore writes.

All database access is query_only + mode=ro, under one read transaction. JSON
decoding uses an explicit dataclass allowlist, never pickle or dynamic imports.
"""
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess

from experimental.gsc0 import model
from experimental.gsc0.engine import Caps, Condition
from integration.froi import (History, OrganizationHandle, ReadRequest, ReferenceOrigin,
    HISTORY_TYPES, canonical, encode_input)
from integration.read_checkpoint import ReadCheckpoint, AUDIT_EVENT, ordered_json

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'FROI-1-ACCEPTANCE-ARTIFACT-v1'
TYPES = {c.__name__: c for c in (model.Node, model.Variable, model.Value,
    model.Reference, model.Relation, model.Equality, model.Binding, model.PortBinding,
    model.Conflict, model.Witness, Condition, ReadRequest, ReferenceOrigin,
    History, OrganizationHandle)}


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def pack(value):
    if is_dataclass(value):
        if type(value).__name__ not in TYPES:
            raise ValueError('Unregistered artifact type')
        return {'$type': type(value).__name__, 'fields': {f.name: pack(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, tuple):
        return {'$tuple': [pack(x) for x in value]}
    if isinstance(value, list):
        return [pack(x) for x in value]
    if isinstance(value, dict):
        return {k: pack(v) for k, v in value.items()}
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError('Unsupported artifact data')


def unpack(value):
    if isinstance(value, list):
        return [unpack(x) for x in value]
    if isinstance(value, dict):
        if set(value) == {'$tuple'}:
            return tuple(unpack(x) for x in value['$tuple'])
        if set(value) == {'$type', 'fields'}:
            cls = TYPES.get(value['$type'])
            if cls is None or set(value['fields']) != {f.name for f in fields(cls)}:
                raise ValueError('Unknown/incomplete typed artifact')
            return cls(**{k: unpack(v) for k, v in value['fields'].items()})
        return {k: unpack(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class ValidationArtifact:
    content: str

    def __post_init__(self):
        p = json.loads(self.content)
        if ordered_json(p) != self.content or p.get('schema') != SCHEMA or p.get('category') != 'EXPERIMENTER':
            raise ValueError('Invalid canonical validation artifact')
        if p.get('recursive_input') is not False:
            raise ValueError('Artifact cannot be recursive input')
        cp = self.checkpoint
        handle = self.handle
        cp.verify_handle(handle)
        if p['checkpoint_digest'] != cp.digest or p['handle_digest'] != digest(handle.audit()):
            raise ValueError('Artifact checkpoint/handle digest mismatch')
        if p['graph_digest'] != handle.audit()['graph_digest']:
            raise ValueError('Artifact graph digest mismatch')
        history = self.history
        if history.event_cutoff != handle.history_cutoff or history.individual_id != cp.request.individual_id:
            raise ValueError('Artifact history identity mismatch')

    @property
    def payload(self): return json.loads(self.content)
    @property
    def checkpoint(self): return ReadCheckpoint.deserialize(self.payload['checkpoint'])
    @property
    def handle(self): return unpack(self.payload['handle'])
    @property
    def history(self): return unpack(self.payload['history'])
    @property
    def digest(self): return sha256(self.content.encode()).hexdigest()

    def serialize(self): return ordered_json({'content': self.content, 'digest': self.digest})

    @classmethod
    def deserialize(cls, text):
        p = json.loads(text)
        if set(p) != {'content', 'digest'} or sha256(p['content'].encode()).hexdigest() != p['digest']:
            raise ValueError('Validation artifact envelope digest mismatch')
        return cls(p['content'])


@contextmanager
def readonly(database):
    path = Path(database).resolve()
    if not path.is_file(): raise FileNotFoundError('MATERIAL_UNAVAILABLE: database missing')
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        yield db
    finally:
        db.rollback()
        db.close()


def event_rows(db):
    names = ('event_sequence','event_id','individual_id','state_version','event_type','payload')
    return [dict(zip(names, (*r[:5], json.loads(r[5])))) for r in db.execute(
        'SELECT event_sequence,event_id,individual_id,state_version,event_type,payload FROM events ORDER BY event_sequence')]


def read_history(database, version):
    with readonly(database) as db:
        rows = event_rows(db)
        identity = db.execute('SELECT individual_id FROM experiment').fetchone()[0]
        if not db.execute('SELECT 1 FROM states WHERE state_version=?', (version,)).fetchone():
            raise ValueError('MATERIAL_UNAVAILABLE: historical state missing')
        cutoff = max((r['event_sequence'] for r in rows if r['state_version'] <= version), default=0)
        return History(identity, version, cutoff, tuple(canonical(r) for r in rows
            if r['state_version'] <= version and r['event_type'] in HISTORY_TYPES))


def protected_files():
    paths = []
    for folder in ('individual','integration','experimental/gsc0','minecraft','bridge','supervisor','debug','tests'):
        for p in (ROOT / folder).rglob('*'):
            relative=p.relative_to(ROOT).as_posix()
            local=relative in ('minecraft/config.json','individual/lifetime.json') or '.local.' in p.name
            if p.is_file() and not local and p.suffix in ('.py','.js','.json','.yaml') and not any(x in p.parts for x in ('node_modules','__pycache__','.auth')):
                paths.append(p)
    paths.extend(ROOT/p for p in ('FORMAL_RECURSIVE_ORGANIZATION_INTEGRATION_SPEC.md',))
    return {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}


def freeze(database=None):
    data = {'repository_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT).decode().strip(),
        'protected_source_hashes': protected_files()}
    manifest=ROOT/'FROI_ACCEPTANCE_FREEZE.json'
    if manifest.is_file(): data['harness_manifest_digest']=sha256(manifest.read_bytes()).hexdigest()
    if database:
        path = Path(database).resolve()
        data['database_files'] = {str(p): sha256(p.read_bytes()).hexdigest() for p in
            (path, Path(str(path)+'-wal'), Path(str(path)+'-shm')) if p.is_file()}
        with readonly(path) as db:
            data['database_content'] = digest((event_rows(db), list(db.execute('SELECT * FROM states ORDER BY state_version'))))
            data['state_range'] = list(db.execute('SELECT MIN(state_version),MAX(state_version),COUNT(*) FROM states').fetchone())
    return data


def restore_saved_handle(audit, history, request):
    """Lossless inverse of saved handle.audit(), without closure or raw-history read answers."""
    nodes = lambda p: model.Variable(**p) if 'value_type' in p else model.Node(**p)
    relation = lambda p: model.Relation(p['name'],p['type_id'],tuple(nodes(x) for x in p['ports']),p['source'],p['scope'])
    graph = []
    for key, text in audit['graph_content']:
        p = json.loads(text)
        kind = key[0]
        if kind == 'Eq': fact = model.Equality(nodes(p['left']), nodes(p['right']))
        elif kind == 'Bind': fact = model.Binding(nodes(p['variable']), model.Value(**p['value']))
        elif kind == 'PortBind': fact = model.PortBinding(relation(p['relation']),p['port'],nodes(p['variable']),model.Value(**p['value']))
        elif kind == 'Conflict': fact = model.Conflict(nodes(p['variable']), tuple(model.Value(**v) for v in p['values']))
        elif kind == 'Shared': fact = model.Witness(tuples(p['left_leaf']),p['left_port'],tuples(p['right_leaf']),p['right_port'])
        else: raise ValueError('Unsupported saved graph type')
        if fact.key != tuples(key): raise ValueError('Saved typed identity mismatch')
        graph.append(fact)
    p = audit['condition']
    condition = Condition(tuple(nodes(n) for n in p['nodes']),tuple(model.Value(**v) for v in p['values']),
        tuples(p['signatures']),tuple(model.Reference(r['token'],nodes(r['target']),r['issuer'],r['epoch']) for r in p['references']),p['version'])
    encoded = encode_input(history, request)
    relations = tuple(s.fact for s in encoded.seeds if isinstance(s.fact, model.Relation))
    handle = OrganizationHandle(request,audit['history_cutoff'],condition,audit['status'],tuple(graph),relations,
        tuples(audit['direct_supports']),tuples(audit['root_witnesses']),tuples(audit['roots']),
        tuples(audit['input_records']),canonical(audit['input_registry']),canonical(audit['diagnostic']))
    if canonical(handle.audit()) != canonical(audit): raise ValueError('Saved handle restoration mismatch')
    return handle


def tuples(x):
    return tuple(tuples(v) for v in x) if isinstance(x, (list, tuple)) else x


def export_artifact(database, version, *, test_fixture=False):
    """Reads one exact stored read; never prepares a new prefix or executes A."""
    with readonly(database) as db:
        rows = event_rows(db)
        selected = [r for r in rows if r['state_version'] == version]
        cps = [r for r in selected if r['event_type'] == AUDIT_EVENT]
        if len(cps) != 1:
            raise ValueError('HISTORICAL_CHECKPOINT_NOT_RECONSTRUCTABLE: exact checkpoint unavailable/ambiguous')
        raw = cps[0]['payload']
        cp = ReadCheckpoint.deserialize(raw['checkpoint'])
        if cp.payload['test_only'] or raw.get('test_only'):
            raise ValueError('TEST_ONLY checkpoint is not formal acceptance material')
        if cp.payload['state_version'] != version: raise ValueError('Checkpoint version mismatch')
        formed = [r['payload'] for r in selected if r['event_type'] == 'FROI_ORGANIZATION_FORMED']
        if len(formed) != 1 or not formed[0].get('closure_complete'):
            raise ValueError('NOT_TESTABLE: COMPLETE organization unavailable')
        history_version = version-1
        history_rows = [r for r in rows if r['event_sequence'] <= cp.payload['history_cutoff'] and r['event_type'] in HISTORY_TYPES]
        history = History(cp.payload['individual_id'],history_version,cp.payload['history_cutoff'],tuple(canonical(r) for r in history_rows))
        handle = restore_saved_handle(formed[0], history, cp.request)
        if raw['checkpoint_digest'] != cp.digest or raw['organization_handle_digest'] != digest(handle.audit()):
            raise ValueError('Stored checkpoint/handle binding mismatch')
        snapshot = db.execute('SELECT snapshot FROM states WHERE state_version=?',(version,)).fetchone()
        if not snapshot: raise ValueError('MATERIAL_UNAVAILABLE: processing state missing')
        original = json.loads(snapshot[0])
        if original['session_id'] != cp.payload['session_id'] or original['individual_id'] != cp.payload['individual_id']:
            raise ValueError('Checkpoint session/individual mismatch')
        data = {'schema':SCHEMA,'category':'EXPERIMENTER','recursive_input':False,
            'material_scope':'TEST_ONLY_FIXTURE' if test_fixture else 'FORMAL_RECORDED',
            'database':str(Path(database).resolve()),'source_freeze':freeze(database),
            'checkpoint':cp.serialize(),'checkpoint_digest':cp.digest,'handle':pack(handle),
            'handle_digest':digest(handle.audit()),'graph_digest':handle.audit()['graph_digest'],
            'history':pack(history),'history_digest':digest(pack(history)),
            'event_range':[selected[0]['event_sequence'],selected[-1]['event_sequence']],
            'source_events':rows,'formal_snapshot':original,'round_events':selected,
            'next_round_events':[r for r in rows if r['state_version']>version]}
        return ValidationArtifact(ordered_json(data))
