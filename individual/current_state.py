"""Persistence boundary only. Current snapshots are not audit-history evidence."""


def has_table(db, name):
    return db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone() is not None


def current_row(db):
    """Authoritative row; legacy read-only fallback only before migration."""
    if has_table(db, 'current_state'):
        row = db.execute('SELECT state_version,individual_id,timestamp,snapshot FROM current_state WHERE singleton=1').fetchone()
        if row is None and db.execute('SELECT 1 FROM experiment WHERE singleton=1').fetchone():
            raise ValueError('Authoritative current state is missing; refusing historical fallback')
        return row
    return db.execute('SELECT state_version,individual_id,timestamp,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()


def current_metadata(db):
    table = 'current_state' if has_table(db, 'current_state') else 'states'
    if table == 'current_state':
        row = db.execute('SELECT state_version,timestamp FROM current_state WHERE singleton=1').fetchone()
        if row is None and db.execute('SELECT 1 FROM experiment WHERE singleton=1').fetchone():
            raise ValueError('Authoritative current state is missing')
        return row
    return db.execute('SELECT state_version,timestamp FROM states ORDER BY state_version DESC LIMIT 1').fetchone()


def current_query(db):
    """Shared SQL source for current-state-only readers, including legacy tools."""
    if has_table(db, 'current_state'):
        return 'current_state WHERE singleton=1'
    return 'states ORDER BY state_version DESC LIMIT 1'


def ends_table(db):
    return 'session_lifecycle_ends' if has_table(db, 'session_lifecycle_ends') else 'session_ends'


def session_mode(db, session_id):
    if has_table(db, 'session_recording_modes'):
        row = db.execute('SELECT full_history_enabled FROM session_recording_modes WHERE session_id=?', (session_id,)).fetchone()
        if row:
            return bool(row[0])
    return True  # Pre-option lifetimes recorded full audit history.


def audit_gaps(db):
    if not has_table(db, 'audit_gaps'):
        return []
    return db.execute('SELECT start_version,end_version FROM audit_gaps ORDER BY start_version').fetchall()


SCHEMA = """
CREATE TABLE IF NOT EXISTS current_state (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 state_version INTEGER NOT NULL CHECK(state_version>=0),
 individual_id TEXT NOT NULL REFERENCES experiment(individual_id),
 timestamp TEXT NOT NULL,
 snapshot TEXT NOT NULL CHECK(json_valid(snapshot)),
 full_history_enabled INTEGER NOT NULL CHECK(full_history_enabled IN (0,1)),
 CHECK(json_extract(snapshot,'$.individual_id') IS individual_id),
 CHECK(json_extract(snapshot,'$.state_version') IS state_version),
 CHECK(json_extract(snapshot,'$.last_update_at') IS timestamp),
 CHECK(json_extract(snapshot,'$.continuity_required') IS 1)
);
CREATE TABLE IF NOT EXISTS session_recording_modes (
 session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
 full_history_enabled INTEGER NOT NULL CHECK(full_history_enabled IN (0,1))
);
CREATE TABLE IF NOT EXISTS reduced_session_ends (
 session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
 ended_at TEXT NOT NULL, end_version INTEGER NOT NULL,
 reason TEXT NOT NULL, interrupted INTEGER NOT NULL CHECK(interrupted IN (0,1))
);
CREATE VIEW IF NOT EXISTS session_lifecycle_ends AS
 SELECT * FROM session_ends UNION ALL SELECT * FROM reduced_session_ends;
CREATE TABLE IF NOT EXISTS audit_gaps (
 start_version INTEGER PRIMARY KEY CHECK(start_version>=0),
 end_version INTEGER NOT NULL CHECK(end_version>=start_version)
);
CREATE TRIGGER IF NOT EXISTS current_identity_insert BEFORE INSERT ON current_state
WHEN NEW.individual_id IS NOT (SELECT individual_id FROM experiment WHERE singleton=1)
 OR json_extract(NEW.snapshot,'$.started_at') IS NOT (SELECT started_at FROM experiment WHERE singleton=1)
 OR NEW.state_version != COALESCE((SELECT MAX(state_version) FROM states),0)
BEGIN SELECT RAISE(ABORT,'Invalid current-state initialization'); END;
CREATE TRIGGER IF NOT EXISTS current_identity_update BEFORE UPDATE ON current_state
WHEN NEW.singleton != OLD.singleton OR NEW.individual_id != OLD.individual_id
 OR NEW.state_version != OLD.state_version+1
 OR json_extract(NEW.snapshot,'$.started_at') IS NOT (SELECT started_at FROM experiment WHERE singleton=1)
BEGIN SELECT RAISE(ABORT,'Current-state identity/version cannot change discontinuously'); END;
CREATE TRIGGER IF NOT EXISTS current_session_insert BEFORE INSERT ON current_state
WHEN json_extract(NEW.snapshot,'$.session_id') IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM sessions WHERE session_id=json_extract(NEW.snapshot,'$.session_id')
 AND individual_id=NEW.individual_id AND start_version<=NEW.state_version)
BEGIN SELECT RAISE(ABORT,'Current-state session identity mismatch'); END;
CREATE TRIGGER IF NOT EXISTS current_session_update BEFORE UPDATE ON current_state
WHEN json_extract(NEW.snapshot,'$.session_id') IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM sessions WHERE session_id=json_extract(NEW.snapshot,'$.session_id')
 AND individual_id=NEW.individual_id AND start_version<=NEW.state_version)
BEGIN SELECT RAISE(ABORT,'Current-state session identity mismatch'); END;
CREATE TRIGGER IF NOT EXISTS current_no_delete BEFORE DELETE ON current_state
BEGIN SELECT RAISE(ABORT,'Current state must persist'); END;
CREATE TRIGGER IF NOT EXISTS gap_no_delete BEFORE DELETE ON audit_gaps
BEGIN SELECT RAISE(ABORT,'Audit coverage metadata must persist'); END;
CREATE TRIGGER IF NOT EXISTS gap_insert BEFORE INSERT ON audit_gaps
WHEN NEW.start_version != NEW.end_version
 OR NEW.end_version IS NOT (SELECT state_version FROM current_state WHERE singleton=1 AND full_history_enabled=0)
BEGIN SELECT RAISE(ABORT,'Invalid audit omission boundary'); END;
CREATE TRIGGER IF NOT EXISTS gap_update BEFORE UPDATE ON audit_gaps
WHEN NEW.start_version != OLD.start_version OR NEW.end_version != OLD.end_version+1
 OR NEW.end_version IS NOT (SELECT state_version FROM current_state WHERE singleton=1 AND full_history_enabled=0)
BEGIN SELECT RAISE(ABORT,'Invalid audit omission extension'); END;
CREATE TRIGGER IF NOT EXISTS current_locked_caps BEFORE UPDATE ON current_state
WHEN (json_extract(OLD.snapshot,'$.internal_state.l0_state.locked_caps') IS NOT NULL AND (
 json_extract(NEW.snapshot,'$.internal_state.l0_state.locked_caps') IS NOT json_extract(OLD.snapshot,'$.internal_state.l0_state.locked_caps')
 OR json_extract(NEW.snapshot,'$.internal_state.l0_state.locked_resource_caps') IS NOT json_extract(OLD.snapshot,'$.internal_state.l0_state.locked_resource_caps')
 OR json_extract(NEW.snapshot,'$.internal_state.l0_state.formal_condition_id') IS NOT json_extract(OLD.snapshot,'$.internal_state.l0_state.formal_condition_id')
 OR json_extract(NEW.snapshot,'$.internal_state.l0_state.baseline_version') IS NOT json_extract(OLD.snapshot,'$.internal_state.l0_state.baseline_version')))
 OR (json_extract(OLD.snapshot,'$.internal_state.l0_state.froi_boundary') IS NOT NULL AND
 json_extract(NEW.snapshot,'$.internal_state.l0_state.froi_boundary') IS NOT json_extract(OLD.snapshot,'$.internal_state.l0_state.froi_boundary'))
BEGIN SELECT RAISE(ABORT,'locked formal capacities cannot change'); END;
"""


def install(db):
    """Create/backfill at writer startup. Old state/event rows are never changed."""
    existed = has_table(db, 'current_state')
    # DDL, backfill and replacement guards commit together, including on failure.
    db.executescript('BEGIN IMMEDIATE;\n' + SCHEMA)
    try:
        if not existed:
            identity = db.execute('SELECT individual_id FROM experiment WHERE singleton=1').fetchone()
            if identity:
                from .startup_validation import verify_startup_boundary
                # Validate legacy snapshot and current commit before adopting it.
                role = db.execute('SELECT role FROM individual_lifetime WHERE singleton=1').fetchone()[0]
                verify_startup_boundary(None, identity[0], db, legacy=True, role=role)
                row = db.execute('SELECT state_version,individual_id,timestamp,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
                db.execute('INSERT INTO current_state VALUES(1,?,?,?,?,1)', row)
        elif db.execute('SELECT 1 FROM experiment WHERE singleton=1').fetchone():
            current_row(db)  # An empty authoritative store is corruption, not migration.
        for table in ('session_recording_modes', 'reduced_session_ends'):
            for operation in ('UPDATE', 'DELETE'):
                db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'immutable recording metadata'); END")
        db.execute('DROP TRIGGER IF EXISTS contiguous_states')
        db.execute("""CREATE TRIGGER contiguous_states BEFORE INSERT ON states
            WHEN NEW.state_version IS NOT (SELECT state_version FROM current_state WHERE singleton=1)
              OR NEW.snapshot IS NOT (SELECT snapshot FROM current_state WHERE singleton=1)
            BEGIN SELECT RAISE(ABORT,'History must match current committed transition'); END""")
        db.execute('DROP TRIGGER IF EXISTS one_open_session')
        db.execute("""CREATE TRIGGER one_open_session BEFORE INSERT ON sessions
            WHEN EXISTS(SELECT 1 FROM sessions s LEFT JOIN session_lifecycle_ends e USING(session_id) WHERE e.session_id IS NULL)
            BEGIN SELECT RAISE(ABORT,'Only one session may be active'); END""")
        for table, other in (('session_ends','reduced_session_ends'),('reduced_session_ends','session_ends')):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS unique_{table}_end BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {other} WHERE session_id=NEW.session_id) BEGIN SELECT RAISE(ABORT,'Session already ended'); END")
        db.commit()
    except BaseException:
        db.rollback()
        raise


def persist(db, state, enabled, encode):
    """Called inside the owning transition's transaction, never independently."""
    if not db.in_transaction:
        raise RuntimeError('Current state must commit inside the transition transaction')
    raw = encode(state.to_dict())
    if db.execute('SELECT 1 FROM current_state WHERE singleton=1').fetchone():
        db.execute('UPDATE current_state SET state_version=?,individual_id=?,timestamp=?,snapshot=?,full_history_enabled=? WHERE singleton=1',
                   (state.state_version,state.individual_id,state.last_update_at,raw,int(enabled)))
    else:
        db.execute('INSERT INTO current_state VALUES(1,?,?,?,?,?)',
                   (state.state_version,state.individual_id,state.last_update_at,raw,int(enabled)))
    if not enabled:
        previous = db.execute('SELECT start_version,end_version FROM audit_gaps ORDER BY start_version DESC LIMIT 1').fetchone()
        if previous and previous[1] == state.state_version-1:
            db.execute('UPDATE audit_gaps SET end_version=? WHERE start_version=?', (state.state_version,previous[0]))
        else:
            db.execute('INSERT INTO audit_gaps VALUES(?,?)', (state.state_version,state.state_version))
