"""Explicit fresh TEST_ONLY lifecycle, no silent adoption of prior databases."""
from copy import deepcopy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from individual.current_state import current_row
from experimental.observation_interface_references.real.channel import RealEffectCore
from .engine import MODE, VERSION, UsageRealEngine

class UsageRealCore(RealEffectCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False):
        if initialize_lifetime:
            if MODE in (config.origin_state or {}).get('l0_state', {}):
                raise ValueError('Fresh origin cannot claim a prior usage version')
        else:
            with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as db:
                row = current_row(db)
                if not row or json.loads(row[3])['internal_state']['l0_state'].get(MODE) != {'version': VERSION}:
                    raise ValueError('No silent migration to ordinary Pair usage version')
        super().__init__(database, bridge, config=config, initialize_lifetime=initialize_lifetime)
        self._engine = UsageRealEngine(self._engine.caps, self._engine.resource_caps)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][MODE] = {'version': VERSION}
            changes['internal_state'] = internal
        prospective = changes.get('internal_state', self._state.internal_state)
        if MODE in prospective.get('l0_state', {}) and prospective['l0_state'][MODE] != {'version': VERSION}:
            raise ValueError('Ordinary Pair usage version conflict')
        return super()._transition(event_type, payload, additional_events, **changes)
