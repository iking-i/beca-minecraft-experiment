"""External current-boundary validation, deliberately NOT a lifetime integrity audit.

Only the latest snapshot and its identity/session metadata are read. Historical
transitions, event totals and old snapshots belong to individual.inspect.verify.
"""
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import sqlite3

from .state import AState
from .current_state import current_row, has_table, ends_table, session_mode


def _timestamp(value):
    if not isinstance(value, str) or not value or datetime.fromisoformat(value).tzinfo is None:
        raise ValueError('Invalid current-state timestamp')


def _counter(value):
    if type(value) is not int or value < 0:
        raise ValueError('Invalid current-state counter')


def preflight_current_caps(database, caps, resource_caps=None):
    """Current-state restore adapter; the frozen formal cap rules remain unchanged.

    The historical formal_boundary.preflight still belongs to its frozen source
    environment. Normal startup uses this adapter and its existing validator.
    """
    from .formal_boundary import validate_boundary
    path = Path(database).resolve()
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not has_table(db, 'states'):
            return
        row = current_row(db)
        if row:
            internal = json.loads(row[3]).get('internal_state') or {}
            if caps is None:
                if internal.get('l0_state', {}).get('locked_caps') or internal.get('l0_state', {}).get('profile') == 'formal_l0':
                    raise ValueError('Formal lifetime cannot resume through legacy adaptation; use an independent debug fixture')
            else:
                validate_boundary(internal, caps, resource_caps)


def verify_startup_boundary(database, individual_id, connection=None, *, legacy=False, role='mainline'):
    """Read-only mainline preflight; never claims full historical verification.

    A caller-supplied connection permits SQL tracing in isolated tests. A read
    transaction keeps the latest snapshot and its metadata at the same boundary.
    """
    if connection is None:
        path = Path(database).resolve()
        wal = Path(str(path) + '-wal')
        flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
        with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
            return verify_startup_boundary(database, individual_id, db, legacy=legacy, role=role)
    db = connection
    if not db.in_transaction:
        db.execute('BEGIN')
    identity = db.execute('SELECT individual_id,started_at,continuity_required FROM experiment WHERE singleton=1').fetchone()
    lifetime = db.execute('SELECT individual_id,started_at,role,origin FROM individual_lifetime WHERE singleton=1').fetchone()
    if not identity or not lifetime or identity[0] != individual_id or lifetime[0] != individual_id:
        raise ValueError('Database identity differs from lifetime manifest')
    if lifetime[2] != role or lifetime[1] != identity[1] or identity[2] != 1:
        raise ValueError('Invalid mainline lifetime/continuity metadata')
    _timestamp(identity[1])
    origin = json.loads(lifetime[3])
    authoritative = not legacy and has_table(db, 'current_state')
    row = current_row(db) if authoritative else db.execute('SELECT state_version,individual_id,timestamp,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
    if not row:
        raise ValueError('No latest lawful snapshot')
    snapshot = json.loads(row[3])
    if not isinstance(snapshot, dict):
        raise ValueError('Latest snapshot must be an object')
    try:
        state = AState(**snapshot)
    except TypeError as error:
        raise ValueError('Invalid latest snapshot schema') from error
    _counter(state.state_version)
    _counter(state.environment_sequence)
    _counter(state.carrier_epoch)
    _timestamp(state.started_at)
    _timestamp(state.last_update_at)
    if (state.individual_id != individual_id or row[1] != individual_id or
            state.state_version != row[0] or state.started_at != identity[1] or
            state.last_update_at != row[2] or state.continuity_required is not True or
            not isinstance(state.internal_state, dict) or not isinstance(state.status, str)):
        raise ValueError('Latest snapshot identity/continuity metadata mismatch')
    # Validate the current commit only, using events_by_version. Never iterate
    # historical STATE_UPDATED records or count lifetime observations/events.
    if not authoritative:
        updates = db.execute("SELECT individual_id,payload FROM events WHERE state_version=? "
                             "AND event_type='STATE_UPDATED' LIMIT 2", (state.state_version,)).fetchall()
        if len(updates) != 1 or updates[0][0] != individual_id:
            raise ValueError('Missing or duplicate latest STATE_UPDATED')
        update = json.loads(updates[0][1])
        if (not isinstance(update, dict) or update.get('state') != snapshot or
                update.get('to_version') != state.state_version or
                update.get('from_version') != (state.state_version - 1 if state.state_version else None)):
            raise ValueError('Latest event/snapshot commit mismatch')
        association = db.execute('SELECT session_id FROM state_sessions WHERE state_version=?', (state.state_version,)).fetchone()
        legacy_adoption = state.session_id is None and origin.get('kind') == 'legacy_adoption'
        if association is None or (association[0] != state.session_id and not legacy_adoption):
            raise ValueError('Latest state/session association mismatch')
    session_status = None
    if state.session_id is not None:
        if not isinstance(state.session_id, str) or not state.session_id:
            raise ValueError('Invalid current session identity')
        session = db.execute('SELECT individual_id,started_at,start_version,carrier_epoch FROM sessions WHERE session_id=?', (state.session_id,)).fetchone()
        if not session or session[0] != individual_id:
            raise ValueError('Latest session identity mismatch')
        _timestamp(session[1])
        _counter(session[2])
        _counter(session[3])
        # sessions.carrier_epoch is the opening epoch. Body reconnects can advance
        # the latest state epoch within that same session (Core's existing rule).
        if session[2] > state.state_version or session[3] > state.carrier_epoch:
            raise ValueError('Invalid latest session boundary')
        end = db.execute(f'SELECT ended_at,end_version FROM {ends_table(db)} WHERE session_id=?', (state.session_id,)).fetchone()
        if end:
            _timestamp(end[0])
            _counter(end[1])
            if not session[2] <= end[1] <= state.state_version:
                raise ValueError('Invalid latest session end boundary')
        session_status = 'ended' if end else 'open'
    return {'individual_id': individual_id, 'role': lifetime[2], 'started_at': identity[1],
            'state_version': state.state_version, 'session_id': state.session_id,
            'session_status': session_status,
            'session_count': db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],
            'full_history_enabled': session_mode(db, state.session_id),
            'restore_source': 'CURRENT_STATE' if authoritative else 'LEGACY_LATEST_SNAPSHOT',
            'full_history_verification': 'NOT_RUN'}
