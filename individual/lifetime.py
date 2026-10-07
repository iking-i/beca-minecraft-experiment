"""Pinned lifetime storage, read-only reports and explicit snapshot branches."""

import argparse
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from .events import EventStore, encode
from .identity import ExperimentLease, new_individual_id
from .state import AState, utc_now
from .current_state import current_metadata, ends_table, session_mode, audit_gaps

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'individual/lifetime.json'


def read_database(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def initialize_lifetime(database):
    """Explicit first registration, never invoked by a session restart."""
    path = Path(database).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb'):
        pass
    lease = ExperimentLease(path).acquire()
    store = None
    try:
        store = EventStore(path)
        state = store.register_lifetime()
        return {'database': str(path), 'individual_id': state.individual_id,
                'state_version': state.state_version, 'runtime_started': False}
    finally:
        if store:
            store.close()
        lease.release()


def resolve_runtime_database(database=None, branch_database=None, config=CONFIG):
    """Normal launches cannot select a fresh database and silently replace A."""
    if database and branch_database and Path(database).resolve() != Path(branch_database).resolve():
        raise ValueError('Use either the pinned mainline or an explicit --branch-db')
    settings = json.loads(Path(config).read_text(encoding='utf-8'))
    mainline = (ROOT / settings['database']).resolve()
    path = Path(branch_database).resolve() if branch_database else mainline
    if database and not branch_database and Path(database).resolve() != mainline:
        raise ValueError('A uses its pinned lifetime database. Do not create a new --db per session; use main.py without --db. Snapshot branches require --branch-db.')
    if not path.is_file():
        raise ValueError('Lifetime database is missing; refusing to generate a replacement identity')
    with closing(read_database(path)) as db:
        identity = db.execute('SELECT individual_id FROM experiment WHERE singleton=1').fetchone()
        if identity is None:
            raise ValueError('Database has no individual lifetime identity')
        if branch_database:
            row = db.execute('SELECT role,origin FROM individual_lifetime WHERE singleton=1').fetchone()
            if not row or row[0] != 'snapshot_branch' or identity[0] == settings['individual_id']:
                raise ValueError('Explicit branch execution requires a distinct snapshot-branch identity')
        elif identity[0] != settings['individual_id']:
            raise ValueError('Pinned individual_id differs from the stored lifetime; refusing replacement')
        elif db.execute("SELECT 1 FROM sqlite_master WHERE name='individual_lifetime'").fetchone():
            if db.execute('SELECT role FROM individual_lifetime').fetchone()[0] != 'mainline':
                raise ValueError('A snapshot branch cannot be selected as the original mainline')
    return path


def history_summary(database, connection=None):
    owns = connection is None
    db = read_database(database) if owns else connection
    try:
        if not db.in_transaction:
            db.execute('BEGIN')
        identity = db.execute('SELECT individual_id,started_at FROM experiment').fetchone()
        if identity is None:
            raise ValueError('No individual lifetime history')
        state_count, first, last = db.execute('SELECT COUNT(*),MIN(state_version),MAX(state_version) FROM states').fetchone()
        has_lifetime = db.execute("SELECT 1 FROM sqlite_master WHERE name='individual_lifetime'").fetchone()
        lifetime = db.execute('SELECT role,origin FROM individual_lifetime').fetchone() if has_lifetime else None
        result = {'A_lifetime_history': {'individual_id': identity[0], 'started_at': identity[1],
            'role': lifetime[0] if lifetime else 'legacy_independent_experiment',
            'origin': json.loads(lifetime[1]) if lifetime else None,
            'states': state_count, 'first_state_version': first, 'last_state_version': last,
            'events': db.execute('SELECT COUNT(*) FROM events').fetchone()[0]},
            'Experiment_session_history': []}
        current = current_metadata(db)
        result['A_lifetime_history'].update(current_state_version=current[0] if current else None,
            audit_coverage_end=last, audit_history_complete=not bool(audit_gaps(db)))
        if lifetime:
            for sid, label, env, start, end, began, ended, reason, interrupted, origin in db.execute(
                'SELECT s.session_id,s.label,s.environment,s.start_version,e.end_version,s.started_at,e.ended_at,e.reason,e.interrupted,s.origin '
                f'FROM sessions s LEFT JOIN {ends_table(db)} e USING(session_id) ORDER BY s.start_version,s.rowid'):
                counts = dict(db.execute('SELECT e.event_type,COUNT(*) FROM events e JOIN state_sessions ss USING(state_version) WHERE ss.session_id=? GROUP BY e.event_type', (sid,)))
                result['Experiment_session_history'].append({'session_id': sid, 'label': label,
                    'environment': json.loads(env), 'start_version': start, 'end_version': end,
                    'started_at': began, 'ended_at': ended, 'reason': reason,
                    'interrupted': bool(interrupted), 'origin': origin,
                    'full_history_enabled': session_mode(db, sid),
                    'event_counts': counts if session_mode(db, sid) else None})
        return result
    finally:
        if owns:
            db.close()


def fork_snapshot(source, snapshot_id, destination):
    """Create a distinct branch, carrying exact source history in an immutable namespace."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or destination.exists():
        raise ValueError('Branch destination must be a new, distinct database')
    with closing(read_database(source)) as parent:
        parent.execute('BEGIN')
        row = parent.execute('SELECT individual_id,state_version,snapshot_hash,snapshot FROM snapshots WHERE snapshot_id=?', (snapshot_id,)).fetchone()
        if row is None or sha256(row[3].encode()).hexdigest() != row[2]:
            raise ValueError('Snapshot missing or integrity check failed')
        owner, source_version, digest, raw = row
        original = parent.execute('SELECT snapshot FROM states WHERE state_version=?', (source_version,)).fetchone()
        if original is None or original[0] != raw:
            raise ValueError('Snapshot does not match original lifetime history')
        origin = {'kind': 'snapshot_branch', 'parent_individual_id': owner,
            'parent_state_version': source_version, 'snapshot_id': snapshot_id,
            'snapshot_hash': digest, 'source_database': str(source), 'original_mainline': False}
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents overwriting either an old branch or a concurrent creator.
        with destination.open('xb'):
            pass
        lease = ExperimentLease(destination).acquire()
        store = None
        try:
            store = EventStore(destination)
            db = store.connection
            db.executescript("""
                CREATE TABLE origin_history(kind TEXT NOT NULL,owner_id TEXT NOT NULL,
                    record_id TEXT NOT NULL,record TEXT NOT NULL CHECK(json_valid(record)),
                    PRIMARY KEY(kind,owner_id,record_id));
                CREATE TRIGGER immutable_origin_history_UPDATE BEFORE UPDATE ON origin_history
                BEGIN SELECT RAISE(ABORT,'append-only origin history'); END;
                CREATE TRIGGER immutable_origin_history_DELETE BEFORE DELETE ON origin_history
                BEGIN SELECT RAISE(ABORT,'append-only origin history'); END;
            """)
            with db:
                db.execute('BEGIN IMMEDIATE')
                if parent.execute("SELECT 1 FROM sqlite_master WHERE name='origin_history'").fetchone():
                    db.executemany('INSERT INTO origin_history VALUES(?,?,?,?)', parent.execute('SELECT * FROM origin_history'))
                exports = (
                    ('states', 'state_version', 'state_version<=?'),
                    ('events', 'event_id', 'state_version<=?'),
                    ('sessions', 'session_id', 'start_version<=?'),
                    ('session_ends', 'session_id', 'end_version<=?'),
                    ('state_sessions', 'state_version', 'state_version<=?'),
                    ('snapshots', 'snapshot_id', 'state_version<=?'))
                for table, key, condition in exports:
                    cursor = parent.execute(f'SELECT * FROM {table} WHERE {condition}', (source_version,))
                    names = [col[0] for col in cursor.description]
                    records = (dict(zip(names, values)) for values in cursor)
                    db.executemany('INSERT INTO origin_history VALUES(?,?,?,?)',
                        ((table, owner, str(record[key]), encode(record)) for record in records))
                now, branch_id, sid = utc_now(), new_individual_id(), f'S-{uuid4()}'
                seed = AState(**json.loads(raw))
                state = replace(seed, individual_id=branch_id, state_version=0, started_at=now,
                    last_update_at=now, status='dormant', session_id=sid,
                    carrier_epoch=max(seed.carrier_epoch, (seed.observation_frame or {}).get('body_epoch', 0)) + 1)
                db.execute('INSERT INTO experiment VALUES(1,?,?,1)', (branch_id, now))
                db.execute('INSERT INTO individual_lifetime VALUES(1,?,?,?,?)',
                    (branch_id, now, 'snapshot_branch', encode(origin)))
                db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?)',
                    (sid, branch_id, now, 0, 'snapshot seed', encode(origin), state.carrier_epoch, 'snapshot_branch'))
                store._insert_state(state)
                store._insert_event(state, 'INDIVIDUAL_BRANCH_CREATED', origin)
                store._insert_event(state, 'POLICY_REGISTRY_INHERITED', {'origin': origin,
                    'policy_migration_status': state.internal_state.get('policy_migration_status', {})})
                store._insert_event(state, 'SESSION_STARTED', {'session_id': sid, 'snapshot_seed': True})
                store._insert_event(state, 'SESSION_ENDED', {'session_id': sid, 'reason': 'snapshot_seed_saved', 'lifetime_ended': False})
                store._insert_event(state, 'STATE_UPDATED', {'from_version': None, 'to_version': 0, 'state': state.to_dict()})
                db.execute('INSERT INTO session_ends VALUES(?,?,?,?,0)', (sid, now, 0, 'snapshot_seed_saved'))
            return {'branch_database': str(destination), 'branch_individual_id': branch_id, **origin}
        finally:
            if store:
                store.close()
            lease.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', help='Existing lifetime or branch for read-only history / snapshot creation')
    commands = parser.add_subparsers(dest='command', required=True)
    initialize = commands.add_parser('initialize', help='Explicitly create and select a NEW individual in its own directory; retain old history')
    initialize.add_argument('--label', default='')
    initialize.add_argument('--replace-missing-selection', action='store_true',
        help='Explicit NEW A when the selected old database is missing; archive the old pointer, never claim resume')
    commands.add_parser('history')
    commands.add_parser('migrate')
    snap = commands.add_parser('snapshot')
    snap.add_argument('--version', type=int)
    snap.add_argument('--label', default='')
    fork = commands.add_parser('fork')
    fork.add_argument('--snapshot-id', required=True)
    fork.add_argument('--output', help='Optional explicit destination; otherwise create a separate individual directory')
    args = parser.parse_args()
    if args.command == 'initialize':
        if args.db:
            parser.error('initialize allocates a new individual directory; do not supply --db')
        from .storage import create_lifetime
        result = create_lifetime(label=args.label, replace_missing_selection=args.replace_missing_selection)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    database = Path(args.db).resolve() if args.db else resolve_runtime_database()
    if not database.is_file():
        parser.error('An existing lifetime database is required')
    if args.command == 'history':
        result = history_summary(database)
    elif args.command == 'fork':
        if args.output:
            result = fork_snapshot(database, args.snapshot_id, args.output)
        else:
            from .storage import create_branch
            result = create_branch(database, args.snapshot_id)
    elif args.command == 'snapshot':
        # This external artifact writer is not another A. SQLite serializes the insert;
        # a running Core keeps its lifetime lease and state chain.
        store = EventStore(database)
        try:
            result = {'snapshot_id': store.save_snapshot(args.version, args.label)}
        finally:
            store.close()
    else:
        lease = ExperimentLease(database).acquire()
        store = None
        try:
            store = EventStore(database)
            result = history_summary(database)
        finally:
            if store:
                store.close()
            lease.release()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
