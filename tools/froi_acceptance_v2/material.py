"""Bounded SQLite evidence access; unchanged v1 canonical logical byte stream."""
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
import threading

import psutil
from debug.froi_acceptance_material import (
    ROOT, digest, pack, unpack, protected_files, restore_saved_handle)
from integration.froi import History, HISTORY_TYPES, canonical
from integration.read_checkpoint import ReadCheckpoint, AUDIT_EVENT

COLS = 'event_sequence,event_id,individual_id,state_version,event_type,payload'
ENCODER = json.JSONEncoder(sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
ACTIVE_METRICS = None


class Metrics:
    def __init__(self):
        self.started = time.monotonic()
        self.rows_scanned = 0
        self.bytes_streamed = 0
        self.largest_single_decoded_event = 0
        self.largest_evidence_block = 0
        self.peak_rss = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()

    def _sample(self):
        process = psutil.Process()
        while not self._stop.is_set():
            info=process.memory_info()
            self.peak_rss = max(self.peak_rss, info.rss, getattr(info,'peak_wset',0))
            self._stop.wait(.02)

    def result(self, output_size=0):
        self._stop.set(); self._thread.join()
        info=psutil.Process().memory_info()
        self.peak_rss=max(self.peak_rss,info.rss,getattr(info,'peak_wset',0))
        return {'peak_rss_bytes': self.peak_rss,
                'rss_scope': 'actual executing Python process; producer/resume are in this process',
                'rss_method': 'Windows OS peak_wset plus 20ms sampling; sampling fallback on other platforms',
                'largest_single_decoded_event_bytes': self.largest_single_decoded_event,
                'decoded_event_size_definition': 'original UTF-8 payload bytes, not Python heap size',
                'largest_evidence_block_bytes': self.largest_evidence_block,
                'rows_scanned': self.rows_scanned, 'bytes_streamed': self.bytes_streamed,
                'artifact_output_size_bytes': output_size,
                'duration_seconds': time.monotonic() - self.started}


@contextmanager
def readonly(database):
    path = Path(database).resolve()
    if not path.is_file(): raise FileNotFoundError('MATERIAL_UNAVAILABLE: database missing')
    wal = Path(str(path) + '-wal')
    # Immutable mode must never silently ignore outstanding committed WAL data.
    immutable = not wal.exists() or wal.stat().st_size == 0
    db = __import__('sqlite3').connect(path.as_uri() + '?mode=ro' + ('&immutable=1' if immutable else ''), uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA cache_size=-4096')
        db.execute('BEGIN')
        yield db
    finally:
        db.rollback(); db.close()


def events(db, *, version=None, max_version=None, cutoff=None, types=None, after=None, metrics=None):
    """Stable keyset pages of ONE row: even large audit rows never batch-accumulate."""
    if metrics is None: metrics = ACTIVE_METRICS
    clauses = []; args = []
    if version is not None: clauses.append('state_version=?'); args.append(version)
    if max_version is not None: clauses.append('state_version<=?'); args.append(max_version)
    if cutoff is not None: clauses.append('event_sequence<=?'); args.append(cutoff)
    if types is not None:
        clauses.append('event_type IN (' + ','.join('?' for _ in types) + ')'); args.extend(types)
    last = after or 0
    while True:
        query = 'SELECT ' + COLS + ' FROM events WHERE event_sequence>?'
        if clauses: query += ' AND ' + ' AND '.join(clauses)
        row = db.execute(query + ' ORDER BY event_sequence LIMIT 1', (last, *args)).fetchone()
        if row is None: break
        last = row[0]
        if metrics:
            metrics.rows_scanned += 1
            metrics.largest_single_decoded_event = max(metrics.largest_single_decoded_event, len(row[5].encode('utf8')))
        yield dict(zip(COLS.split(','), (*row[:5], json.loads(row[5]))))


def feed(hasher, value, metrics=None, secondary=None):
    for token in ENCODER.iterencode(value):
        # JSONEncoder can emit a whole string token. Bound its UTF-8 conversion.
        for offset in range(0, len(token), 65536):
            chunk = token[offset:offset + 65536].encode('utf8')
            hasher.update(chunk)
            if secondary: secondary.update(chunk)
            if metrics: metrics.bytes_streamed += len(chunk)


def file_hash(path, metrics=None):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            if metrics: metrics.bytes_streamed += len(block)
    return h.hexdigest()


def logical_digest(db, metrics=None):
    """Exactly canonical((v1 event_rows, ordered SELECT * states)), not a new digest format."""
    h = sha256(); ev = sha256(); h.update(b'[['); ev.update(b'[')
    first = True
    for row in events(db, metrics=metrics):
        if not first: h.update(b','); ev.update(b',')
        feed(h, row, metrics, ev); first = False
    h.update(b'],['); ev.update(b']'); first = True
    for row in db.execute('SELECT * FROM states ORDER BY state_version'):
        if not first: h.update(b',')
        feed(h, row, metrics); first = False
        if metrics: metrics.rows_scanned += 1
    h.update(b']]')
    return h.hexdigest(), ev.hexdigest()


def freeze(database=None, metrics=None):
    import subprocess
    result = {'repository_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
              'protected_source_hashes': protected_files()}
    manifest = ROOT / 'FROI_ACCEPTANCE_FREEZE.json'
    if manifest.is_file(): result['harness_manifest_digest'] = file_hash(manifest)
    if database:
        path = Path(database).resolve()
        result['database_files'] = {str(p): file_hash(p, metrics) for p in
            (path, Path(str(path) + '-wal'), Path(str(path) + '-shm')) if p.is_file()}
        with readonly(path) as db:
            result['database_content'], source = logical_digest(db, metrics)
            result['state_range'] = list(db.execute('SELECT MIN(state_version),MAX(state_version),COUNT(*) FROM states').fetchone())
        # Extra event digest is separate from v1 freeze to keep its exact dictionary contract.
        return result, source
    return result


def read_history(database, version):
    with readonly(database) as db:
        identity = db.execute('SELECT individual_id FROM experiment').fetchone()[0]
        if not db.execute('SELECT 1 FROM states WHERE state_version=?', (version,)).fetchone():
            raise ValueError('MATERIAL_UNAVAILABLE: historical state missing')
        cutoff = db.execute('SELECT COALESCE(MAX(event_sequence),0) FROM events WHERE state_version<=?', (version,)).fetchone()[0]
        # Only the FULL declared prefix enters the unchanged producer History API.
        history = tuple(canonical(r) for r in events(db, max_version=version, cutoff=cutoff, types=HISTORY_TYPES))
        return History(identity, version, cutoff, history)


def locator(database, freeze_identity, cp_digest, cutoff, table, row, object_type):
    return {'database': str(Path(database).resolve()), 'source_freeze_digest': freeze_identity,
            'checkpoint_digest': cp_digest, 'history_cutoff': cutoff, 'table': table,
            'event_sequence': row.get('event_sequence'), 'event_id': row.get('event_id'),
            'state_version': row['state_version'], 'object_type': object_type, 'content_digest': digest(row)}


@dataclass(frozen=True)
class Artifact:
    manifest_text: str
    checkpoint: object
    handle: object
    history: object
    _payload: object
    verified_source_events_digest: str

    @property
    def payload(self):
        # A small local view, not a JSON reparse of the session. Caller copies cannot mutate it.
        from copy import deepcopy
        return deepcopy(self._payload)

    @property
    def digest(self): return sha256(self.manifest_text.encode()).hexdigest()

    def verify_source_events(self):
        return json.loads(self.manifest_text)['source_events_digest'] == self.verified_source_events_digest


def export_manifest(database, version, source_freeze, source_events_digest, *, test_fixture=False, metrics=None):
    with readonly(database) as db:
        rr = list(events(db, version=version, metrics=metrics))
        cps = [r for r in rr if r['event_type'] == AUDIT_EVENT]
        formed = [r for r in rr if r['event_type'] == 'FROI_ORGANIZATION_FORMED']
        if len(cps) != 1: raise ValueError('HISTORICAL_CHECKPOINT_NOT_RECONSTRUCTABLE')
        cp = ReadCheckpoint.deserialize(cps[0]['payload']['checkpoint'])
        if cp.payload['test_only'] or cps[0]['payload'].get('test_only'): raise ValueError('TEST_ONLY checkpoint')
        if len(formed) != 1 or not formed[0]['payload'].get('closure_complete'):
            raise ValueError('NOT_TESTABLE: COMPLETE organization unavailable')
        cutoff = cp.payload['history_cutoff']
        hr = list(events(db, cutoff=cutoff, types=HISTORY_TYPES, metrics=metrics))
        h = History(cp.payload['individual_id'], version - 1, cutoff, tuple(canonical(r) for r in hr))
        handle = restore_saved_handle(formed[0]['payload'], h, cp.request); cp.verify_handle(handle)
        raw = cps[0]['payload']
        if cp.digest != raw['checkpoint_digest'] or digest(handle.audit()) != raw['organization_handle_digest']:
            raise ValueError('Stored checkpoint/handle binding mismatch')
        snap = db.execute('SELECT * FROM states WHERE state_version=?', (version,)).fetchone()
        if snap is None: raise ValueError('MATERIAL_UNAVAILABLE: processing state missing')
        snapshot_row = dict(zip(('state_version','individual_id','timestamp','snapshot'), snap))
        fid = digest(source_freeze)
        references = [locator(database,fid,cp.digest,cutoff,'events',r,r['event_type']) for r in rr + hr]
        references.append(locator(database,fid,cp.digest,cutoff,'states',snapshot_row,'formal_snapshot'))
        manifest = {'schema':'FROI-1-ACCEPTANCE-ARTIFACT-v2','category':'EXPERIMENTER','recursive_input':False,
            'database':str(Path(database).resolve()), 'state_version':version,
            'material_scope':'TEST_ONLY_FIXTURE' if test_fixture else 'FORMAL_RECORDED',
            'source_freeze':source_freeze, 'source_events_digest':source_events_digest,
            'checkpoint_digest':cp.digest, 'handle_digest':digest(handle.audit()),
            'graph_digest':handle.audit()['graph_digest'], 'history_digest':digest(pack(h)),
            'event_range':[rr[0]['event_sequence'],rr[-1]['event_sequence']], 'locators':references}
        if metrics:
            metrics.largest_evidence_block = max(metrics.largest_evidence_block,
                len(raw['checkpoint'].encode()), *(len(canonical(r).encode()) for r in rr + hr))
        return canonical(manifest)


def load_manifest(text, source_freeze, source_events_digest, metrics=None):
    m = json.loads(text)
    if canonical(m) != text or m['schema'] != 'FROI-1-ACCEPTANCE-ARTIFACT-v2': raise ValueError('Invalid v2 manifest')
    if m['source_freeze'] != source_freeze or m['source_events_digest'] != source_events_digest:
        raise ValueError('Source event material changed/missing/corrupt')
    database=m['database']; version=m['state_version']
    # Recreate the expected locator set from the actual complete prefix, detecting missing/extra references.
    expected=export_manifest(database,version,source_freeze,source_events_digest,
                             test_fixture=m['material_scope']=='TEST_ONLY_FIXTURE',metrics=metrics)
    if expected != text: raise ValueError('Artifact locator completeness/identity mismatch')
    with readonly(database) as db:
        rr=list(events(db,version=version,metrics=metrics))
        raw=next(r['payload'] for r in rr if r['event_type']==AUDIT_EVENT)
        cp=ReadCheckpoint.deserialize(raw['checkpoint'])
        hr=list(events(db,cutoff=cp.payload['history_cutoff'],types=HISTORY_TYPES,metrics=metrics))
        h=History(cp.payload['individual_id'],version-1,cp.payload['history_cutoff'],tuple(canonical(r) for r in hr))
        audit=next(r['payload'] for r in rr if r['event_type']=='FROI_ORGANIZATION_FORMED')
        handle=restore_saved_handle(audit,h,cp.request)
        original=json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=?',(version,)).fetchone()[0])
        if original['session_id']!=cp.payload['session_id'] or original['individual_id']!=cp.payload['individual_id']:
            raise ValueError('Checkpoint session/individual mismatch')
        if cp.payload['state_version'] != version: raise ValueError('Checkpoint version mismatch')
        # Only next WORLD/frame + intervening recorded actions are used by frozen continuation.
        nxt=db.execute("SELECT MIN(event_sequence) FROM events WHERE state_version>? AND event_type='WORLD_OBSERVATION'",(version,)).fetchone()[0]
        future=[] if nxt is None else list(events(db,after=rr[-1]['event_sequence'],cutoff=nxt,
            types=('WORLD_OBSERVATION','ACTION_EXECUTED','ACTION_FAILED'),metrics=metrics))
        p={**m,'checkpoint':cp.serialize(),'checkpoint_digest':cp.digest,'formal_snapshot':original,
           'round_events':rr,'next_round_events':future,'history_digest':digest(pack(h))}
        return Artifact(text,cp,handle,h,p,source_events_digest)


def t1_rows(db, artifact):
    cp=artifact.checkpoint
    # ALL history types in the exact cutoff and ALL selected-round records, including worker evidence.
    hr=list(events(db,cutoff=cp.payload['history_cutoff'],types=HISTORY_TYPES))
    rr=list(events(db,version=cp.payload['state_version']))
    return sorted(hr+rr,key=lambda r:r['event_sequence'])


def t4_material(database, limit_id):
    with readonly(database) as db:
        encounters=[r for r in events(db,types=('CURRENT_LIMIT_ENCOUNTER',)) if r['payload']['limit_id']==limit_id]
        if len(encounters)!=1: return encounters, {}
        version=encounters[0]['state_version']
        nxt=db.execute("SELECT state_version FROM events WHERE state_version>? AND event_type='WORLD_OBSERVATION' ORDER BY event_sequence LIMIT 1",(version,)).fetchone()
        rows=list(events(db,version=version))
        if nxt: rows.extend(events(db,version=nxt[0]))
        state=db.execute('SELECT snapshot FROM states WHERE state_version=?',(version,)).fetchone()
        return rows,{version:json.loads(state[0])} if state else {}


def continuation_rows(db):
    # Every use of `actual` in v1 continuation is a WORLD/frame lookup; no semantic selection.
    return list(events(db,types=('WORLD_OBSERVATION','OBSERVATION_FRAME')))
