"""Explicit opt-in version with pre-write admission, never default adoption."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from individual.current_state import current_row
from individual.internal_state import InternalState
from individual.observation import FrameEncoder
from experimental.typed_operative_connection.channel import ConnectionCore, ConnectionConfig
from experimental.typed_operative_connection.engine import connection
from .engine import BindingEngine, VERSION, REGISTER, validate_bindings

MODE = 'native_parameter_binding_lifecycle'


@dataclass(frozen=True)
class BindingConfig:
    database: str
    version: str = VERSION


def reject_foreign_mode(database, config=None):
    path = Path(database).resolve()
    if config is not None and (type(config) is not BindingConfig or config.version != VERSION
                              or Path(config.database).resolve() != path):
        raise ValueError('Binding mode/version/database mismatch')
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            if config is not None: raise ValueError('Cannot adopt existing non-binding DB')
            return
        row = current_row(db)
        local = json.loads(row[3])['internal_state']['l0_state'] if row else {}
        if (MODE in local) != (config is not None):
            raise ValueError('Cannot switch native parameter binding mode')
        if config is not None:
            state = json.loads(row[3])
            validate_state(state, config)


def validate_state(state, config):
    expected = {'version': VERSION, 'database': str(Path(config.database).resolve()),
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}
    if state['internal_state']['l0_state'].get(MODE) != expected:
        raise ValueError('Binding lifecycle mismatch')
    validate_bindings(InternalState.from_dict(state['internal_state']))


class ReceiptEncoder(FrameEncoder):
    def encode(self, raw, sequence, body_epoch=0):
        frame = super().encode(raw, sequence, body_epoch)
        frame.nearby_data['typed_execution_receipts'] = deepcopy(raw.get('typedExecutionReceipts', []))
        return frame


class BindingCore(ConnectionCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False,
                 origin=None, origin_edges=None, full_history_enabled=True):
        reject_foreign_mode(database, config)
        if not initialize_lifetime and (not Path(database).is_file() or origin is not None or origin_edges is not None):
            raise ValueError('Binding restart requires same existing DB, no new origin')
        self._binding_config = config
        super().__init__(database, bridge, config=ConnectionConfig(str(database), origin,
            (tuple(origin_edges) if origin_edges is not None else
             (connection('U-origin-0', 'U-origin-1'),)) if initialize_lifetime else ()),
            initialize_lifetime=initialize_lifetime, full_history_enabled=full_history_enabled)
        self._engine = BindingEngine(self._engine.caps, self._engine.resource_caps)
        self._encoder = ReceiptEncoder(self.state.individual_id)
        validate_state(self.state.to_dict(), config)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][REGISTER] = []
            internal['l0_state'][MODE] = {'version': VERSION,
                'database': str(Path(self._binding_config.database).resolve()),
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            changes['internal_state'] = internal
        elif MODE in self._state.internal_state.get('l0_state', {}):
            prospective = self._state.to_dict()
            prospective['internal_state'] = changes.get('internal_state', self._state.internal_state)
            validate_state(prospective, self._binding_config)
        return super()._transition(event_type, payload, additional_events, **changes)
