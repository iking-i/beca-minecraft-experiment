"""Explicit isolated Core lifecycle; only authoritative Current State is restored."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from individual.core import ACore
from individual.current_state import current_row
from individual.internal_state import InternalState
from experimental.formall0_continuous.channel import TestOnlyOperativeConfig
from experimental.native_parameter_binding_extension.channel import ReceiptEncoder
from .references import KEY, VERSION
from .engine import ReferenceEngine, validate

MODE = 'body_reference_lifecycle'


@dataclass(frozen=True)
class ReferenceConfig:
    database: str
    version: str = VERSION
    origin_state: dict | None = None


def validate_state(state, config):
    expected = {'version': VERSION, 'database': str(Path(config.database).resolve()),
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}
    if state['internal_state']['l0_state'].get(MODE) != expected:
        raise ValueError('Body reference lifecycle mismatch')
    internal = InternalState.from_dict(state['internal_state'])
    pool = validate(internal)
    if state.get('observation_frame'):
        from individual.observation import ObservationFrame
        from .references import observed_catalog
        catalog = observed_catalog(ObservationFrame(**state['observation_frame']))
        catalog['body_epoch'] = pool['catalog']['body_epoch']
        if catalog != pool['catalog']:
            raise ValueError('Current interface/frame mismatch')
        supplied = internal.body_capabilities
        if (supplied.get('version') != catalog['version']
                or sorted(supplied.get('actions', []), key=lambda e: e['code']) != catalog['declarations']):
            raise ValueError('References do not match provisioned native body interface')


def preflight(database, config, initialize):
    path = Path(database).resolve()
    if (type(config) is not ReferenceConfig or config.version != VERSION
            or Path(config.database).resolve() != path):
        raise ValueError('Body reference mode/version/database mismatch')
    if initialize:
        if path.exists() or config.origin_state is None or KEY in config.origin_state.get('l0_state', {}):
            raise ValueError('Fresh reference experiment requires new DB and unformed origin')
        native_types = {'NativePort', 'ParameterSlot', 'ParameterDomain', 'ObservedValue', 'ObservedReference', 'BodyRef'}
        if any(isinstance(u.get('pattern'), dict) and u['pattern'].get('type') in native_types
               for u in config.origin_state.get('units', {}).values()):
            raise ValueError('Native operands must originate in actual observed input')
    else:
        if not path.is_file() or config.origin_state is not None:
            raise ValueError('Restart requires same DB without origin reinjection')
        wal = Path(str(path) + '-wal')
        flags = '?mode=ro' if wal.exists() and wal.stat().st_size else '?mode=ro&immutable=1'
        with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
            row = current_row(db)
            if not row:
                raise ValueError('No authoritative reference state')
            validate_state(json.loads(row[3]), config)


class ReferenceCore(ACore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False,
                 full_history_enabled=True):
        preflight(database, config, initialize_lifetime)
        self._reference_config = config
        super().__init__(database, bridge, initialize_lifetime=initialize_lifetime,
            full_history_enabled=full_history_enabled,
            test_only_operative=TestOnlyOperativeConfig(str(Path(database).resolve()),
                                                       origin_state=config.origin_state),
            session_context={MODE: {'mode': 'TEST_ONLY', 'version': VERSION}})
        self._engine = ReferenceEngine(self._engine.caps, self._engine.resource_caps)
        self._encoder = ReceiptEncoder(self.state.individual_id)
        validate_state(self.state.to_dict(), config)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][KEY] = {'version': VERSION, 'catalog': None,
                'current_source': None, 'sources': {}, 'edges': {}, 'evidence': {}, 'nodes': {}, 'node_evidence': {}}
            internal['l0_state'][MODE] = {'version': VERSION,
                'database': str(Path(self._reference_config.database).resolve()),
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            changes['internal_state'] = internal
        if KEY in changes.get('internal_state', self._state.internal_state).get('l0_state', {}):
            prospective = {**self._state.to_dict(), **changes}
            validate_state(prospective, self._reference_config)
        return super()._transition(event_type, payload, additional_events, **changes)

    def execute_discrete_action(self, *args, **kwargs):
        raise RuntimeError('Body reference admission experiment has no body execution')

    def execute_action(self, *args, **kwargs):
        raise RuntimeError('Body reference admission experiment has no body execution')
