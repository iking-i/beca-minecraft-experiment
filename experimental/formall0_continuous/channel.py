"""Versioned admission guard, not a formation law or separate executor."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from individual.current_state import current_row
from individual.internal_state import InternalState

VERSION = 'FORMALL0-OPERATIVE-CORE-TEST_ONLY-1'
KEY = 'operative_core_test_only'


def session_metadata(database):
    return {'mode': 'TEST_ONLY', 'mechanism_version': VERSION,
            'database': str(Path(database).resolve())}


@dataclass(frozen=True)
class TestOnlyOperativeConfig:
    __test__ = False
    database: str
    mechanism_version: str = VERSION
    origin_state: dict | None = None


def validate_config(database, config, initialize):
    if not isinstance(config, TestOnlyOperativeConfig):
        raise ValueError('Explicit TEST_ONLY operative configuration required')
    if config.mechanism_version != VERSION:
        raise ValueError('Incompatible TEST_ONLY operative mechanism version')
    if Path(config.database).resolve() != Path(database).resolve():
        raise ValueError('TEST_ONLY operative database selection mismatch')
    if initialize:
        if Path(database).exists() or config.origin_state is None:
            raise ValueError('TEST_ONLY origin requires a fresh independent database')
    elif config.origin_state is not None:
        raise ValueError('Restart cannot re-supply S0')


def validate_state(database, config, state, engine):
    internal = state.internal_state
    local = internal.get('l0_state', {})
    expected = {'mode': 'TEST_ONLY', 'mechanism_version': VERSION,
                'database': str(Path(database).resolve()),
                'individual_id': state.individual_id}
    if config is None or local.get(KEY) != expected:
        raise ValueError('TEST_ONLY operative lifecycle metadata mismatch')
    if config.mechanism_version != VERSION or Path(config.database).resolve() != Path(database).resolve():
        raise ValueError('TEST_ONLY operative configuration changed')
    parsed = InternalState.from_dict(internal)
    if not local.get('operative_test_only', {}).get('edges'):
        raise ValueError('Missing operative collection')
    # Existing operand validator; no audit/provenance participates in admission.
    engine._read_operative_operands(parsed, local.get('feedback', {}).get('next_relation_ref'))


def preflight(database, config, engine):
    """Read authoritative current snapshot only, before any writer/schema/session."""
    path = Path(database).resolve()
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.exists() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            if config is not None:
                raise ValueError('Existing database is not an operative test lifetime')
            return  # Preserve the default Core's existing empty-file rejection.
        row = current_row(db)
        if row is None:
            if config is not None:
                raise ValueError('Cannot adopt an existing database into TEST_ONLY mode')
            return
        from individual.state import AState
        state = AState(**json.loads(row[3]))
        local = state.internal_state.get('l0_state', {})
        marked = 'operative_test_only' in local or KEY in local
        environment = {}
        if state.session_id:
            session = db.execute('SELECT environment FROM sessions WHERE session_id=?',
                                 (state.session_id,)).fetchone()
            environment = json.loads(session[0]) if session else {}
        lifecycle = environment.get(KEY)
        if config is None:
            if marked or lifecycle is not None:
                raise ValueError('TEST_ONLY operative state cannot resume through default Core')
        else:
            if lifecycle != session_metadata(database):
                raise ValueError('TEST_ONLY session mechanism metadata mismatch')
            validate_state(database, config, state, engine)


def validate_origin(config, engine):
    origin = InternalState.from_dict(deepcopy(config.origin_state))
    from individual.formal_boundary import validate_boundary
    validate_boundary(origin.to_dict(), engine.caps, engine.resource_caps)
    local = origin.l0_state
    if (KEY in local or local.get('previous_frame') is not None
            or origin.latest_integration or local.get('latest_experience')):
        raise ValueError('Origin cannot contain resumed experience or lifecycle state')
    engine._read_operative_operands(origin, local.get('feedback', {}).get('next_relation_ref'))
    if not local['operative_test_only']['edges']:
        raise ValueError('Origin requires S0')
    return origin


def initialize_state(core, config):
    """Only fresh Core creation adopts the supplied scaffold; never restart."""
    origin = validate_origin(config, core._engine)
    internal = InternalState.from_dict(core.state.internal_state)
    internal.units = deepcopy(origin.units)
    internal.relations = deepcopy(origin.relations)
    # Preserve Core's sealed identity/capacity boundary and policy administration.
    for key in ('profile', 'active_layer', 'process_id', 'previous_frame',
                'previous_unit', 'feedback', 'pending_consequences', 'operative_test_only'):
        internal.l0_state[key] = deepcopy(origin.l0_state[key])
    internal.l0_state[KEY] = {'mode': 'TEST_ONLY', 'mechanism_version': VERSION,
        'database': str(Path(core._store.path).resolve()),
        'individual_id': core.state.individual_id}
    core._transition('TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED',
        {'mode': 'TEST_ONLY', 'mechanism_version': VERSION, 'source': 'ORIGIN_SUPPLIED'},
        internal_state=internal.to_dict())
