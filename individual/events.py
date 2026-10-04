"""Append-only individual lifetime, with separate experiment sessions."""

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3
from uuid import uuid4

from .identity import new_individual_id
from .internal_state import InternalState
from .policies import PolicyRegistry
from .state import AState, utc_now


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


SCHEMA = """
CREATE TABLE IF NOT EXISTS experiment (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    individual_id TEXT NOT NULL UNIQUE,
    started_at TEXT NOT NULL,
    continuity_required INTEGER NOT NULL CHECK(continuity_required = 1)
);
CREATE TABLE IF NOT EXISTS states (
    state_version INTEGER PRIMARY KEY CHECK(state_version >= 0),
    individual_id TEXT NOT NULL REFERENCES experiment(individual_id),
    timestamp TEXT NOT NULL,
    snapshot TEXT NOT NULL CHECK(json_valid(snapshot))
);
CREATE TABLE IF NOT EXISTS events (
    event_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    individual_id TEXT NOT NULL REFERENCES experiment(individual_id),
    state_version INTEGER NOT NULL REFERENCES states(state_version),
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL CHECK(json_valid(payload))
);
CREATE INDEX IF NOT EXISTS events_by_version ON events(state_version, event_sequence);
CREATE TRIGGER IF NOT EXISTS contiguous_states BEFORE INSERT ON states
WHEN NEW.state_version != COALESCE((SELECT MAX(state_version) + 1 FROM states), 0)
BEGIN SELECT RAISE(ABORT, 'state_version must increase by one'); END;
CREATE TRIGGER IF NOT EXISTS matching_state_identity BEFORE INSERT ON states
WHEN NEW.individual_id != (SELECT individual_id FROM experiment WHERE singleton = 1)
BEGIN SELECT RAISE(ABORT, 'individual identity cannot change'); END;
CREATE TRIGGER IF NOT EXISTS matching_event_identity BEFORE INSERT ON events
WHEN NEW.individual_id != (SELECT individual_id FROM states WHERE state_version = NEW.state_version)
BEGIN SELECT RAISE(ABORT, 'event identity must match its state'); END;
"""

LIFETIME_SCHEMA = """
CREATE TABLE IF NOT EXISTS individual_lifetime (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    individual_id TEXT NOT NULL UNIQUE REFERENCES experiment(individual_id),
    started_at TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('mainline','snapshot_branch')),
    origin TEXT NOT NULL CHECK(json_valid(origin))
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    individual_id TEXT NOT NULL REFERENCES experiment(individual_id),
    started_at TEXT NOT NULL,
    start_version INTEGER NOT NULL,
    label TEXT NOT NULL,
    environment TEXT NOT NULL CHECK(json_valid(environment)),
    carrier_epoch INTEGER NOT NULL,
    origin TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session_ends (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
    ended_at TEXT NOT NULL,
    end_version INTEGER NOT NULL REFERENCES states(state_version),
    reason TEXT NOT NULL,
    interrupted INTEGER NOT NULL CHECK(interrupted IN (0,1))
);
CREATE TABLE IF NOT EXISTS state_sessions (
    state_version INTEGER PRIMARY KEY REFERENCES states(state_version),
    session_id TEXT REFERENCES sessions(session_id)
);
CREATE INDEX IF NOT EXISTS states_by_session ON state_sessions(session_id,state_version);
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    individual_id TEXT NOT NULL REFERENCES experiment(individual_id),
    state_version INTEGER NOT NULL REFERENCES states(state_version),
    created_at TEXT NOT NULL,
    label TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    snapshot TEXT NOT NULL CHECK(json_valid(snapshot))
);
CREATE TRIGGER IF NOT EXISTS one_open_session BEFORE INSERT ON sessions
WHEN EXISTS(SELECT 1 FROM sessions s LEFT JOIN session_ends e USING(session_id) WHERE e.session_id IS NULL)
BEGIN SELECT RAISE(ABORT,'Only one session may be active'); END;
CREATE TRIGGER IF NOT EXISTS session_identity BEFORE INSERT ON sessions
WHEN NEW.individual_id != (SELECT individual_id FROM experiment WHERE singleton=1)
BEGIN SELECT RAISE(ABORT,'Session cannot replace lifetime identity'); END;
CREATE TRIGGER IF NOT EXISTS lifetime_identity BEFORE INSERT ON individual_lifetime
WHEN NEW.individual_id != (SELECT individual_id FROM experiment WHERE singleton=1)
BEGIN SELECT RAISE(ABORT,'Lifetime identity must match history'); END;
CREATE TRIGGER IF NOT EXISTS state_session_identity BEFORE INSERT ON state_sessions
WHEN NEW.session_id IS NOT NULL AND
 (SELECT individual_id FROM states WHERE state_version=NEW.state_version) !=
 (SELECT individual_id FROM sessions WHERE session_id=NEW.session_id)
BEGIN SELECT RAISE(ABORT,'State/session identity mismatch'); END;
CREATE TRIGGER IF NOT EXISTS matching_snapshot BEFORE INSERT ON snapshots
WHEN NEW.individual_id != (SELECT individual_id FROM states WHERE state_version=NEW.state_version)
 OR NEW.snapshot != (SELECT snapshot FROM states WHERE state_version=NEW.state_version)
BEGIN SELECT RAISE(ABORT,'Snapshot must match its historical state'); END;
"""


class EventStore:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute('PRAGMA foreign_keys = ON')
        self.connection.execute('PRAGMA journal_mode = WAL')
        self.connection.execute('PRAGMA synchronous = FULL')
        self.connection.executescript(SCHEMA)
        self.connection.executescript(LIFETIME_SCHEMA)
        for table in ('experiment', 'states', 'events', 'individual_lifetime', 'sessions',
                      'session_ends', 'state_sessions', 'snapshots'):
            for operation in ('UPDATE', 'DELETE'):
                self.connection.execute(f"""CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation}
                    BEFORE {operation} ON {table}
                    BEGIN SELECT RAISE(ABORT, 'append-only history'); END""")
        self.connection.commit()
        self._import_legacy_lifetime()

    def _import_legacy_lifetime(self):
        """Add metadata only; never rewrite old states, events, IDs or provenance."""
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            if self.connection.execute('SELECT 1 FROM individual_lifetime').fetchone():
                return
            identity = self.connection.execute('SELECT individual_id,started_at FROM experiment').fetchone()
            if identity is None:
                return
            row = self.connection.execute('SELECT state_version,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
            if row is None:
                raise ValueError('Identity has no committed lifetime history')
            last = json.loads(row[1])
            epoch = max(last.get('carrier_epoch', 0), (last.get('observation_frame') or {}).get('body_epoch', 0))
            self.connection.execute('INSERT INTO individual_lifetime VALUES(1,?,?,?,?)',
                (*identity, 'mainline', encode({'kind': 'legacy_adoption', 'history_rewritten': False})))
            session_id = f'S-{uuid4()}'
            self.connection.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?)',
                (session_id, *identity, 0, 'legacy experiment', encode({'legacy': True}), epoch, 'legacy_import'))
            self.connection.execute('INSERT INTO state_sessions SELECT state_version,? FROM states', (session_id,))
            if last['status'] == 'stopped':
                self.connection.execute('INSERT INTO session_ends VALUES(?,?,?,?,?)',
                    (session_id, last['last_update_at'], row[0], 'legacy_experiment_stopped', 0))

    def latest_state(self):
        row = self.connection.execute('SELECT snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
        return AState(**json.loads(row[0])) if row else None

    def register_lifetime(self):
        """Explicit one-time registration; no world session or running carrier is created."""
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            if self.connection.execute('SELECT 1 FROM experiment').fetchone():
                raise ValueError('Lifetime already registered; identity cannot be regenerated')
            now, marker = utc_now(), new_individual_id()
            internal = InternalState()
            PolicyRegistry(internal).bind_experiment(marker, now)
            state = AState(marker, 0, now, now, status='registered', internal_state=internal.to_dict())
            self.connection.execute('INSERT INTO experiment VALUES(1,?,?,1)', (marker, now))
            self.connection.execute('INSERT INTO individual_lifetime VALUES(1,?,?,?,?)',
                (marker, now, 'mainline', encode({'kind': 'explicit_new_lifetime_registration'})))
            self._insert_state(state)
            self._insert_event(state, 'INDIVIDUAL_REGISTERED', {'runtime_started': False, 'continuity_required': True})
            self._insert_event(state, 'POLICY_REGISTRY_INITIALIZED', {
                'registry': internal.policy_registry, 'parameter_sources': internal.parameter_sources,
                'policy_migration_status': internal.policy_migration_status})
            self._insert_event(state, 'STATE_UPDATED', {'from_version': None, 'to_version': 0, 'state': state.to_dict()})
        return state

    def open_session(self, environment=None, label='Minecraft', carrier_restart=True, runtime_status='starting'):
        """Continue the lifetime; only the first opening creates an identity and A0."""
        environment = {} if environment is None else environment
        encode(environment)
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            previous = self.latest_state()
            first_carrier = previous is not None and previous.status == 'registered'
            now = utc_now()
            open_row = self.connection.execute('SELECT s.session_id FROM sessions s LEFT JOIN session_ends e USING(session_id) WHERE e.session_id IS NULL').fetchone()
            if open_row:
                interrupted = replace(previous, state_version=previous.state_version + 1,
                    last_update_at=now, session_id=open_row[0], status='session_interrupted')
                self._append_transition(previous, interrupted, 'SESSION_INTERRUPTED', {
                    'session_id': open_row[0], 'reason': 'previous_carrier_stopped_without_session_end',
                    'physical_continuity_proven': False})
                self.connection.execute('INSERT INTO session_ends VALUES(?,?,?,?,?)',
                    (open_row[0], now, interrupted.state_version, 'carrier_interruption', 1))
                previous = interrupted
            session_id = f'S-{uuid4()}'
            if previous is None:
                individual_id = new_individual_id()
                internal = InternalState()
                PolicyRegistry(internal).bind_experiment(individual_id, now)
                state = AState(individual_id, 0, now, now, internal_state=internal.to_dict(), session_id=session_id)
                self.connection.execute('INSERT INTO experiment VALUES(1,?,?,1)', (individual_id, now))
                self.connection.execute('INSERT INTO individual_lifetime VALUES(1,?,?,?,?)',
                    (individual_id, now, 'mainline', encode({'kind': 'initial_creation'})))
            else:
                epoch = max(previous.carrier_epoch, (previous.observation_frame or {}).get('body_epoch', 0)) + 1
                state = replace(previous, state_version=previous.state_version + 1, last_update_at=now,
                    session_id=session_id, carrier_epoch=epoch, status=runtime_status)
            self.connection.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?)',
                (session_id, state.individual_id, now, state.state_version, label,
                 encode(environment), state.carrier_epoch, 'carrier_restart' if previous and carrier_restart and not first_carrier else 'session_start'))
            payload = {'session_id': session_id, 'environment': environment, 'label': label,
                       'resumed_lifetime': previous is not None,
                       'previous_state_version': previous.state_version if previous else None,
                       'carrier_restart': bool(previous and carrier_restart and not first_carrier),
                       'physical_continuity_proven': False if previous and carrier_restart and not first_carrier else None}
            if previous is None:
                self._insert_state(state)
                self._insert_event(state, 'INDIVIDUAL_STARTED', {'continuity_required': True, 'restored': False})
                self._insert_event(state, 'POLICY_REGISTRY_INITIALIZED', {
                    'registry': internal.policy_registry, 'parameter_sources': internal.parameter_sources,
                    'policy_migration_status': internal.policy_migration_status})
                self._insert_event(state, 'SESSION_STARTED', payload)
                self._insert_event(state, 'STATE_UPDATED', {'from_version': None, 'to_version': 0, 'state': state.to_dict()})
            else:
                self._append_transition(previous, state, 'SESSION_STARTED', payload,
                    [('INDIVIDUAL_STARTED', {'first_runtime_session': True})] if first_carrier else [])
        return state

    def create_initial_state(self):
        # Compatibility entry: a session opening never resets an existing lifetime.
        return self.open_session()

    def _insert_state(self, state):
        self.connection.execute('INSERT INTO states VALUES (?, ?, ?, ?)',
                                (state.state_version, state.individual_id, state.last_update_at, encode(state.to_dict())))
        self.connection.execute('INSERT INTO state_sessions VALUES(?,?)', (state.state_version, state.session_id))

    def _append_transition(self, previous, current, event_type, payload, additional_events=()):
        self._insert_state(current)
        self._insert_event(current, event_type, payload)
        for kind, details in additional_events:
            self._insert_event(current, kind, details)
        self._insert_event(current, 'STATE_UPDATED', {'from_version': previous.state_version,
            'to_version': current.state_version, 'state': current.to_dict()})

    def _insert_event(self, state, event_type, payload):
        self.connection.execute('INSERT INTO events(event_id,timestamp,individual_id,state_version,event_type,payload) VALUES (?,?,?,?,?,?)',
                                (str(uuid4()), state.last_update_at, state.individual_id, state.state_version, event_type, encode(payload)))

    def transition(self, previous, current, event_type, payload, additional_events=()):
        if current.individual_id != previous.individual_id or current.started_at != previous.started_at or not current.continuity_required:
            raise ValueError('Identity and experiment definition cannot change')
        if current.state_version != previous.state_version + 1:
            raise ValueError('state_version must increase by one')
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            last = self.connection.execute('SELECT MAX(state_version) FROM states').fetchone()[0]
            if last != previous.state_version:
                raise ValueError('Stale state transition')
            self._append_transition(previous, current, event_type, payload, additional_events)

    def end_session(self, previous, reason, carrier_stop=False):
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            if self.latest_state().state_version != previous.state_version:
                raise ValueError('Stale session end')
            if not previous.session_id or self.connection.execute('SELECT 1 FROM session_ends WHERE session_id=?', (previous.session_id,)).fetchone():
                return previous
            state = replace(previous, state_version=previous.state_version + 1, last_update_at=utc_now(),
                status='dormant' if carrier_stop else 'between_sessions')
            self._append_transition(previous, state, 'SESSION_ENDED', {
                'session_id': previous.session_id, 'reason': reason, 'carrier_stop': carrier_stop,
                'internal_state_preserved': True, 'lifetime_ended': False,
                'physical_continuity_after_carrier_stop': 'unproven' if carrier_stop else 'carrier_running'})
            self.connection.execute('INSERT INTO session_ends VALUES(?,?,?,?,?)',
                (previous.session_id, state.last_update_at, state.state_version, reason, 0))
        return state

    def save_snapshot(self, version=None, label=''):
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            if version is None:
                version = self.latest_state().state_version
            row = self.connection.execute('SELECT individual_id,snapshot FROM states WHERE state_version=?', (version,)).fetchone()
            if row is None:
                raise ValueError('Unknown historical state version')
            snapshot_id = f'SNAP-{uuid4()}'
            self.connection.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?)',
                (snapshot_id, row[0], version, utc_now(), label, sha256(row[1].encode()).hexdigest(), row[1]))
        return snapshot_id

    def close(self):
        self.connection.close()

