"""Opt-in Core and atomic EventStore adapter. No production monkeypatch."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from individual.events import EventStore
from individual.current_state import current_row
from individual.internal_state import InternalState
from .store import SourceStore, using, VERSION, repository
from .channel import UsageRealCore
from .reference.references import KEY
from .effects.engine import validate

MODE = 'observation_source_boundary_lifecycle'


class _DuringInitialization:
    def __init__(self, core):
        self.core = core

    def __getattr__(self, name):
        return getattr(self.core._source_store, name)


class BoundaryEventStore(EventStore):
    def _append_transition(self, previous, current, event_type, payload, additional_events=()):
        pool = current.internal_state.get('l0_state', {}).get(KEY)
        if pool is not None:
            repository().flush(pool['observations'])
        return super()._append_transition(previous, current, event_type, payload, additional_events)


class BoundaryCore(UsageRealCore):
    def __init__(self, database, bridge, *, config, initialize_lifetime=False, full_history_enabled=True):
        self._source_store = None
        self._source_path = str(Path(database).resolve())
        if initialize_lifetime:
            if Path(database).exists():
                raise ValueError('Source boundary requires a fresh independent database')
            with using(_DuringInitialization(self)):
                super().__init__(database, bridge, config=config, initialize_lifetime=True,
                                 full_history_enabled=full_history_enabled)
        else:
            # Validate sources and version before Core obtains lease or writer.
            with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
                db.execute('PRAGMA query_only=ON')
                store = SourceStore(db)
                state = json.loads(current_row(db)[3])
                self._check_boundary_mode(state)
                with using(store):
                    validate(InternalState.from_dict(state['internal_state']))
                    self._source_store = store
                    super().__init__(database, bridge, config=config, initialize_lifetime=False,
                                     full_history_enabled=full_history_enabled)
                    self._ensure_store()

    def _check_boundary_mode(self, state):
        if state['internal_state']['l0_state'].get(MODE) != {
                'version': VERSION, 'database': self._source_path,
                'individual_id': state['individual_id'], 'mode': 'TEST_ONLY'}:
            raise ValueError('Source boundary lifecycle/version/database mismatch')

    def _ensure_store(self):
        if self._source_store is None or self._source_store.db is not self._store.connection:
            install = self._source_store is None
            self._source_store = SourceStore(self._store.connection, install=install)
            self._store.__class__ = BoundaryEventStore

    def _transition(self, event_type, payload, additional_events=(), **changes):
        self._ensure_store()
        if event_type == 'TEST_ONLY_OPERATIVE_ORIGIN_ADOPTED':
            internal = deepcopy(changes['internal_state'])
            internal['l0_state'][MODE] = {'version': VERSION, 'database': self._source_path,
                'individual_id': self._state.individual_id, 'mode': 'TEST_ONLY'}
            changes['internal_state'] = internal
        if MODE in changes.get('internal_state', self._state.internal_state).get('l0_state', {}):
            self._check_boundary_mode({**self._state.to_dict(), **changes})
        with using(self._source_store):
            result = super()._transition(event_type, payload, additional_events, **changes)
            self._source_store.published()
            return result

    def accept_observation(self, observation):
        self._source_store.reset_reads()
        with using(self._source_store):
            try:
                return super().accept_observation(observation)
            finally:
                # Publication failures must not leave phantom pending facts.
                self._source_store.pending = None
                self._source_store.cache.clear()

    def bootstrap_once(self):
        with using(self._source_store):
            return super().bootstrap_once()

    def shutdown(self, *args, **kwargs):
        with using(self._source_store):
            return super().shutdown(*args, **kwargs)
