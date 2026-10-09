"""Explicit isolated lifecycle and mechanical tail for committed native effects."""
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from individual.current_state import current_row
from individual.internal_state import InternalState
from individual.bridge import BridgeError
from experimental.observation_source_boundary.reference.channel import ReferenceCore, ReferenceConfig
from .engine import EffectEngine, KEY, VERSION, empty_pool, validate

MODE = 'observation_reference_effect_lifecycle'


@dataclass(frozen=True)
class EffectConfig:
    database: str
    version: str = VERSION
    origin_state: dict | None = None
    cells: dict | None = None
    cell_bindings: tuple = ()


def validate_state(state, config):
    internal = InternalState.from_dict(state['internal_state'])
    expected = {'version': VERSION, 'database': str(Path(config.database).resolve()),
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}
    if internal.l0_state.get(MODE) != expected:
        raise ValueError('Effect lifecycle/version mismatch')
    validate(internal)
    packet = internal.l0_state[KEY]['current']
    if packet is not None:
        from individual.observation import ObservationFrame
        from .native import project
        frame = ObservationFrame(**state['observation_frame'])
        if packet['frame_id'] != frame.frame_id:
            raise ValueError('Effect packet is not from current input')
        status, operations = project(internal, frame, packet['effects'])
        if status != packet['body_status'] or operations != packet['operations']:
            raise ValueError('Operation differs from activated endpoints')


class EffectCore(ReferenceCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False, full_history_enabled=True):
        path = Path(database).resolve()
        if (type(config) is not EffectConfig or config.version != VERSION
                or Path(config.database).resolve() != path):
            raise ValueError('Effect configuration mismatch')
        if not initialize_lifetime:
            if config.origin_state is not None or config.cells or config.cell_bindings or not path.is_file():
                raise ValueError('Restart must restore same effect state without reinjection')
            with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
                row = current_row(db)
                if not row:
                    raise ValueError('Missing authoritative effect state')
                validate_state(json.loads(row[3]), config)
        elif (config.origin_state is None or KEY in config.origin_state.get('l0_state', {})
              or MODE in config.origin_state.get('l0_state', {})):
            raise ValueError('No preformed effect answer in origin')
        self._effect_config = config
        super().__init__(database, bridge, config=ReferenceConfig(str(path), origin_state=config.origin_state),
                         initialize_lifetime=initialize_lifetime, full_history_enabled=full_history_enabled)
        self._engine = EffectEngine(self._engine.caps, self._engine.resource_caps)
        validate_state(self.state.to_dict(), config)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            pool = empty_pool()
            pool['cells'] = deepcopy(self._effect_config.cells or {})
            pool['cell_bindings'] = deepcopy(list(self._effect_config.cell_bindings))
            internal['l0_state'][KEY] = pool
            internal['l0_state'][MODE] = {'version': VERSION,
                'database': str(Path(self._effect_config.database).resolve()),
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            # ReferenceCore will add its own collection before final validation.
            changes['internal_state'] = internal
        elif KEY in changes.get('internal_state', self._state.internal_state).get('l0_state', {}):
            validate_state({**self._state.to_dict(), **changes}, self._effect_config)
        return super()._transition(event_type, payload, additional_events, **changes)

    def _commit_observation(self, observation, fields, sequence, internal, frame, journal):
        state = super()._commit_observation(observation, fields, sequence, internal, frame, journal)
        self._dispatch_current_effect()
        return self.state

    def _dispatch_current_effect(self):
        # No caller supplies a port, parameter or query. Only this just-committed
        # ordinary read's operation is eligible; no history/content scan.
        internal = InternalState.from_dict(self._state.internal_state)
        pool = validate(internal)
        packet = pool['current']
        if not packet or packet['body_status'] != 'READY':
            return
        if (packet['frame_id'] != self._state.observation_frame['frame_id']
                or packet['state_version'] != self._state.state_version):
            return  # A later transition cannot revive a saved occurrence.
        operation, = packet['operations']
        attempt_key = f"{self._state.individual_id}:{packet['frame_id']}:{packet['state_version']}"
        if attempt_key in pool['attempts']:
            return
        expression = deepcopy(operation['expression'])
        action_id = str(uuid4())
        request = {'action_id': action_id, 'action_code': expression['code'],
                   'status': 'requested', 'method': 'perform', 'args': expression,
                   'initiator': 'TEST_ONLY_ORDINARY_OCCURRENCE_EFFECT',
                   'provenance': {'operation': deepcopy(operation), 'packet': deepcopy(packet),
                                  'formation_rule': VERSION,
                                  'action_selection_claimed': False}}
        # A previous frame/version can never be revived by this tail. Current
        # state needs one reservation, while EventStore retains request receipts.
        pool['attempts'] = {attempt_key: {'status': 'requested', 'action_id': action_id,
                                        'expression': expression}}
        self._transition('ACTION_REQUESTED', request, internal_state=internal.to_dict(), latest_action=request)
        try:
            result = self._bridge.call('perform', deepcopy(expression))
            from individual.formal_l0 import digest
            if (not isinstance(result, dict) or type(result.get('code')) is not int
                    or result['code'] != expression['code'] or digest(result.get('parameters')) != digest(expression['parameters'])
                    or not result.get('started_at') or not result.get('finished_at')):
                raise ValueError('Native effect receipt mismatch')
        except Exception as error:
            final = {**request, 'status': 'failed', 'error': {'type': type(error).__name__, 'message': str(error)}}
            event = 'ACTION_FAILED'
        else:
            final = {**request, 'status': 'executed', 'result': deepcopy(result)}
            event = 'ACTION_EXECUTED'
        internal = InternalState.from_dict(self._state.internal_state)
        internal.l0_state[KEY]['attempts'][attempt_key]['status'] = final['status']
        self._transition(event, final, internal_state=internal.to_dict(), latest_action=final)
        self._pending_actions.append({'action_id': action_id, 'action_code': expression['code'],
                                      'parameters': deepcopy(expression['parameters']), 'status': final['status']})

    def tick(self, now=None):
        # Observation carrier only. Body effects happen inside accept_observation,
        # never in the default sampler's action stage.
        now = time.monotonic() if now is None else now
        for message in self._bridge.drain_events():
            if message['kind'] == 'lifecycle':
                self.accept_bridge_status(message['status'], source=message)
            elif message['kind'] in ('transport_error', 'exited'):
                self._transition('BRIDGE_DISCONNECTED', message, status='waiting_for_bridge')
                raise BridgeError('BRIDGE_EXITED', 'Effect carrier stopped without restart')
        if not self._bridge.alive:
            raise BridgeError('BRIDGE_EXITED', 'Effect carrier is not alive')
        if not self._session_active or self._paused or self._closed:
            return
        if (not self._bridge_status.get('connected') and self._bridge_status.get('state') != 'dead') or self._bridge_status.get('lastError'):
            return
        if now >= self._next_observation:
            self._observe()
            self._next_observation = now + self._observation_interval
