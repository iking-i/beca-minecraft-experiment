"""TEST_ONLY negative-control histories; no canonical selection, no real-world claim."""
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import time
from unittest.mock import patch
from uuid import uuid4

from individual.action_space import bind_parameters, formal_command
from individual.behavioral_audit import audit_behavior
from individual.bridge import MinecraftBridge, ROOT
from individual.core import ACore
from individual.formal_l0 import FormalL0Engine, FormalLimits, select_uniform_action
from individual.internal_state import InternalState
from individual.lifetime import initialize_lifetime
from individual.observation import ObservationFrame
from individual.storage import INDIVIDUALS, _finish_directory, write_json


def readout(state, frame, pattern):
    internal = InternalState.from_dict(deepcopy(state))
    available = [a['code'] for a in frame['nearby_data']['body']['action_space'] if a['currently_available']]
    code, selection = select_uniform_action(internal, pattern, available)
    parameters = bind_parameters(code, frame, internal, selection)
    return {'command': formal_command(code, parameters), 'selection': selection}


def ablation(state, frame, version, caps):
    """Only detached copies; compare actual recursion read and separate action readout."""
    erased = deepcopy(state)
    erased['relations'] = {}
    probes = []
    pattern = state['l0_state']['current_pattern']
    for variant in (state, erased):
        _, _, journal = FormalL0Engine(caps).advance(deepcopy(variant), ObservationFrame(**deepcopy(frame)), version, [])
        partial = next(p for k, p in journal if k == 'RECURSIVE_PARTIAL_OUTPUT')
        probes.append({'processing': partial['processing'], 'readout': readout(variant, frame, pattern)})
    return {'scope': 'TEST_ONLY detached state; original DB never rewritten',
        'removed': 'relations', 'held_constant': ['frame', 'bootstrap state', 'body', 'caps', 'feedback reference'],
        'before': probes[0], 'after': probes[1],
        'recursive_read_changed': any(probes[0]['processing'][key] != probes[1]['processing'][key]
            for key in ('read_succeeded', 'expected_outcomes')),
        'action_changed': probes[0]['readout']['command'] != probes[1]['readout']['command']}


def parameter_probes(states, frame):
    """Probe every available code, not cherry-picked behavior; never send these commands."""
    available = [a['code'] for a in frame['nearby_data']['body']['action_space'] if a['currently_available']]
    result = []
    for code in available:
        values = []
        for state in states:
            internal = InternalState.from_dict(deepcopy(state))
            selection = {'policy_id': 'formal.action_sampling'}
            parameters = bind_parameters(code, frame, internal, selection)
            values.append({'parameters': parameters, 'binding': selection['parameter_binding']})
        result.append({'code': code, 'values': values, 'parameters_equal': values[0]['parameters'] == values[1]['parameters']})
    return result


def relation_contents(state):
    """Compare substantive retained evidence, not different UUIDs or individual IDs."""
    return {key: {'antecedent': relation['antecedent'], 'action_code': relation['action_code'],
        'evidence_count': relation['evidence_count'],
        'outcomes': {unit: data['evidence_count'] for unit, data in relation['outcomes'].items()}}
        for key, relation in state['relations'].items()}


def canonical_guard():
    """File integrity observations only; never open canonical SQLite or acquire its lease."""
    selection = ROOT / 'individual/lifetime.json'
    if not selection.exists():
        return {'selection_exists': False}
    pin = json.loads(selection.read_text(encoding='utf-8'))
    db = (ROOT / pin['database']).resolve()
    paths = [selection, ROOT/'minecraft/config.json', db,
             *[Path(str(db) + s) for s in ('-wal', '-shm', '.lock')]]
    return {str(p): {'size': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns,
                    **({'sha256': sha256(p.read_bytes()).hexdigest()} if p.stat().st_size < 10_000_000 else {})}
            for p in paths if p.exists()}


def validate(storage_root=INDIVIDUALS):
    storage_root = Path(storage_root).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)
    before = canonical_guard()
    cores, directories, states = [], [], []
    caps = FormalLimits()  # Frozen default ceilings; no resource-monitor claim in this fixture.
    common = None
    try:
        for index, offsets in enumerate(((0, 1, 0, 1, 0), (0, 2, 4, 6, 0))):
            staging = storage_root / ('.behavioral-validation-' + uuid4().hex)
            with patch('individual.internal_state.secrets.randbits', return_value=0):
                registration = initialize_lifetime(staging / 'individual.db')
            directory = _finish_directory(staging, storage_root, registration['individual_id'])
            directories.append(directory)
            config = directory / 'body-fixture.json'
            write_json(config, {})
            write_json(directory/'lifetime.json', {'individual_id': registration['individual_id'],
                'database': 'individual.db', 'role': 'test_fixture', 'mainline_selected': False,
                'label': 'behavioral negative control', 'real_minecraft': False})
            bridge = MinecraftBridge(config, adapter=ROOT/'tests/fixtures/capability_body.js')
            # Equal declared bootstrap initialization, not derived from either history.
            with patch('individual.internal_state.secrets.randbits', return_value=0):
                core = ACore(directory/'individual.db', bridge, session_context={
                    'test_only': True, 'real_minecraft': False, 'history_source': 'controlled numeric observations',
                    'bootstrap_seed': 0, 'history_index': index}, physical_caps=caps)
                core.start()
                cores.append(core)
                deadline = time.monotonic() + 10
                while not bridge.call('status')['connected']:
                    if time.monotonic() >= deadline:
                        raise RuntimeError('Fixture body did not spawn')
                    time.sleep(.01)
                if common is None:
                    common = bridge.call('observe')
                    common['timestamp'] = '2026-10-04T00:00:00+00:00'
                for offset in offsets:
                    raw = deepcopy(common)
                    raw['position']['x'] += offset
                    core.accept_observation(raw)
                core.accept_observation(deepcopy(common))
            states.append(core.state.internal_state)
        frames = [c.state.observation_frame for c in cores]
        # Actual persisted identities remain distinct. Common detached frame for exact counterfactual equality.
        frame = deepcopy(frames[0])
        frame['frame_id'] = 'TEST_ONLY:common-frame'
        frame['delta'] = {}
        normalized = lambda f: {k:v for k,v in f.items() if k not in ('frame_id', 'delta', 'internal_observations')}
        outputs = [readout(s, frame, states[0]['l0_state']['current_pattern']) for s in states]
        erase = ablation(states[0], frame, cores[0].state.state_version + 1, caps)
        probes = parameter_probes(states, frame)
        for core in cores:
            core.execute_discrete_action()  # Actual unchanged formal selector/binder through numeric perform RPC.
            core.accept_observation(core._bridge.call('observe'))
        actual_actions = [deepcopy(c.state.latest_action) for c in cores]
        for core in cores:
            core.shutdown('test_only_behavioral_negative_control')
        audits = [audit_behavior(d/'individual.db') for d in directories]
        actual_equal = actual_actions[0]['args'] == actual_actions[1]['args']
        report = {'BEHAVIORAL_CAUSAL_CLOSURE': 'failed', 'implementation_scope': 'diagnostic_partial',
            'BEHAVIORALLY_BINDING_LIMIT': 'not_tested_in_this_fixture',
            'real_minecraft': False, 'fixture_body_rpc': True, 'test_only': True,
            'validation_individual_ids': [a['individual_id'] for a in audits],
            'databases': [str(d/'individual.db') for d in directories],
            'canonical_guard_kind': 'file metadata and small-file hashes; no canonical SQLite connection',
            'canonical_unchanged': before == canonical_guard(),
            'history_offsets': [[0,1,0,1,0], [0,2,4,6,0]],
            'history_formation': 'Both histories passed ACore observation → FormalL0Engine experience → partial → integration; no behavior fields hand-written.',
            'current_frame_equal_except_identity_and_audit_delta': normalized(frames[0]) == normalized(frames[1]),
            'exact_shared_counterfactual_frame': frame,
            'same_bootstrap_state': states[0]['exploration_state']['random_state'] == states[1]['exploration_state']['random_state'],
            'same_caps': states[0]['l0_state']['locked_caps'] == states[1]['l0_state']['locked_caps'],
            'internal_relation_contents_differ': relation_contents(states[0]) != relation_contents(states[1]),
            'substantive_relation_contents': [relation_contents(s) for s in states],
            'relation_structures': [s['relations'] for s in states],
            'readouts': outputs, 'action_commands_equal': outputs[0]['command'] == outputs[1]['command'],
            'actual_formal_commands_equal': actual_equal,
            'parameter_domain_probes': probes, 'ablation': erase, 'audits': audits,
            'fresh_fixture_frames_after_action': [c.state.observation_frame['frame_id'] for c in cores],
            'missing': ['internal behavioral expression producer', 'history-formed choice/binding control',
                        'internally authored necessary parameters', 'real Minecraft closure consequence'],
            'WORLD_ENTRY_FREEZE_changed': False, 'L1_claimed': False}
        for directory in directories:
            write_json(directory/'reports/behavioral-negative-control.json', report)
        return report
    finally:
        for core in cores:
            core.shutdown('test_only_validation_cleanup')


def main():
    report = validate()
    print(json.dumps({k:report[k] for k in ('BEHAVIORAL_CAUSAL_CLOSURE', 'validation_individual_ids',
        'databases', 'internal_relation_contents_differ', 'action_commands_equal', 'canonical_unchanged')}, indent=2))


if __name__ == '__main__':
    main()
