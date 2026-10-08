"""Explicit extension of ContentCore; no schema migration or body pathway."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from individual.current_state import current_row
from individual.internal_state import InternalState
from experimental.operative_content.channel import ContentCore, ContentConfig
from .engine import KEY, VERSION, NativeEngine, validate_native

MODE = 'native_operand_lifecycle'


@dataclass(frozen=True)
class NativeConfig:
    database: str
    origin_state: dict | None = None
    version: str = VERSION


def validate_state(state, config):
    expected = {'version': VERSION, 'database': str(Path(config.database).resolve()),
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}
    if state['internal_state']['l0_state'].get(MODE) != expected:
        raise ValueError('Native operand lifetime binding mismatch')
    validate_native(InternalState.from_dict(state['internal_state']))


def reject_foreign_mode(database, config=None):
    path = Path(database).resolve()
    if config is not None and (type(config) is not NativeConfig or config.version != VERSION
                              or Path(config.database).resolve() != path):
        raise ValueError('Native mode/version/database mismatch')
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            if config is not None:
                raise ValueError('Cannot adopt existing non-native database')
            return
        row = current_row(db)
        if row is None:
            if config is not None:
                raise ValueError('Cannot adopt existing empty database')
            return
        state = json.loads(row[3])
        local = state['internal_state'].get('l0_state', {})
        marked = KEY in local or MODE in local
        if marked != (config is not None):
            raise ValueError('Cannot silently adopt/switch native operand mode')
        if marked:
            validate_state(state, config)


class NativeCore(ContentCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False,
                 full_history_enabled=True):
        reject_foreign_mode(database, config)
        if initialize_lifetime and any(k in (config.origin_state or {}).get('l0_state', {})
                                       for k in (KEY, MODE)):
            raise ValueError('Cannot supply native results at origin')
        if initialize_lifetime and any(v.get('operand_kind') == 'NATIVE_SENSOR'
                or isinstance(v.get('pattern'), dict)
                for v in (config.origin_state or {}).get('units', {}).values()):
            raise ValueError('Native operands must come from observed input, not origin injection')
        self._native_config = config
        super().__init__(database, bridge, config=ContentConfig(config.database, config.origin_state),
            initialize_lifetime=initialize_lifetime, full_history_enabled=full_history_enabled)
        self._engine = NativeEngine(self._engine.caps, self._engine.resource_caps)
        validate_state(self.state.to_dict(), config)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][KEY] = {'version': VERSION, 'sources': {}, 'incidence': {}, 'evidence': {}}
            internal['l0_state'][MODE] = {'version': VERSION,
                'database': str(Path(self._native_config.database).resolve()),
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            changes['internal_state'] = internal
        elif MODE in self._state.internal_state.get('l0_state', {}):
            validate_state(self._state.to_dict(), self._native_config)
            prospective = self._state.to_dict()
            prospective['internal_state'] = changes.get('internal_state', self._state.internal_state)
            validate_state(prospective, self._native_config)
        result = super()._transition(event_type, payload, additional_events, **changes)
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            self._engine = NativeEngine(self._engine.caps, self._engine.resource_caps)
            validate_state(self.state.to_dict(), self._native_config)
        return result
