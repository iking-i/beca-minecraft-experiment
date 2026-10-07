"""Read-only audit of persisted state chains; never starts or restores A."""

import argparse
import json
from pathlib import Path
import sqlite3
from .current_state import audit_gaps, current_metadata, ends_table, session_mode


def verify(database, connection=None):
    path = Path(database).resolve()
    owns_connection = connection is None
    if owns_connection:
        connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        if not connection.in_transaction:
            connection.execute('BEGIN')  # One consistent snapshot, also while A is running.
        identity = connection.execute('SELECT individual_id FROM experiment').fetchone()
        if not identity:
            raise ValueError('No experiment identity')
        gaps = audit_gaps(connection)
        current = current_metadata(connection)
        if gaps:
            off_intervals = connection.execute(
                f'SELECT s.start_version,COALESCE(e.end_version,?) FROM sessions s '
                f'JOIN session_recording_modes m USING(session_id) LEFT JOIN {ends_table(connection)} e USING(session_id) '
                'WHERE m.full_history_enabled=0 ORDER BY s.start_version', (current[0],)).fetchall()
            for first, last in gaps:
                boundary = first
                for start, end in off_intervals:
                    if end < boundary:
                        continue
                    if start > boundary:
                        break
                    boundary = end + 1
                    if boundary > last:
                        break
                if boundary <= last:
                    raise ValueError('Audit gap is not covered by Full History OFF sessions')
        def omitted(start, end):
            if start > end:
                return True
            for first, last in gaps:
                if last < start:
                    continue
                if first > start:
                    return False
                start = last + 1
                if start > end:
                    return True
            return False
        previous = -1
        observations = 0
        has_lifetime = connection.execute("SELECT 1 FROM sqlite_master WHERE name='individual_lifetime'").fetchone()
        role_row = connection.execute('SELECT role,origin FROM individual_lifetime').fetchone() if has_lifetime else None
        initial_row = connection.execute('SELECT snapshot FROM states WHERE state_version=0').fetchone()
        branch_base = json.loads(initial_row[0])['environment_sequence'] if role_row and role_row[0] == 'snapshot_branch' else 0
        if role_row and role_row[0] == 'snapshot_branch':
            origin = json.loads(role_row[1])
            source = connection.execute("SELECT record FROM origin_history WHERE kind='states' AND owner_id=? AND record_id=?",
                (origin['parent_individual_id'], str(origin['parent_state_version']))).fetchone()
            if source is None:
                raise ValueError('Branch has no preserved snapshot origin')
            parent_state = json.loads(json.loads(source[0])['snapshot'])
            if parent_state['environment_sequence'] != branch_base or identity[0] == origin['parent_individual_id']:
                raise ValueError('Branch cannot impersonate original lifetime')
        states = 0
        last_environment_sequence = branch_base
        for version, individual_id, raw in connection.execute('SELECT state_version,individual_id,snapshot FROM states ORDER BY state_version'):
            state = json.loads(raw)
            skipped = version != previous + 1
            if ((skipped and not omitted(previous+1, version-1)) or omitted(version, version)
                    or individual_id != identity[0] or state['individual_id'] != individual_id or state['state_version'] != version):
                raise ValueError(f'Broken state chain at A{version}')
            if role_row:
                session = connection.execute('SELECT session_id FROM state_sessions WHERE state_version=?', (version,)).fetchone()
                if session is None or (state.get('session_id') is not None and session[0] != state['session_id']):
                    raise ValueError(f'Broken session association at A{version}')
            updates = connection.execute("SELECT payload FROM events WHERE state_version=? AND event_type='STATE_UPDATED'", (version,)).fetchall()
            if len(updates) != 1:
                raise ValueError(f'Missing or duplicate STATE_UPDATED for A{version}')
            update = json.loads(updates[0][0])
            if update['state'] != state or update['to_version'] != version or update['from_version'] != (version-1 if version else None):
                raise ValueError(f'Event/snapshot mismatch at A{version}')
            world_inputs = connection.execute("SELECT COUNT(*) FROM events WHERE state_version=? AND event_type='WORLD_OBSERVATION'", (version,)).fetchone()[0]
            observations += world_inputs
            expected_sequence = last_environment_sequence + world_inputs
            if ((not skipped and state['environment_sequence'] != expected_sequence)
                    or (skipped and state['environment_sequence'] < expected_sequence)
                    or state['continuity_required'] is not True):
                raise ValueError(f'Broken environment sequence at A{version}')
            last_environment_sequence = state['environment_sequence']
            previous = version
            states += 1
        if states == 0 and not gaps:
            raise ValueError('No states')
        if current and current[0] < previous:
            raise ValueError('Current state is behind recorded history')
        if current and current[0] > previous and not omitted(previous+1, current[0]):
            raise ValueError('Current state ahead of history without declared audit gap')
        if any(first > last or first < 0 or not current or last > current[0] for first,last in gaps):
            raise ValueError('Invalid audit gap metadata')
        if role_row:
            for sid, start, end in connection.execute(f'SELECT s.session_id,s.start_version,e.end_version FROM sessions s LEFT JOIN {ends_table(connection)} e USING(session_id)'):
                limit = current[0] if not session_mode(connection, sid) else previous
                if start > limit or (end is not None and (end < start or end > limit)):
                    raise ValueError('Session bounds are outside lifetime history')
        result = {'valid_state_chain': not bool(gaps), 'individual_id': identity[0], 'states': states,
                'last_state_version': previous, 'observations': observations,
                'events': connection.execute('SELECT COUNT(*) FROM events').fetchone()[0],
                'subject_continuity_after_stop': 'not established by storage alone'}
        result.update(audit_history_complete=not bool(gaps), recorded_segments_verified=True,
            audit_gaps=[{'start_version': a,'end_version': b,'reason': 'FULL_HISTORY_OFF'} for a,b in gaps],
            audit_coverage_end=previous if states else None,
            current_state_version=current[0] if current else None)
        if has_lifetime:
            from .lifetime import history_summary
            result.update(history_summary(database, connection))
        return result
    finally:
        if owns_connection:
            connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', help='Defaults to the selected individual lifetime')
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--limit', type=int, default=30)
    args = parser.parse_args()
    if args.db is None:
        from .lifetime import resolve_runtime_database
        args.db = str(resolve_runtime_database())
    result = verify(args.db)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.history:
        connection = sqlite3.connect(Path(args.db).resolve().as_uri() + '?mode=ro', uri=True)
        try:
            for version, kind, timestamp in connection.execute('SELECT state_version,event_type,timestamp FROM events ORDER BY event_sequence LIMIT ?', (args.limit,)):
                print(f'A{version:<6} {kind:<26} {timestamp}')
        finally:
            connection.close()


if __name__ == '__main__':
    main()
