"""Measurement-only tests; fake/offline cases are not new Minecraft evidence."""
from copy import deepcopy
import json
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from experimental.continuous_capacity.recorder import CapacityTrace, inventory, delta
from experimental.continuous_capacity.run import events_after, outcome, observation_carrier_available
from experimental.observation_interface_references.reference.references import KEY as REF
from experimental.observation_interface_references.effects.engine import KEY as FX
from experimental.operative_content.engine import ContentCapacityError
from tests.test_ordinary_pair_usage import prepared


def test_inventory_counts_retained_and_current_packet_separately(tmp_path):
    core = prepared(tmp_path / 'counts.db')
    try:
        from experimental.body_interface_references.runner import sample
        core.accept_observation(sample(4, 1))
        state = core.state.to_dict()
        original = deepcopy(state)
        result = inventory(state)
        pool = state['internal_state']['l0_state'][REF]
        packet = state['internal_state']['l0_state'][FX]['current']
        assert result['content_nodes'] == len(pool['nodes'])
        assert result['current_packet_charge'] == len(packet['effects']) + len(packet['operations'])
        assert result['total_unit_charge'] == result['retained_unit_content_charge'] + result['current_packet_charge']
        assert result['unit_capacity'] == 64 and result['relation_capacity'] == 96
        assert state == original
    finally:
        core.shutdown()


def test_delta_distinguishes_recomputation_from_explicit_read(tmp_path):
    from experimental.body_interface_references.runner import sample
    core = prepared(tmp_path / 'delta.db')
    try:
        before = core.state.to_dict()
        row = core._store.connection.execute('SELECT max(event_sequence) FROM events').fetchone()
        core.accept_observation(sample(4, 1))
        after = core.state.to_dict()
        unchanged = deepcopy((before, after))
        events = events_after(core._store, row[0])
        result = delta(before, after, events)
        assert result['existing_direct_pairs_recomputed_by_constructor']
        assert result['actual_typed_connections_used']
        assert not result['explicit_pair_operands_returned_by_ordinary_read']
        assert not result['old_pair_operands_used_to_form_wrappers']
        assert result['old_content_unchanged'] and result['retained_old_pair_ids']
        assert result['activated_route_ids'] and result['current_operations']
        assert (before, after) == unchanged
    finally:
        core.shutdown()


def test_exception_observer_preserves_rejected_locals_and_exception():
    old_trace = sys.gettrace()
    error = ContentCapacityError('actual test rejection')

    def reject():
        staged = {'a': {'type': 'Pair'}}
        raise error

    with pytest.raises(ContentCapacityError) as caught:
        with CapacityTrace() as trace:
            reject()
    assert caught.value is error
    assert trace.records[0]['function'] == 'reject'
    assert trace.records[0]['staged'] == {'a': {'type': 'Pair'}}
    assert sys.gettrace() is old_trace
    assert not CapacityTrace().records


def test_incremental_external_event_read_never_writes(tmp_path):
    database = tmp_path / 'events.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE events(event_sequence,event_type,state_version,timestamp,payload)')
        connection.executemany('INSERT INTO events VALUES(?,?,?,?,?)',
            [(i, 'EXPERIENCE_FORMED', i, 't', json.dumps({'action_ids': []})) for i in range(1, 5)])
    before = database.read_bytes()
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        store = SimpleNamespace(connection=connection)
        assert [e['event_sequence'] for e in events_after(store, 2)] == [3, 4]
        assert not events_after(store, 4)
        assert connection.total_changes == 0
    assert database.read_bytes() == before


def test_budget_and_resource_failure_classifications_are_distinct():
    assert outcome(32, 32, None) == 'BUDGET_COMPLETED'
    assert outcome(7, 32, {'type': 'ContentCapacityError'}) == 'RESOURCE_LIMIT'
    assert outcome(0, 32, {'type': 'BridgeError'}) == 'NOT_TESTABLE'
    assert outcome(7, 32, {'type': 'RuntimeError'}) == 'FAILURE'


def test_dead_body_is_observable_but_not_a_transport_reconnect():
    assert observation_carrier_available({'state': 'ready', 'connected': True, 'lastError': None})
    assert observation_carrier_available({'state': 'dead', 'connected': False, 'lastError': None})
    assert not observation_carrier_available({'state': 'disconnected', 'connected': False})
    assert not observation_carrier_available({'state': 'dead', 'connected': False, 'lastError': {'code': 'DISCONNECTED'}})
