"""Isolated real carrier; one external bootstrap, unchanged formed-effect tail."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from individual.bridge import MinecraftBridge
from individual.current_state import current_row
from individual.formal_l0 import digest
from experimental.observation_source_boundary.effects.channel import EffectCore, EffectConfig
from .adapter import MODE, VERSION, RealEncoder, RealEffectEngine, canonical_observation

BOOTSTRAP = {'code': 16, 'parameters': {'slot': 0}}


class RealEffectCore(EffectCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False, full_history_enabled=True):
        self._native_records = {}
        self._real_source = ('NATIVE_BRIDGE_EXECUTION' if isinstance(bridge, MinecraftBridge)
                             else 'OFFLINE_RECEIPT_ADAPTER_TEST')
        self._real_path = str(Path(database).resolve())
        if not initialize_lifetime:
            with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
                row = current_row(db)
                if not row:
                    raise ValueError('Missing real carrier state')
                self._validate_mode(json.loads(row[3]))
        elif MODE in (config.origin_state or {}).get('l0_state', {}):
            raise ValueError('No preformed real lifecycle in origin')
        super().__init__(database, bridge, config=config, initialize_lifetime=initialize_lifetime, full_history_enabled=full_history_enabled)
        self._encoder = RealEncoder(self.state.individual_id)
        self._engine = RealEffectEngine(self._engine.caps, self._engine.resource_caps)
        self._validate_mode(self.state.to_dict())

    def _validate_mode(self, state):
        record = state['internal_state']['l0_state'].get(MODE)
        if (type(record) is not dict or set(record) !=
                {'version', 'database', 'individual_id', 'source', 'bootstrap_attempted'}
                or record['version'] != VERSION or record['database'] != self._real_path
                or record['individual_id'] != state['individual_id']
                or record['source'] != self._real_source
                or type(record['bootstrap_attempted']) is not bool):
            raise ValueError('Real receipt lifecycle/version/source mismatch')

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][MODE] = {'version': VERSION, 'database': self._real_path,
                'individual_id': self._state.individual_id, 'source': self._real_source,
                'bootstrap_attempted': False}
            changes['internal_state'] = internal
        if MODE in changes.get('internal_state', self._state.internal_state).get('l0_state', {}):
            self._validate_mode({**self._state.to_dict(), **changes})
        state = super()._transition(event_type, payload, additional_events, **changes)
        if event_type == 'ACTION_EXECUTED':
            self._native_records[payload['action_id']] = {
                'action_id': payload['action_id'], 'source': self._real_source,
                'request': deepcopy(payload['args']), 'receipt': deepcopy(payload['result']),
                'before_frame_id': self._state.observation_frame['frame_id'],
                'individual_id': self._state.individual_id}
        return state

    def accept_observation(self, observation):
        if observation.get('typedExecutionReceipts') or 'nativeExecutionRecords' in observation:
            raise ValueError('No caller-supplied receipt artifacts in real observation')
        raw = canonical_observation(observation)
        pending_ids = {a['action_id'] for a in self._pending_actions}
        records = [deepcopy(self._native_records[i]) for i in pending_ids if i in self._native_records]
        if any(a['status'] == 'executed' and a['action_id'] not in self._native_records
               for a in self._pending_actions):
            raise ValueError('No owned receipt for pending real execution')
        raw['nativeExecutionRecords'] = records
        state = super().accept_observation(raw)
        for identity in pending_ids:
            self._native_records.pop(identity, None)
        return state

    def bootstrap_once(self):
        """Explicit external initial condition. Never called by tick/advance."""
        mode = self._state.internal_state['l0_state'][MODE]
        if mode['bootstrap_attempted'] or self._state.environment_sequence != 1 or self._pending_actions:
            raise ValueError('Bootstrap only once after first committed native observation')
        body = self._state.observation_frame['nearby_data']['body']
        entries = [e for e in body['action_space'] if e['code'] == BOOTSTRAP['code']]
        if (len(entries) != 1 or not entries[0]['formal_enabled'] or not entries[0]['currently_available']
                or entries[0]['parameter_schema'] != {'type': 'object',
                    'properties': {'slot': {'type': 'integer', 'minimum': 0, 'maximum': 8}},
                    'required': ['slot'], 'additionalProperties': False}):
            raise ValueError('Frozen bootstrap is unavailable/incompatible; do not replace it')
        internal = deepcopy(self._state.internal_state)
        internal['l0_state'][MODE]['bootstrap_attempted'] = True
        request = {'action_id': str(uuid4()), 'action_code': BOOTSTRAP['code'],
            'status': 'requested', 'method': 'perform', 'args': deepcopy(BOOTSTRAP),
            'initiator': 'EXPERIMENTER_SUPPLIED_REAL_BOOTSTRAP',
            'provenance': {'source': 'EXTERNAL_FIXED_INITIAL_CONDITION', 'internal_authorship': False}}
        self._transition('ACTION_REQUESTED', request, internal_state=internal, latest_action=request)
        try:
            receipt = self._bridge.call('perform', deepcopy(BOOTSTRAP))
            if (type(receipt.get('code')) is not int or receipt['code'] != BOOTSTRAP['code']
                    or digest(receipt.get('parameters')) != digest(BOOTSTRAP['parameters'])
                    or receipt.get('result') != {'input_sent': 1, 'effect_acknowledged': 0}
                    or not receipt.get('started_at') or not receipt.get('finished_at')):
                raise ValueError('Bootstrap receipt mismatch')
        except Exception as error:
            self._transition('ACTION_FAILED', {**request, 'status': 'failed',
                'error': {'type': type(error).__name__, 'message': str(error)}},
                latest_action={**request, 'status': 'failed'})
            raise
        final = {**request, 'status': 'executed', 'result': deepcopy(receipt)}
        self._transition('ACTION_EXECUTED', final, latest_action=final)
        self._pending_actions.append({'action_id': request['action_id'], 'action_code': BOOTSTRAP['code'],
            'parameters': deepcopy(BOOTSTRAP['parameters']), 'status': 'executed'})
        return deepcopy(final)
