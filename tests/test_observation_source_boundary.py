"""Source representation controls; no Minecraft or old database writes."""
from copy import deepcopy
import hashlib
import json
import sqlite3
import pytest

from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from experimental.observation_source_boundary.lifecycle import BoundaryCore
from experimental.observation_source_boundary.effects.channel import EffectConfig
from experimental.observation_source_boundary.reference.references import KEY, resolve, fact_ref
from experimental.observation_source_boundary.store import using
from tests.test_ordinary_pair_usage import Carrier
from individual.internal_state import InternalState
from individual.formal_l0 import digest
from experimental.native_body_operands.engine import unit_identity


def create(path, origin=True, history=True):
    bridge = Carrier()
    config = EffectConfig(str(path), origin_state=initial()[0] if origin else None)
    core = BoundaryCore(path, bridge, config=config, initialize_lifetime=origin,
                        full_history_enabled=history)
    bridge.core = core
    return core


def test_initial_and_complete_source_storage(tmp_path):
    c = create(tmp_path / 'new.db')
    try:
        c.accept_observation(sample(1, 0))
        pool = c.state.internal_state['l0_state'][KEY]
        assert pool['observations']['count'] == 1
        assert all(type(f) is str for f in pool['sources'].values())
        with using(c._source_store):
            from individual.internal_state import InternalState
            i = InternalState.from_dict(c.state.internal_state)
            source = pool['current_source']
            assert c._source_store.get(source['frame_id']) == source
            channel = next(iter(source['numeric_channels']))
            assert resolve(i, fact_ref(i, source['frame_id'], channel))['value'] == source['numeric_channels'][channel]
            assert c._source_store.audit()['sources'] == 1
    finally:
        c.shutdown()


def test_effect_and_feedback_rule_unchanged(tmp_path):
    c = create(tmp_path / 'effects.db')
    try:
        c.accept_observation(sample(1, 0)); c.bootstrap_once()
        c.accept_observation(sample(2, 1)); c.accept_observation(sample(3, 0))
        c.accept_observation(sample(4, 1)); c.accept_observation(sample(5, 1))
        assert c._bridge.calls == [{'code':16, 'parameters':{'slot':0}}, {'code':16, 'parameters':{'slot':1}}]
        assert c._source_store.audit()['sources'] == 5
        assert c._store.latest_state().to_dict() == c.state.to_dict()
    finally:
        c.shutdown()


def test_off_resume_same_a(tmp_path):
    path = tmp_path / 'off.db'
    c = create(path, history=False)
    c.accept_observation(sample(1, 0)); c.accept_observation(sample(2, 1))
    iid, version = c.state.individual_id, c.state.state_version
    c.shutdown()
    d = create(path, origin=False, history=False)
    try:
        assert d.state.individual_id == iid and d.state.state_version > version
        assert d._source_store.audit()['sources'] == 2
        d.accept_observation(sample(3, 1))
        assert d._store.connection.execute('SELECT count(*) FROM states').fetchone()[0] == 0
        assert d._source_store.audit()['sources'] == 3
    finally:
        d.shutdown()


def test_atomic_source_and_current_state_failure(tmp_path):
    c = create(tmp_path / 'atomic.db', history=False)
    try:
        c.accept_observation(sample(1, 0))
        before = c.state.to_dict()
        c._source_store.fail_after_sources = True
        with pytest.raises(RuntimeError, match='publication failure'):
            c.accept_observation(sample(2, 1))
        assert c.state.to_dict() == before == c._store.latest_state().to_dict()
        assert c._store.connection.execute('SELECT count(*) FROM os_sources').fetchone()[0] == 1
        assert c._source_store._header()['count'] == 1
        assert c._source_store.pending is None
        c._source_store.fail_after_sources = False
        assert c._source_store.audit()['sources'] == 1
        c.accept_observation(sample(2, 1))
    finally:
        c._source_store.fail_after_sources = False
        c.shutdown()


@pytest.mark.parametrize('change', ['frame', 'channel', 'digest', 'namespace', 'node'])
def test_exact_address_rejection(tmp_path, change):
    c = create(tmp_path / (change + '.db'))
    try:
        c.accept_observation(sample(1, 0))
        i = InternalState.from_dict(c.state.internal_state)
        source = i.l0_state[KEY]['current_source']
        with using(c._source_store):
            ref = fact_ref(i, source['frame_id'], next(iter(source['numeric_channels'])))
            if change in ('namespace', 'node'):
                ref = {'type':'ObservationRef', 'namespace':source['namespace'],
                       'node':unit_identity({'type':'ObservedValue','value_type':'integer','value':0})}
                ref[change] = 'foreign'
            else:
                ref[{'frame':'frame_id','channel':'channel_id','digest':'source_digest'}[change]] = 'forged'
            with pytest.raises(ValueError):
                resolve(i, ref)
    finally:
        c.shutdown()


def test_equal_values_do_not_collapse_facts(tmp_path):
    c = create(tmp_path / 'facts.db')
    try:
        c.accept_observation(sample(1, 0)); c.accept_observation(sample(2, 0))
        i = InternalState.from_dict(c.state.internal_state)
        frames = [r[0] for r in c._store.connection.execute('SELECT frame_id FROM os_sources ORDER BY ordinal')]
        with using(c._source_store):
            channel = next(iter(c._source_store.get(frames[0])['numeric_channels']))
            a, b = (fact_ref(i, f, channel) for f in frames)
            assert a != b and resolve(i, a) == resolve(i, b)
    finally:
        c.shutdown()


def test_current_object_epoch_and_membership(tmp_path):
    c = create(tmp_path / 'objects.db')
    try:
        raw = sample(1, 0)
        c.accept_observation(raw)
        i = InternalState.from_dict(c.state.internal_state)
        from experimental.native_body_operands.engine import typed_inputs
        source = i.l0_state[KEY]['current_source']
        objects = {n:p for n,p in typed_inputs(source).items() if p['type']=='ObservedReference'}
        assert objects, 'Fixture must contain a real declared object reference'
        ref = {'type':'ObservationRef','namespace':source['namespace'],'node':next(iter(objects))}
        with using(c._source_store):
            assert resolve(i, ref)['type'] == 'ObservedReference'
            i.l0_state[KEY]['current_source']['references'] = []
            with pytest.raises(ValueError, match='Stale'):
                resolve(i, ref)
            i.l0_state[KEY]['current_source'] = deepcopy(source)
            i.l0_state[KEY]['current_source']['body_epoch'] += 1
            with pytest.raises(ValueError, match='Stale'):
                resolve(i, ref)
    finally:
        c.shutdown()


def test_real_capacity_refusal_has_no_source_commit(tmp_path):
    from experimental.operative_content.engine import identity, ContentCapacityError
    c = create(tmp_path / 'capacity.db')
    try:
        c.accept_observation(sample(1, 0)); c.bootstrap_once(); c.accept_observation(sample(2, 1))
        c.accept_observation(sample(3, 0))
        state = deepcopy(c.state.internal_state); pool = state['l0_state'][KEY]
        right = next(k for k,n in pool['nodes'].items() if n['type']=='BodyRef'); left = right
        while len(state['units']) + len(pool['nodes']) < 64:
            node = {'type':'Pair','left':left,'right':right}; left = identity(node)
            pool['nodes'][left] = node; pool['node_evidence'][left] = {'source':'capacity_control'}
        c._transition('TEST_ONLY_CAPACITY_CONTROL', {}, internal_state=state)
        before = c.state.to_dict()
        with pytest.raises(ContentCapacityError):
            c.accept_observation(sample(4, 1))
        assert c.state.to_dict() == before == c._store.latest_state().to_dict()
        assert c._source_store.audit()['sources'] == 3
    finally:
        c.shutdown()


def corrupt_body(core, frame, body='{}'):
    db = core._store.connection
    db.execute('DROP TRIGGER immutable_os_sources_UPDATE')
    with db:
        db.execute('UPDATE os_sources SET body=? WHERE frame_id=?', (body, frame))
    core._source_store.cache.clear()


def test_unused_corruption_detection_timing_is_explicit(tmp_path):
    c = create(tmp_path / 'timing.db')
    try:
        for n in range(1, 11):
            c.accept_observation(sample(n, 0))
        frames = [r[0] for r in c._store.connection.execute('SELECT frame_id FROM os_sources ORDER BY ordinal')]
        corrupt_body(c, frames[6])  # not incidence/current/atom witness/route support
        c.accept_observation(sample(11, 0))  # documented difference from frozen validator
        with pytest.raises((ValueError, KeyError)):
            c._source_store.get(frames[6])
        with pytest.raises((ValueError, KeyError)):
            c._source_store.audit()
    finally:
        c.shutdown()


def test_missing_current_source_restart_rejects_before_writes(tmp_path):
    path = tmp_path / 'missing.db'; c = create(path, history=False)
    c.accept_observation(sample(1, 0)); frame = c.state.observation_frame['frame_id']; c.shutdown()
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('DROP TRIGGER immutable_os_sources_DELETE')
        db.execute('DELETE FROM os_sources WHERE frame_id=?', (frame,))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        create(path, origin=False)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_no_old_database_adoption_or_default_takeover(tmp_path):
    from tests.test_ordinary_pair_usage import create as old_create
    from individual.core import ACore
    path = tmp_path / 'old.db'; c = old_create(path, origin_state=initial()[0]); c.shutdown()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        create(path, origin=False)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    path = tmp_path / 'new.db'; c = create(path); c.shutdown()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        ACore(path, Carrier())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_on_off_on_keeps_gap_and_sources(tmp_path):
    path = tmp_path / 'modes.db'; iid = None
    for n, mode in enumerate((True, False, True), 1):
        c = create(path, origin=n==1, history=mode)
        try:
            iid = iid or c.state.individual_id
            assert c.state.individual_id == iid
            c.accept_observation(sample(n, 0))
            assert c._source_store.audit()['sources'] == n
            assert c._store.latest_state().internal_state == c.state.internal_state
        finally:
            c.shutdown()
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT count(*) FROM audit_gaps').fetchone()[0] == 1
        assert [r[0] for r in db.execute('SELECT full_history_enabled FROM session_recording_modes ORDER BY rowid')] == [1,0,1]


def test_effect_ablation_and_restore_still_changes_operations(tmp_path):
    from experimental.observation_source_boundary.effects.engine import KEY as FX
    c = create(tmp_path / 'ablation.db')
    try:
        c.accept_observation(sample(1,0)); c.bootstrap_once()
        c.accept_observation(sample(2,1)); c.accept_observation(sample(3,0))
        state = c.state.internal_state; frame = c._encoder.encode(sample(4,1),4,c._body_epoch)
        def advance(current):
            with using(c._source_store):
                try:
                    return c._engine.advance(current, deepcopy(frame),c.state.state_version+1,[])[0]
                finally:
                    c._source_store.pending = None
        a = advance(state)
        without = deepcopy(state); without['l0_state'][FX]['routes'] = {}; without['l0_state'][FX]['supports'] = {}
        b = advance(without); restored = advance(state)
        assert a.l0_state[FX]['current']['operations'] == restored.l0_state[FX]['current']['operations']
        assert a.l0_state[FX]['current']['operations'] and not b.l0_state[FX]['current']['operations']
    finally:
        c.shutdown()


def test_actual_process_restart_and_interrupted_transaction(tmp_path):
    import subprocess, sys
    path = tmp_path / 'process.db'
    def run(phase):
        return subprocess.run([sys.executable,'-B','-X','utf8','-m',
            'experimental.observation_source_boundary.worker',phase,str(path)],
            capture_output=True,text=True,encoding='utf-8',timeout=60)
    a = run('create'); assert a.returncode == 0, a.stderr
    before = json.loads(a.stdout)
    crash = run('crash'); assert crash.returncode == 73, crash.stderr
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT count(*) FROM os_sources').fetchone()[0] == 1
        assert db.execute('SELECT count FROM os_boundary').fetchone()[0] == 1
    b = run('resume'); assert b.returncode == 0, b.stderr
    after = json.loads(b.stdout)
    assert before['pid'] != after['pid']
    assert before['individual_id'] == after['individual_id']
    assert after['after_version'] > before['after_version']
    assert before['sources'] == 1 and after['sources'] == 2
    assert before['authoritative'] and after['authoritative']


def test_wrong_version_or_database_refuses_before_writer(tmp_path):
    path = tmp_path / 'guard.db'; c = create(path); c.shutdown()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    for config in (EffectConfig(str(path),version='wrong'), EffectConfig(str(tmp_path/'other.db'))):
        with pytest.raises(ValueError):
            BoundaryCore(path, Carrier(), config=config)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_ambiguous_index_and_corrupt_witness_fail_closed(tmp_path):
    c = create(tmp_path / 'index.db')
    try:
        c.accept_observation(sample(1,0))
        i = InternalState.from_dict(c.state.internal_state)
        source = i.l0_state[KEY]['current_source']
        node = unit_identity({'type':'ObservedValue','value_type':'integer','value':0})
        ref = {'type':'ObservationRef','namespace':source['namespace'],'node':node}
        fake = {'type':'ObservedValue','value_type':'integer','value':1}
        with c._store.connection:
            c._store.connection.execute('INSERT INTO os_atoms VALUES(?,?,?,?,?)',
                (source['namespace'],node,digest(fake),json.dumps(fake),source['frame_id']))
        with using(c._source_store):
            with pytest.raises(ValueError): resolve(i,ref)
            with pytest.raises(ValueError): c._source_store.audit()
        # Stop without invoking corrupted state validators; this is an isolated
        # deliberately broken database, never repaired by the implementation.
    finally:
        c._store.close(); c._lease.release(); c._closed = True


def test_body_read_count_and_state_size_do_not_grow_with_stable_sources(tmp_path):
    c = create(tmp_path/'reads.db',history=False)
    try:
        counts, sizes = [], []
        for n in range(1,21):
            c.accept_observation(sample(n,0))
            if n in (10,20):
                counts.append(c._source_store.reads)
                sizes.append(len(json.dumps(c.state.internal_state,separators=(',',':'))))
        assert counts[1] <= counts[0] + 1
        assert sizes[1] - sizes[0] < 1000
        assert c._source_store.header['count'] == 20
        assert len(c._source_store.cache) == 0  # cleared at transition boundary
    finally:
        c.shutdown()
