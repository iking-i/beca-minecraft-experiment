"""Offline Core lifecycle controls; never use a mainline DB or body process."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from unittest.mock import patch

import pytest

from experimental.formall0_continuous.channel import TestOnlyOperativeConfig, VERSION, KEY
from experimental.formall0_continuous.runner import FakeBridge, observation
from experimental.formall0_operative.validation import initial, operands
from individual.core import ACore
from individual.events import EventStore
from individual.formal_l0 import digest
from individual.identity import ExperimentInUse


def child(database, phase, history=True):
    command = [sys.executable, '-m', 'experimental.formall0_continuous.runner', phase, str(database)]
    if not history:
        command.append('--history-off')
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                            env={**os.environ, 'PYTHONUTF8': '1'}, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def create(database, history=True):
    return ACore(database, FakeBridge(), initialize_lifetime=True, full_history_enabled=history,
        test_only_operative=TestOnlyOperativeConfig(str(database), origin_state=initial()[0]))


def reopen(database):
    return ACore(database, FakeBridge(), test_only_operative=TestOnlyOperativeConfig(str(database)))


def journal_partial(record):
    return next(p for kind, p in record['journal'] if kind == 'RECURSIVE_PARTIAL_OUTPUT')


def current(database):
    with sqlite3.connect(database) as db:
        return json.loads(db.execute('SELECT snapshot FROM current_state').fetchone()[0])


def capture(core, raw, transform=lambda value: value):
    """Exact Core input; isolate output before persistence, no substitute consumer."""
    result = {}
    advance = core._engine.advance

    def actual(state, frame, version, actions):
        result['input'] = deepcopy(state)
        return advance(transform(deepcopy(state)), frame, version, actions)

    def before_commit(observation, fields, sequence, internal, frame, journal):
        result['state'] = internal.to_dict()
        result['partial'] = next(p for k, p in journal if k == 'RECURSIVE_PARTIAL_OUTPUT')
        raise Captured()

    with patch.object(core._engine, 'advance', side_effect=actual), \
            patch.object(core, '_commit_observation', side_effect=before_commit), \
            pytest.raises(Captured):
        core.accept_observation(raw)
    return result


class Captured(Exception):
    pass


@pytest.fixture
def formed(tmp_path):
    db = tmp_path / 'test-only.db'
    a = child(db, 'create')
    s0 = a['start']['internal_state']['l0_state']['operative_test_only']['edges'][0]
    s1, = [e for e in a['committed']['internal_state']['l0_state']['operative_test_only']['edges'] if e != s0]
    return db, a, s0, s1


@pytest.mark.parametrize('history', [True, False])
def test_actual_process_restart_authoritative_state_and_reentry(tmp_path, history):
    db = tmp_path / 'same-a.db'
    first = child(db, 'create', history)
    s0, s1 = first['committed']['internal_state']['l0_state']['operative_test_only']['edges']
    saved = current(db)
    assert saved == first['shutdown']
    second = child(db, 'resume', history)
    assert first['pid'] != second['pid'] != os.getpid()
    assert first['lease_released'] and second['lease_released']
    assert first['closed'] and second['closed']
    assert first['start']['individual_id'] == second['shutdown']['individual_id']
    assert second['start']['state_version'] == first['shutdown']['state_version'] + 1
    assert second['start']['session_id'] != first['shutdown']['session_id']
    original_graph = saved['internal_state']['l0_state']['operative_test_only']
    assert second['start']['internal_state']['l0_state']['operative_test_only'] == original_graph
    assert first['start']['internal_state']['l0_state']['operative_test_only']['edges'] == [s0]
    formation = journal_partial(first['records'][1])
    assert s1 not in formation['processing']['operative_dependencies']['dependencies']
    evidence = original_graph['evidence'][digest(s1)]
    assert evidence['supports']['experience_id'] == formation['experience']['experience_id']
    assert evidence['supports']['integration_id'] == first['committed']['internal_state']['latest_integration']['integration_id']
    assert any(k == 'TEMPORAL_LINK_UNRESOLVED' for k, _ in second['records'][0]['journal'])
    assert not any(k == 'RECURSIVE_PARTIAL_OUTPUT' for k, _ in second['records'][0]['journal'])
    for record in second['records'][1:]:
        assert s1 in journal_partial(record)['processing']['operative_dependencies']['dependencies']
        assert record['after']['state_version'] == record['before']['state_version'] + 1
        assert record['after']['internal_state']['l0_state']['operative_test_only']['evidence'][digest(s1)] == evidence
    assert current(db) == second['shutdown']
    with sqlite3.connect(db) as connection:
        assert connection.execute('SELECT COUNT(*) FROM experiment').fetchone()[0] == 1
        if not history:
            assert connection.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0
            assert connection.execute('SELECT COUNT(*) FROM states').fetchone()[0] == 0
            assert connection.execute('SELECT COUNT(*) FROM audit_gaps').fetchone()[0] == 1


def test_s1_only_ablation_actual_comparison_and_no_control_commit(formed):
    db, first, s0, s1 = formed
    child(db, 'resume')
    core = reopen(db)
    try:
        before = current(db)
        core.accept_observation(observation(6, 5))  # Existing carrier-gap boundary.
        before = current(db)
        raw = observation(7, 6)
        normal = capture(core, raw)

        def ablate(state):
            state['l0_state']['operative_test_only']['edges'].remove(s1)
            return state

        negative = capture(core, raw, ablate)
        assert normal['input'] == negative['input']
        assert operands(normal['partial']) != operands(negative['partial'])
        assert normal['partial']['processing']['outcome_previously_observed'] is True
        assert negative['partial']['processing']['outcome_previously_observed'] is None
        assert current(db) == before and core.state.to_dict() == before
    finally:
        core.shutdown()


@pytest.mark.parametrize('mode', ['removed', 'swapped', 'unified'])
def test_provenance_does_not_change_core_computation(formed, mode):
    db, _, s0, s1 = formed
    child(db, 'resume')
    core = reopen(db)
    try:
        core.accept_observation(observation(6, 5))
        normal = capture(core, observation(7, 6))

        def labels(state):
            evidence = state['l0_state']['operative_test_only']['evidence']
            if mode == 'removed':
                evidence.clear()
            else:
                for e in evidence.values():
                    e['provenance'] = 'NEUTRAL' if mode == 'unified' else (
                        'INTERNALLY_FORMED' if e['provenance'] == 'ORIGIN_SUPPLIED' else 'ORIGIN_SUPPLIED')
            return state

        alternate = capture(core, observation(7, 6), labels)
        assert operands(normal['partial']) == operands(alternate['partial'])
    finally:
        core.shutdown()


@pytest.mark.parametrize('defect', ['default', 'wrong_version', 'wrong_database', 'origin_again'])
def test_restart_rejection_precedes_any_store_write(formed, defect):
    db, _, _, _ = formed
    before = db.read_bytes()
    config = TestOnlyOperativeConfig(str(db))
    if defect == 'wrong_version':
        config = replace(config, mechanism_version='unknown')
    elif defect == 'wrong_database':
        config = replace(config, database=str(db.parent / 'different.db'))
    elif defect == 'origin_again':
        config = replace(config, origin_state=initial()[0])
    with patch('individual.core.EventStore', side_effect=AssertionError('Must reject before write')), pytest.raises(ValueError):
        ACore(db, FakeBridge(), test_only_operative=None if defect == 'default' else config)
    assert db.read_bytes() == before


@pytest.mark.parametrize('defect', ['missing_endpoint', 'missing_entry', 'duplicate', 'empty', 'wrong_schema'])
def test_invalid_origin_leaves_no_database(tmp_path, defect):
    db = tmp_path / 'invalid.db'
    state, edge = initial()
    graph = state['l0_state']['operative_test_only']
    if defect == 'missing_endpoint':
        del state['relations'][edge['target']]
    elif defect == 'missing_entry':
        state['l0_state']['feedback']['next_relation_ref'] = 'missing'
    elif defect == 'duplicate':
        graph['edges'].append(deepcopy(edge))
    elif defect == 'empty':
        graph['edges'].clear()
    else:
        graph['schema'] = 'unknown'
    with pytest.raises(ValueError):
        ACore(db, FakeBridge(), initialize_lifetime=True,
              test_only_operative=TestOnlyOperativeConfig(str(db), origin_state=state))
    assert not db.exists()


def test_existing_ordinary_database_not_silently_converted(tmp_path):
    db = tmp_path / 'ordinary.db'
    core = ACore(db, FakeBridge(), initialize_lifetime=True)
    core.shutdown()
    before = db.read_bytes()
    with pytest.raises(ValueError):
        reopen(db)
    assert db.read_bytes() == before


def test_lease_and_mode_exclusivity(formed):
    db, _, _, _ = formed
    core = reopen(db)
    try:
        before = current(db)
        with pytest.raises(ExperimentInUse):
            reopen(db)
        assert current(db) == before
        with pytest.raises(ValueError):
            ACore(db, FakeBridge(), froi=True, test_only_operative=TestOnlyOperativeConfig(str(db)))
        assert current(db) == before
    finally:
        core.shutdown()


def test_failed_atomic_commit_rolls_back_state_and_events(formed):
    db, _, _, _ = formed
    core = reopen(db)
    try:
        before = core.state.to_dict()
        count = core._store.connection.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        core._store.connection.execute("CREATE TEMP TRIGGER fail_test_only_event BEFORE INSERT ON events WHEN NEW.event_type='WORLD_OBSERVATION' BEGIN SELECT RAISE(ABORT,'injected commit failure'); END")
        with pytest.raises(sqlite3.IntegrityError):
            core.accept_observation(observation(3, 2))
        assert current(db) == before and core.state.to_dict() == before
        assert core._store.connection.execute('SELECT COUNT(*) FROM events').fetchone()[0] == count
    finally:
        core.shutdown()


def test_runtime_restoration_never_reads_full_audit(formed):
    db, _, _, s1 = formed
    statements = []
    original = sqlite3.connect

    def traced(*args, **kwargs):
        connection = original(*args, **kwargs)
        connection.set_trace_callback(statements.append)
        return connection

    with patch('sqlite3.connect', side_effect=traced), patch('individual.inspect.verify', side_effect=AssertionError('No full audit')):
        core = reopen(db)
        try:
            core.accept_observation(observation(3, 2))
        finally:
            core.shutdown()
    reads = [s.lower() for s in statements if s.lstrip().lower().startswith('select')]
    assert not any(' from events' in s or ' from states' in s for s in reads)
    assert any('from current_state' in s for s in reads)


def test_guarded_state_writeback_cannot_drop_metadata_or_committed_edge(formed):
    db, _, _, s1 = formed
    core = reopen(db)
    try:
        before = current(db)
        for defect in ('metadata', 'edge', 'version'):
            state = deepcopy(before['internal_state'])
            if defect == 'metadata':
                del state['l0_state'][KEY]
            elif defect == 'version':
                state['l0_state'][KEY]['mechanism_version'] = 'invalid'
            else:
                state['l0_state']['operative_test_only']['edges'].remove(s1)
            with pytest.raises(ValueError):
                core._transition('TEST_ONLY_INVALID_CONTROL', {}, internal_state=state)
            assert current(db) == before and core.state.to_dict() == before
    finally:
        core.shutdown()


@pytest.mark.parametrize('defect', ['metadata_version', 'metadata_identity', 'metadata_database', 'missing_endpoint', 'duplicate_edge', 'missing_collection'])
def test_invalid_restored_snapshot_rejected_before_writer(formed, defect):
    db, _, _, s1 = formed
    with sqlite3.connect(db) as connection:
        row = list(connection.execute('SELECT state_version,individual_id,timestamp,snapshot FROM current_state').fetchone())
    state = json.loads(row[3])
    local = state['internal_state']['l0_state']
    if defect == 'metadata_version':
        local[KEY]['mechanism_version'] = 'invalid'
    elif defect == 'metadata_identity':
        local[KEY]['individual_id'] = 'another-individual'
    elif defect == 'metadata_database':
        local[KEY]['database'] = str(db.parent / 'another.db')
    elif defect == 'missing_endpoint':
        del state['internal_state']['relations'][s1['target']]
    elif defect == 'duplicate_edge':
        local['operative_test_only']['edges'].append(deepcopy(s1))
    else:
        del local['operative_test_only']
    row[3] = json.dumps(state)
    before = db.read_bytes()
    with patch('experimental.formall0_continuous.channel.current_row', return_value=row), \
            patch('individual.core.EventStore', side_effect=AssertionError('No writer permitted')), pytest.raises(ValueError):
        reopen(db)
    assert db.read_bytes() == before


def test_origin_caps_conflict_rejected_before_database_creation(tmp_path):
    db = tmp_path / 'invalid-caps.db'
    state, _ = initial()
    state['l0_state']['locked_caps']['relations'] += 1
    with pytest.raises(ValueError):
        ACore(db, FakeBridge(), initialize_lifetime=True,
              test_only_operative=TestOnlyOperativeConfig(str(db), origin_state=state))
    assert not db.exists()


def test_origin_commit_failure_remains_marked_and_cannot_be_adopted_by_default(tmp_path):
    db = tmp_path / 'incomplete-test.db'
    with patch('experimental.formall0_continuous.channel.initialize_state', side_effect=RuntimeError('origin commit interrupted')), pytest.raises(RuntimeError):
        create(db)
    assert KEY not in current(db)['internal_state']['l0_state']
    before = db.read_bytes()
    with patch('individual.core.EventStore', side_effect=AssertionError('No default adoption')), pytest.raises(ValueError):
        ACore(db, FakeBridge())
    with pytest.raises(ValueError):
        reopen(db)
    assert db.read_bytes() == before
