"""Explicit lifecycle; existing NativeCore cannot silently adopt this version."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from individual.current_state import current_row
from individual.internal_state import InternalState
from experimental.native_body_operands.channel import NativeConfig, NativeCore
from .engine import KEY, VERSION, ConnectionEngine, validate_connections

MODE = 'typed_connection_lifecycle'


@dataclass(frozen=True)
class ConnectionConfig:
    database: str
    origin_state: dict | None = None
    origin_connections: tuple = ()
    version: str = VERSION


def validate_state(state, config):
    expected = {'version': VERSION, 'database': str(Path(config.database).resolve()),
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}
    if state['internal_state']['l0_state'].get(MODE) != expected:
        raise ValueError('Typed connection lifetime mismatch')
    validate_connections(InternalState.from_dict(state['internal_state']))


def reject_foreign_mode(database, config=None):
    path = Path(database).resolve()
    if config is not None and (type(config) is not ConnectionConfig or config.version != VERSION
                              or Path(config.database).resolve() != path):
        raise ValueError('Typed mode/version/database mismatch')
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            if config is not None:
                raise ValueError('Cannot adopt non-connection database')
            return
        row = current_row(db)
        if row is None:
            if config is not None:
                raise ValueError('Cannot adopt empty database')
            return
        state = json.loads(row[3])
        local = state['internal_state'].get('l0_state', {})
        if (KEY in local or MODE in local) != (config is not None):
            raise ValueError('Cannot switch typed connection mode')
        if config is not None:
            validate_state(state, config)


class ConnectionCore(NativeCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False,
                 full_history_enabled=True):
        reject_foreign_mode(database, config)
        if not initialize_lifetime and not Path(database).is_file():
            raise ValueError('Restart requires the existing same connection database')
        if initialize_lifetime:
            if config.origin_state is None or not config.origin_connections:
                raise ValueError('Fresh connection lifetime requires explicit S0')
            origin = InternalState.from_dict(deepcopy(config.origin_state))
            if KEY in origin.l0_state or MODE in origin.l0_state:
                raise ValueError('Cannot inject formed collection at origin')
            from individual.formal_l0 import digest
            edges = {digest(e): deepcopy(e) for e in config.origin_connections}
            if len(edges) != len(config.origin_connections):
                raise ValueError('Duplicate S0 connection')
            origin.l0_state[KEY] = {'version': VERSION, 'edges': edges, 'evidence': {}}
            validate_connections(origin)
        elif config.origin_state is not None or config.origin_connections:
            raise ValueError('Cannot resupply S0 on restart')
        self._typed_config = config
        super().__init__(database, bridge,
            config=NativeConfig(config.database, config.origin_state),
            initialize_lifetime=initialize_lifetime, full_history_enabled=full_history_enabled)
        self._engine = ConnectionEngine(self._engine.caps, self._engine.resource_caps)
        validate_state(self.state.to_dict(), config)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            from individual.formal_l0 import digest
            internal = deepcopy(changes['internal_state'])
            edges = {digest(e): deepcopy(e) for e in self._typed_config.origin_connections}
            internal['l0_state'][KEY] = {'version': VERSION, 'edges': edges,
                'evidence': {r: {'provenance': 'ORIGIN_SUPPLIED'} for r in edges}}
            internal['l0_state'][MODE] = {'version': VERSION,
                'database': str(Path(self._typed_config.database).resolve()),
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            changes['internal_state'] = internal
            validate_connections(InternalState.from_dict(internal))
        elif MODE in self._state.internal_state.get('l0_state', {}):
            prospective = self._state.to_dict()
            prospective['internal_state'] = changes.get('internal_state', self._state.internal_state)
            validate_state(prospective, self._typed_config)
            previous = self._state.internal_state['l0_state'][KEY]['edges']
            following = prospective['internal_state']['l0_state'][KEY]['edges']
            if any(following.get(ref) != edge for ref, edge in previous.items()):
                raise ValueError('Cannot erase committed typed connections')
        result = super()._transition(event_type, payload, additional_events, **changes)
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            self._engine = ConnectionEngine(self._engine.caps, self._engine.resource_caps)
        return result
