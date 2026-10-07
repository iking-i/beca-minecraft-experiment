"""Pure-code live state-chain tests; synthetic sensor input, no Minecraft claim."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

from individual.action_space import DEFINITIONS
from individual.core import ACore
from individual.formal_l0 import FormalLimits
from individual.live_body_structure import consume_saved, identity
from tests.test_core import FakeBridge
from tests.test_structure import observation


def sensor(x=0, codes=(0,)):
    raw = observation(x)
    raw.update(inventorySlots=[], inventoryScreen={'slot_state': [], 'cursor': {}},
               selectedHotbarSlot=0, heldItem=None, controlState=[], bodyInputs={})
    raw['actionSpace'] = []
    for code in codes:
        d = DEFINITIONS[code]
        raw['actionSpace'].append({'code': code, 'action_id': d['action_id'],
            'category': 'BODY_CAPABILITY', 'parameter_schema': {
                'type': 'object', 'properties': deepcopy(d['parameters']),
                'required': [k for k, v in d['parameters'].items() if not v.get('optional')],
                'additionalProperties': False}, 'formal_enabled': d['formal_enabled'],
            'environment_requirement_codes': [], 'currently_available': True})
    return raw


@pytest.fixture
def runs(tmp_path):
    cores = []
    def make(condition='CANONICAL', caps=None, bridge=None):
        db = tmp_path / f'fresh-{len(cores)}.db'
        core = ACore(db, bridge or FakeBridge(), initialize_lifetime=True,
                     live_body_connection=True, live_body_control=condition, physical_caps=caps)
        cores.append(core)
        return core, db
    yield make
    for c in cores:
        c.shutdown()


def rows(db, kind):
    with sqlite3.connect(db) as conn:
        return [json.loads(p) for p, in conn.execute(
            'SELECT payload FROM events WHERE event_type=? ORDER BY event_sequence', (kind,))]


def graph(core):
    return core.state.internal_state['l0_state']['live_body_structure']


def chain(core, codes=(0,)):
    core.accept_observation(sensor(0, codes))
    core.accept_observation(sensor(1, codes))
    saved, version = graph(core), core.state.state_version
    core.accept_observation(sensor(2, codes))
    return saved, version, core.state.internal_state['l0_state']['live_body_read']


def test_online_form_commit_then_actual_recursive_read(runs):
    core, db = runs()
    owner = core.state.individual_id, core.state.session_id
    saved, version, read = chain(core)
    assert read['status'] == 'CONNECTED'
    assert read['connection_ids'] == saved['connections']
    assert read['query_source'] == saved['feedback']
    assert read['read_from_committed_version'] == version
    assert read['ports'] == [{'catalog_version': 2, 'code': 0}]
    with sqlite3.connect(db) as conn:
        stored = json.loads(conn.execute('SELECT snapshot FROM states WHERE state_version=?', (version,)).fetchone()[0])
        assert stored['internal_state']['l0_state']['live_body_structure'] == saved
        assert conn.execute('SELECT count(DISTINCT individual_id) FROM states').fetchone()[0] == 1
        versions = [v for v, in conn.execute('SELECT state_version FROM states ORDER BY state_version')]
        assert versions == list(range(len(versions)))
    processing = rows(db, 'RECURSIVE_PARTIAL_OUTPUT')[-1]['processing']['live_body_connection_read']
    assert processing == read
    process, = core.state.internal_state['active_processes'].values()
    assert process['output']['live_body_connection_read'] == read
    assert (core.state.individual_id, core.state.session_id) == owner
    assert not rows(db, 'ACTION_REQUESTED')
    assert not core._bridge.calls


def test_o_is_independent_observed_endpoint_before_c(runs):
    core, _ = runs()
    core.accept_observation(sensor(codes=(0, 5)))
    g = graph(core)
    endpoints = [v for v in g['facts'].values() if v['kind'] == 'BodyPort']
    assert {e['data']['code'] for e in endpoints} == {0, 5}
    assert not g['connections']
    assert not any(f['kind'] == 'CurrentChange' for f in g['facts'].values())
    assert all(g['supports'][identity('BodyPort', e['data'])][0]['rule'] == 'OBSERVED_NATIVE_ENDPOINT' for e in endpoints)


def test_multiple_observed_ports_all_retained_no_choice(runs):
    core, _ = runs()
    saved, _, read = chain(core, codes=(0, 5))
    assert read['status'] == 'MULTIPLE_SUPPORTED_PORTS'
    assert {p['code'] for p in read['ports']} == {0, 5}
    assert len(read['connection_ids']) == len(saved['connections']) == 2
    assert 'selected_port' not in read and 'expression' not in read


def test_entire_actual_catalog_fits_first_formation_and_later_read_without_selection(runs):
    core, _ = runs()
    saved, _, read = chain(core, tuple(DEFINITIONS))
    assert read['status'] == 'MULTIPLE_SUPPORTED_PORTS'
    assert {p['code'] for p in read['ports']} == set(DEFINITIONS)
    assert len(saved['connections']) == len(DEFINITIONS)
    assert core.state.internal_state['l0_state']['live_body_formation_status'] == 'COMPLETE_LOCAL_FORMATION'


def test_cli_rejects_old_database_before_bridge_instantiation(tmp_path):
    from individual.core import main
    db = tmp_path / 'preserve.db'
    db.write_bytes(b'preserve old evidence')
    with (patch('sys.argv', ['core', '--bpc-live-1', '--db', str(db)]),
          patch('individual.core.MinecraftBridge', side_effect=AssertionError('must not launch bridge')),
          pytest.raises(SystemExit) as error):
        main()
    assert error.value.code == 2
    assert db.read_bytes() == b'preserve old evidence'


@pytest.mark.parametrize('condition', ['NC1', 'NC2', 'NC3', 'NC4'])
def test_independent_live_controls_remove_later_effect(runs, condition):
    control, db = runs(condition)
    saved, _, read = chain(control)
    assert read['status'] == 'UNRESOLVED'
    assert not read['connection_ids'] and not read['ports']
    if condition in ('NC1', 'NC2', 'NC3'):
        assert not saved['connections']
    if condition == 'NC1':
        assert not any(f['kind'] == 'BodyPort' for f in saved['facts'].values())
    if condition == 'NC2':
        assert not any(f['kind'] == 'CurrentChange' for f in saved['facts'].values())
    if condition == 'NC3':
        assert rows(db, 'LIVE_BODY_STRUCTURE_FORMATION')[1]['new_connection_ids']
        assert not rows(db, 'LIVE_BODY_STRUCTURE_FORMATION')[1]['persisted']
    if condition == 'NC4':
        assert saved['connections']  # Actual committed graph remains; only access is screened.
    assert rows(db, 'RECURSIVE_PARTIAL_OUTPUT')[-1]['processing']['live_body_connection_read'] == read


@pytest.mark.parametrize('condition', ['CANONICAL', 'NC5', 'NC6'])
def test_no_history_bpc_selector_binder_or_execution_dependency(runs, condition):
    core, db = runs(condition)
    with (patch('integration.froi.history_from_store', side_effect=AssertionError('history replay')),
          patch('individual.core.select_uniform_action', side_effect=AssertionError('selector')),
          patch('individual.core.bind_parameters', side_effect=AssertionError('binder')),
          patch('individual.core.formal_command', side_effect=AssertionError('expression')),
          patch.object(core._store, 'latest_state', side_effect=AssertionError('old DB read'))):
        saved, _, read = chain(core)
    assert read['status'] == 'CONNECTED' and read['connection_ids'] == saved['connections']
    assert not rows(db, 'ACTION_REQUESTED')
    source = Path('individual/live_body_structure.py').read_text(encoding='utf-8')
    assert 'experimental.' not in source and 'sqlite3' not in source


def test_control_instances_use_distinct_new_individuals_and_databases(runs):
    instances = [runs(c) for c in ('CANONICAL', 'NC1', 'NC2', 'NC3', 'NC4', 'NC5', 'NC6')]
    assert len({c.state.individual_id for c, _ in instances}) == 7
    assert len({db for _, db in instances}) == 7
    for c, _ in instances:
        assert not graph(c)['connections']


@pytest.mark.parametrize('damage', ['connection', 'support', 'endpoint', 'c', 'root'])
def test_read_uses_persisted_graph_not_audit_or_raw_inputs(runs, damage):
    core, _ = runs()
    core.accept_observation(sensor(0))
    core.accept_observation(sensor(1))
    g = graph(core)
    edge, = g['connections']
    if damage == 'connection':
        del g['facts'][edge]
    elif damage == 'support':
        g['supports'][edge] = []
    elif damage == 'endpoint':
        p = next(k for k, f in g['facts'].items() if f['kind'] == 'BodyPort')
        del g['facts'][p]
    elif damage == 'c':
        del g['facts'][g['feedback']['current_c']]
    else:
        r = next(k for k, f in g['facts'].items() if f['kind'] == 'Frame')
        del g['facts'][r]
    assert consume_saved(g, core.state.state_version)['status'] == 'UNRESOLVED'


def test_read_is_before_new_formation_not_reconstruction(runs):
    core, _ = runs()
    core.accept_observation(sensor(0))
    core.accept_observation(sensor(1))
    saved = graph(core)
    with patch('individual.formal_live_body.advance_structure', side_effect=AssertionError('formation stopped')):
        assert consume_saved(saved, core.state.state_version)['connection_ids'] == saved['connections']
        with pytest.raises(AssertionError, match='formation stopped'):
            core.accept_observation(sensor(2))
    assert graph(core) == saved  # Aborted round never committed.


def test_unchanged_next_input_still_reads_previous_saved_connection(runs):
    core, _ = runs()
    core.accept_observation(sensor(0))
    core.accept_observation(sensor(1))
    saved = graph(core)
    core.accept_observation(sensor(1))
    assert core.state.internal_state['l0_state']['live_body_read']['connection_ids'] == saved['connections']
    assert graph(core)['connections'] == saved['connections']


def test_metadata_alone_no_fabricated_unobserved_port(runs):
    core, _ = runs()
    raw = sensor(0)
    del raw['actionSpace']
    core.accept_observation(raw)
    raw['position']['x'] = 1
    core.accept_observation(raw)
    assert not graph(core)['connections']
    assert not any(f['kind'] == 'BodyPort' for f in graph(core)['facts'].values())


@pytest.mark.parametrize('field,value', [('action_id', 'fabricated'), ('code', True), ('code', 999),
                                      ('formal_enabled', False), ('parameter_schema', {})])
def test_invalid_capability_rejected_before_state_write(runs, field, value):
    core, _ = runs()
    raw = sensor()
    raw['actionSpace'][0][field] = value
    before = core.state
    with pytest.raises(ValueError):
        core.accept_observation(raw)
    assert core.state == before


def test_resource_limit_does_not_publish_partial_or_raise_caps(runs):
    caps = FormalLimits(units=2)
    core, db = runs(caps=caps)
    core.accept_observation(sensor(0))
    core.accept_observation(sensor(1))
    assert rows(db, 'LIVE_BODY_STRUCTURE_FORMATION')[-1]['status'] == 'RESOURCE_LIMIT'
    assert not graph(core)['connections']
    assert graph(core)['caps'] == asdict(caps)
    assert core.state.internal_state['l0_state']['locked_caps'] == asdict(caps)
    with pytest.raises(RuntimeError, match='RESOURCE_LIMIT'):
        core.accept_observation(sensor(2))


def test_run_records_frozen_implementation_and_policy_is_disabled(runs):
    canonical, db = runs()
    control, other = runs('NC1')
    chain(canonical)
    first, = rows(db, 'LIVE_BODY_RUN_INITIALIZED')
    second, = rows(other, 'LIVE_BODY_RUN_INITIALIZED')
    assert first['runtime_sources'] == second['runtime_sources']
    assert first['runtime_sources']['individual/core.py']
    for key in ('formal.action_sampling', 'action.parameter_binding'):
        assert canonical.state.internal_state['policy_registry'][key]['formal_path_enabled'] is False


def test_future_uncommitted_organization_cannot_be_read(runs):
    core, _ = runs()
    saved, version, _ = chain(core)
    assert consume_saved(saved, version - 1)['status'] == 'UNRESOLVED'


def test_capability_availability_is_not_a_selector(runs):
    core, _ = runs()
    for n in range(3):
        raw = sensor(n, (0, 5))
        raw['actionSpace'][0]['currently_available'] = False
        core.accept_observation(raw)
    assert {p['code'] for p in core.state.internal_state['l0_state']['live_body_read']['ports']} == {0, 5}


def test_audit_or_detached_payload_cannot_supply_formation(runs):
    core, _ = runs()
    for n in range(3):
        raw = sensor(n, ())
        raw['detached_bpc_organization'] = {'BodyPort': {'catalog_version': 2, 'code': 0},
                                           'Shared': ['C', 'O'], 'status': 'COMPLETE'}
        raw['old_history_database'] = 'not-a-live-source.db'
        core.accept_observation(raw)
    assert not graph(core)['connections']
    assert core.state.internal_state['l0_state']['live_body_read']['status'] == 'UNRESOLVED'


def test_existing_database_rejected_without_modification(tmp_path):
    db = tmp_path / 'old.db'
    db.write_bytes(b'old history must not be touched')
    with pytest.raises(ValueError, match='fresh database'):
        ACore(db, FakeBridge(), initialize_lifetime=True, live_body_connection=True)
    assert db.read_bytes() == b'old history must not be touched'


def test_completed_run_cannot_resume_even_with_initialize_flag(runs):
    core, db = runs()
    chain(core)
    core.shutdown()
    with pytest.raises(ValueError, match='fresh database'):
        ACore(db, FakeBridge(), initialize_lifetime=True, live_body_connection=True)


@pytest.mark.parametrize('mode', ['froi', 'legacy', 'policy', 'unregistered'])
def test_incompatible_paths_rejected_before_db_creation(tmp_path, mode):
    args = {'initialize_lifetime': True, 'live_body_connection': True}
    args.update({'froi': True} if mode == 'froi' else
                {'experiment_profile': 'legacy_policy_debug'} if mode == 'legacy' else
                {'policy': object()} if mode == 'policy' else {'initialize_lifetime': False})
    db = tmp_path / 'never-created.db'
    with pytest.raises(ValueError):
        ACore(db, FakeBridge(), **args)
    assert not db.exists()


def test_no_actions_fallback_session_switch_or_control_mutation(runs):
    core, _ = runs()
    chain(core)
    with pytest.raises(RuntimeError):
        core.execute_discrete_action(0, {})
    with pytest.raises(RuntimeError):
        core.execute_action({'method': 'move', 'args': {'direction': 'stop'}})
    with pytest.raises(RuntimeError):
        core.begin_session()
    core._engine.controls = replace(core._engine.controls, condition='NC4')
    with pytest.raises(RuntimeError, match='control boundary'):
        core.accept_observation(sensor(3))


def test_body_epoch_encoding_or_transport_interruption_cannot_continue(runs):
    core, _ = runs()
    core.accept_observation(sensor(0))
    raw = sensor(1)
    raw['encoding']['protocol_version'] = 'another-carrier'
    with pytest.raises(ValueError, match='body/encoding'):
        core.accept_observation(raw)
    core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 1})
    core.accept_bridge_status({'state': 'disconnected', 'connected': False, 'attempt': 1})
    with pytest.raises(RuntimeError, match='continuous'):
        core.accept_observation(sensor(1))


def test_tick_observes_but_never_dispatches_or_samples(runs):
    class SensorBridge(FakeBridge):
        def call(self, method, args=None):
            if method == 'observe':
                return sensor(self.position['x'])
            if method == 'start':
                return super().call(method, args)
            raise AssertionError('No body execution allowed')
    bridge = SensorBridge()
    core, _ = runs(bridge=bridge)
    core.start()
    for n in range(3):
        bridge.position['x'] = n
        core.tick(now=100000000 + n)
    assert core.state.internal_state['l0_state']['live_body_read']['status'] == 'CONNECTED'
    assert all(m in ('start', 'observe') for m, _ in bridge.calls)


def test_serializable_graph_and_no_semantic_action_labels(runs):
    core, _ = runs()
    saved, _, _ = chain(core, (0, 5))
    assert json.loads(json.dumps(saved)) == saved
    encoded = json.dumps(saved)
    assert all(DEFINITIONS[p]['action_id'] not in encoded for p in (0, 5))
    assert all(f['kind'] != 'Shared' or saved['supports'][k][0]['rule'] == 'SHARED_INCIDENCE'
               for k, f in saved['facts'].items())
