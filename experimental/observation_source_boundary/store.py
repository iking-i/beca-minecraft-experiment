"""Same-DB authoritative facts; no connection to optional events/history.

The context is an execution dependency, never serialized into A's state.
Only one uncommitted current source and a bounded decoded-source cache exist.
"""
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import json
import sqlite3
from uuid import uuid4

from individual.events import encode
from individual.formal_l0 import digest
from experimental.native_body_operands.engine import typed_inputs

VERSION = 'AUTHORITATIVE-OBSERVATION-SOURCES-TEST_ONLY-1'
ACTIVE = ContextVar('test_only_observation_repository', default=None)


def repository():
    value = ACTIVE.get()
    if value is None:
        raise ValueError('Explicit authoritative source execution context required')
    return value


@contextmanager
def using(value):
    token = ACTIVE.set(value)
    try:
        yield value
    finally:
        ACTIVE.reset(token)


class SourceStore:
    def __init__(self, db, *, install=False):
        self.db = db
        self.pending = None
        self.cache = OrderedDict()
        self.reads = self.read_bytes = self.index_reads = 0
        self.fail_after_sources = False
        if install:
            # Never called for an existing non-experimental database.
            with db:
                db.execute('CREATE TABLE os_boundary(singleton INTEGER PRIMARY KEY CHECK(singleton=1), version TEXT, store_id TEXT, individual_id TEXT, count INTEGER, last_frame TEXT, head TEXT)')
                iid = db.execute('SELECT individual_id FROM experiment WHERE singleton=1').fetchone()[0]
                db.execute('INSERT INTO os_boundary VALUES(1,?,?,?,?,?,?)', (VERSION, str(uuid4()), iid, 0, None, digest([])))
                db.execute('CREATE TABLE os_sources(frame_id TEXT PRIMARY KEY, individual_id TEXT NOT NULL, source_digest TEXT NOT NULL, meta TEXT NOT NULL, body TEXT NOT NULL, ordinal INTEGER UNIQUE NOT NULL, previous_head TEXT NOT NULL, head TEXT NOT NULL)')
                db.execute('CREATE TABLE os_atoms(namespace TEXT NOT NULL, node TEXT NOT NULL, pattern_digest TEXT NOT NULL, pattern TEXT NOT NULL, witness_frame TEXT NOT NULL REFERENCES os_sources(frame_id), PRIMARY KEY(namespace,node,pattern_digest))')
                db.execute('CREATE TABLE os_channels(channel TEXT PRIMARY KEY, witness_frame TEXT NOT NULL REFERENCES os_sources(frame_id))')
                for table in ('os_sources', 'os_atoms', 'os_channels'):
                    for operation in ('UPDATE', 'DELETE'):
                        db.execute(f"CREATE TRIGGER immutable_{table}_{operation} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'immutable authoritative source'); END")
        self.header = self._header()

    def _header(self):
        try:
            row = self.db.execute('SELECT version,store_id,individual_id,count,last_frame,head FROM os_boundary WHERE singleton=1').fetchone()
        except sqlite3.Error as error:
            raise ValueError('Missing authoritative observation source store') from error
        if not row or row[0] != VERSION:
            raise ValueError('Source store version mismatch')
        return dict(zip(('version', 'store_id', 'individual_id', 'count', 'last_frame', 'head'), row))

    def descriptor(self):
        return deepcopy(self.pending['descriptor'] if self.pending else self.header)

    def boundary(self, descriptor):
        if descriptor not in (self.header, self.descriptor()) or self._header() != self.header:
            raise ValueError('Authority/source commit boundary mismatch')
        if self.header['count']:
            row = self.db.execute('SELECT ordinal,head,individual_id FROM os_sources WHERE frame_id=?', (self.header['last_frame'],)).fetchone()
            if row != (self.header['count'], self.header['head'], self.header['individual_id']):
                raise ValueError('Missing or mismatched source commit head')

    def stage(self, source, meta):
        typed_inputs(source)
        if self.pending:
            raise ValueError('Only one current uncommitted observation allowed')
        if not source['frame_id'].startswith(self.header['individual_id'] + ':E'):
            raise ValueError('Foreign individual observation')
        if self.db.execute('SELECT 1 FROM os_sources WHERE frame_id=?', (source['frame_id'],)).fetchone():
            raise ValueError('Observation identity reused; no replay/replacement')
        if set(meta) != {'timestamp', 'sequence_id', 'source_digest'} or meta['source_digest'] != digest(source):
            raise ValueError('Invalid source metadata')
        if type(meta['sequence_id']) is not int or type(meta['timestamp']) is not str:
            raise ValueError('Invalid source metadata types')
        descriptor = deepcopy(self.header)
        descriptor['count'] += 1
        descriptor['last_frame'] = source['frame_id']
        descriptor['head'] = digest([self.header['head'], source['frame_id'], meta])
        self.pending = {'source': deepcopy(source), 'meta': deepcopy(meta), 'descriptor': descriptor}

    def get(self, frame_id):
        if self.pending and self.pending['source']['frame_id'] == frame_id:
            return deepcopy(self.pending['source'])
        if frame_id in self.cache:
            self.cache.move_to_end(frame_id)
            return deepcopy(self.cache[frame_id])
        row = self.db.execute('SELECT individual_id,source_digest,meta,body FROM os_sources WHERE frame_id=?', (frame_id,)).fetchone()
        if row is None:
            raise ValueError('Missing authoritative observation source')
        iid, expected, raw_meta, raw = row
        self.reads += 1
        self.read_bytes += len(raw.encode('utf-8'))
        source, meta = json.loads(raw), json.loads(raw_meta)
        if (type(source) is not dict or set(source) != {'frame_id','namespace','body_epoch','declarations','numeric_channels','references'}
                or type(meta) is not dict
                or iid != self.header['individual_id'] or not frame_id.startswith(iid + ':E')
                or source['frame_id'] != frame_id or expected != digest(source)
                or meta.get('source_digest') != expected
                or set(meta) != {'timestamp', 'sequence_id', 'source_digest'}
                or type(meta['sequence_id']) is not int or type(meta['timestamp']) is not str):
            raise ValueError('Corrupt authoritative observation source')
        typed_inputs(source)
        self.cache[frame_id] = source
        while len(self.cache) > 8:
            self.cache.popitem(last=False)
        return deepcopy(source)

    def meta(self, frame_id):
        self.get(frame_id)
        if self.pending and self.pending['source']['frame_id'] == frame_id:
            return deepcopy(self.pending['meta'])
        return json.loads(self.db.execute('SELECT meta FROM os_sources WHERE frame_id=?', (frame_id,)).fetchone()[0])

    def atom(self, namespace, node):
        self.index_reads += 1
        rows = self.db.execute('SELECT pattern,witness_frame,pattern_digest FROM os_atoms WHERE namespace=? AND node=? LIMIT 2', (namespace, node)).fetchall()
        patterns = []
        for raw, frame, pd in rows:
            pattern = json.loads(raw)
            source = self.get(frame)
            if digest(pattern) != pd or source['namespace'] != namespace or typed_inputs(source).get(node) != pattern:
                raise ValueError('Corrupt authoritative operand index')
            patterns.append(pattern)
        if self.pending and self.pending['source']['namespace'] == namespace:
            candidate = typed_inputs(self.pending['source']).get(node)
            if candidate and candidate['type'] in ('ObservedValue', 'ObservedReference'):
                patterns.append(candidate)
        if not patterns or any(p != patterns[0] for p in patterns):
            raise ValueError('Unobserved or ambiguous observation endpoint')
        return deepcopy(patterns[0])

    def channel(self, channel):
        if self.pending and channel in self.pending['source']['numeric_channels']:
            return True
        row = self.db.execute('SELECT witness_frame FROM os_channels WHERE channel=?', (channel,)).fetchone()
        if not row:
            return False
        if channel not in self.get(row[0])['numeric_channels']:
            raise ValueError('Corrupt channel incidence index')
        return True

    def flush(self, descriptor):
        if not self.db.in_transaction:
            raise RuntimeError('Source publication requires owning state transaction')
        self.boundary(descriptor)
        if descriptor != self.descriptor():
            raise ValueError('Cannot publish a source outside its next state boundary')
        if not self.pending:
            return
        source, meta, new = (self.pending[k] for k in ('source', 'meta', 'descriptor'))
        self.db.execute('INSERT INTO os_sources VALUES(?,?,?,?,?,?,?,?)',
            (source['frame_id'], self.header['individual_id'], digest(source), encode(meta), encode(source), new['count'], self.header['head'], new['head']))
        for node, pattern in typed_inputs(source).items():
            if pattern['type'] in ('ObservedValue', 'ObservedReference'):
                self.db.execute('INSERT OR IGNORE INTO os_atoms VALUES(?,?,?,?,?)', (source['namespace'], node, digest(pattern), encode(pattern), source['frame_id']))
        for channel in source['numeric_channels']:
            self.db.execute('INSERT OR IGNORE INTO os_channels VALUES(?,?)', (channel, source['frame_id']))
        self.db.execute('UPDATE os_boundary SET count=?,last_frame=?,head=? WHERE singleton=1', (new['count'], new['last_frame'], new['head']))
        if self.fail_after_sources:
            raise RuntimeError('TEST_ONLY publication failure after source writes')

    def published(self):
        self.header = self._header()
        self.pending = None

    def reset_reads(self):
        self.cache.clear()
        self.reads = self.read_bytes = self.index_reads = 0

    def audit(self):
        """Explicit full authority audit, streaming sources, outside recursion."""
        head, count, last = digest([]), 0, None
        expected_atoms, expected_channels = set(), set()
        self.cache.clear()
        for frame, ordinal, previous, saved in self.db.execute('SELECT frame_id,ordinal,previous_head,head FROM os_sources ORDER BY ordinal'):
            source, meta = self.get(frame), self.meta(frame)
            count += 1
            if ordinal != count or previous != head:
                raise ValueError('Broken authoritative source chain')
            head = digest([head, frame, meta])
            if head != saved:
                raise ValueError('Source manifest mismatch')
            last = frame
            for node, p in typed_inputs(source).items():
                if p['type'] in ('ObservedValue', 'ObservedReference'):
                    expected_atoms.add((source['namespace'], node, digest(p), encode(p)))
            expected_channels.update(source['numeric_channels'])
        if (count, last, head) != (self.header['count'], self.header['last_frame'], self.header['head']):
            raise ValueError('Missing authoritative history')
        actual_atoms = set()
        for ns, node, pd, raw, frame in self.db.execute('SELECT * FROM os_atoms'):
            p = json.loads(raw)
            if digest(p) != pd or self.get(frame)['namespace'] != ns or typed_inputs(self.get(frame)).get(node) != p:
                raise ValueError('Corrupt operand index')
            actual_atoms.add((ns, node, pd, raw))
        if expected_atoms != actual_atoms:
            raise ValueError('Missing or foreign operand index')
        actual_channels = set()
        for channel, frame in self.db.execute('SELECT * FROM os_channels'):
            if channel not in self.get(frame)['numeric_channels']:
                raise ValueError('Corrupt channel index')
            actual_channels.add(channel)
        if expected_channels != actual_channels:
            raise ValueError('Channel index coverage mismatch')
        self.cache.clear()
        return {'sources': count, 'head': head, 'classification': 'PASS'}
