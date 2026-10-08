"""Versioned experimental Core, with admission before any persistence side effect."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from individual.current_state import current_row
from individual.internal_state import InternalState
from experimental.formall0_continuous.channel import TestOnlyOperativeConfig
from .engine import ContentEngine, KEY, VERSION, validate_content

MODE = 'operative_content_lifecycle'


@dataclass(frozen=True)
class ContentConfig:
    database: str
    origin_state: dict | None = None
    version: str = VERSION


def reject_foreign_mode(database, config=None):
    path = Path(database).resolve()
    if config is not None and (type(config) is not ContentConfig or config.version != VERSION
                              or Path(config.database).resolve() != path):
        raise ValueError('Content mode/version/database mismatch')
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            return
        row = current_row(db)
        if row is None:
            return
        state = json.loads(row[3])
        local = state['internal_state'].get('l0_state', {})
        marked = KEY in local or MODE in local
        if marked != (config is not None):
            raise ValueError('Cannot silently adopt/switch content experiment mode')
        if marked:
            validate_state(state, config)


def validate_state(state, config):
    expected = {'version': VERSION, 'database': str(Path(config.database).resolve()),
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}
    if state['internal_state']['l0_state'].get(MODE) != expected:
        raise ValueError('Content lifetime binding mismatch')
    validate_content(InternalState.from_dict(state['internal_state']))


# Import after admission helpers: Core's narrow guard imports this module lazily.
from individual.core import ACore


class ContentCore(ACore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False,
                 full_history_enabled=True):
        reject_foreign_mode(database, config)
        if initialize_lifetime:
            if Path(database).exists() or config.origin_state is None:
                raise ValueError('Content origin requires fresh TEST_ONLY DB and S0')
            if KEY in config.origin_state.get('l0_state', {}):
                raise ValueError('Origin cannot contain preconstructed T1')
        elif config.origin_state is not None:
            raise ValueError('Resume cannot resupply origin')
        self._content_config = config
        base_config = TestOnlyOperativeConfig(str(Path(database).resolve()),
                                             origin_state=config.origin_state)
        super().__init__(database, bridge, test_only_operative=base_config,
                         initialize_lifetime=initialize_lifetime,
                         full_history_enabled=full_history_enabled,
                         session_context={MODE: {'mode': 'TEST_ONLY', 'version': VERSION}})
        self._engine = ContentEngine(self._engine.caps, self._engine.resource_caps)
        validate_state(self.state.to_dict(), config)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][KEY] = {'version': VERSION, 'nodes': {}, 'evidence': {}}
            internal['l0_state'][MODE] = {'version': VERSION,
                'database': str(Path(self._content_config.database).resolve()),
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            changes['internal_state'] = internal
            self._engine = ContentEngine(self._engine.caps, self._engine.resource_caps)
        elif MODE in self._state.internal_state.get('l0_state', {}):
            validate_state(self._state.to_dict(), self._content_config)
        prospective = self._state.to_dict()
        prospective['internal_state'] = changes.get('internal_state', self._state.internal_state)
        validate_state(prospective, self._content_config)
        return super()._transition(event_type, payload, additional_events, **changes)

    def execute_discrete_action(self, *args, **kwargs):
        raise RuntimeError('Content experiment has no expression/body path')

    def execute_action(self, *args, **kwargs):
        raise RuntimeError('Content experiment has no expression/body path')
