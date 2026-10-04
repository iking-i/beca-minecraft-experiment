"""Read-only audit of persisted state chains; never starts or restores A."""

import argparse
import json
from pathlib import Path
import sqlite3


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
        for version, individual_id, raw in connection.execute('SELECT state_version,individual_id,snapshot FROM states ORDER BY state_version'):
            state = json.loads(raw)
            if version != previous + 1 or individual_id != identity[0] or state['individual_id'] != individual_id or state['state_version'] != version:
                raise ValueError(f'Broken state chain at A{version}')
            if role_row:
                session = connection.execute('SELECT session_id FROM state_sessions WHERE state_version=?', (version,)).fetchone()
                if session is None or (state.get('session_id') is not None and session[0] != state['session_id']):
                    raise ValueError(f'Broken session association at A{version}')
            updates = connection.execute("SELECT payload FROM events WHERE state_version=? AND event_type='STATE_UPDATED'", (version,)).fetchall()
            if len(updates) != 1:
                raise ValueError(f'Missing or duplicate STATE_UPDATED for A{version}')
            update = json.loads(updates[0][0])
            if update['state'] != state or update['to_version'] != version or update['from_version'] != (previous if previous >= 0 else None):
                raise ValueError(f'Event/snapshot mismatch at A{version}')
            world_inputs = connection.execute("SELECT COUNT(*) FROM events WHERE state_version=? AND event_type='WORLD_OBSERVATION'", (version,)).fetchone()[0]
            observations += world_inputs
            if state['environment_sequence'] != branch_base + observations or state['continuity_required'] is not True:
                raise ValueError(f'Broken environment sequence at A{version}')
            previous = version
            states += 1
        if states == 0:
            raise ValueError('No states')
        if role_row:
            for start, end in connection.execute('SELECT s.start_version,e.end_version FROM sessions s LEFT JOIN session_ends e USING(session_id)'):
                if start > previous or (end is not None and (end < start or end > previous)):
                    raise ValueError('Session bounds are outside lifetime history')
        result = {'valid_state_chain': True, 'individual_id': identity[0], 'states': states,
                'last_state_version': previous, 'observations': observations,
                'events': connection.execute('SELECT COUNT(*) FROM events').fetchone()[0],
                'subject_continuity_after_stop': 'not established by storage alone'}
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
