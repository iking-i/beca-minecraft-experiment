"""External evidence recorder; shared test measurement helpers, not an executor."""
from copy import deepcopy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import runpy
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '76fee923fd1ea2d3b4697e299f1c35f9d6c8817e'


def evidence():
    # Helpers drive real ACore and stop controls before commit. No graph/answer
    # executor is loaded here. The runner subprocesses import no test module.
    helpers = runpy.run_path(str(ROOT / 'tests/test_formal_continuous_operative.py'))
    child, reopen, capture = (helpers[k] for k in ('child', 'reopen', 'capture'))
    def current(database):
        with closing(sqlite3.connect(database)) as db:
            return json.loads(db.execute('SELECT snapshot FROM current_state').fetchone()[0])
    observation, operands, partial = (helpers[k] for k in ('observation', 'operands', 'journal_partial'))
    record = {'base_commit': BASE, 'scope': 'independent TEST_ONLY ACore, synthetic raw observations, FakeBridge',
              'full_history_runs': {}, 'provenance_used_for_execution': False,
              'minecraft_run': False, 'real_mainline_a_created': False,
              'body_changed': False, 'sampler_binder_changed': False,
              'default_acore_behavior_changed': False, 'full_history_replay_required': False}
    with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp', prefix='operative-continuous-evidence-') as directory:
        for enabled in (True, False):
            database = Path(directory) / ('on.db' if enabled else 'off.db')
            first = child(database, 'create', enabled)
            committed = current(database)
            second = child(database, 'resume', enabled)
            restored = second['start']['internal_state']['l0_state']['operative_test_only']
            original = committed['internal_state']['l0_state']['operative_test_only']
            assert restored == original
            s0, s1 = original['edges']
            assert s1 not in partial(first['records'][1])['processing']['operative_dependencies']['dependencies']
            assert s1 in partial(second['records'][1])['processing']['operative_dependencies']['dependencies']
            assert first['start']['individual_id'] == second['shutdown']['individual_id']
            assert first['pid'] != second['pid']
            assert second['start']['state_version'] == first['shutdown']['state_version'] + 1
            assert current(database) == second['shutdown']
            with closing(sqlite3.connect(database)) as db:
                modes = db.execute('SELECT full_history_enabled FROM session_recording_modes').fetchall()
                counts = {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                          for table in ('experiment', 'states', 'events', 'audit_gaps')}
                integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
                assert integrity == 'ok'
            if not enabled:
                assert counts['events'] == counts['states'] == 0
            core = reopen(database)
            try:
                core.accept_observation(observation(6, 5))  # New carrier's existing gap handling.
                before = current(database)
                normal = capture(core, observation(7, 6))

                def ablate(state):
                    state['l0_state']['operative_test_only']['edges'].remove(s1)
                    return state

                negative = capture(core, observation(7, 6), ablate)
                assert normal['input'] == negative['input']
                reconstructed = ablate(deepcopy(normal['input']))
                index = normal['input']['l0_state']['operative_test_only']['edges'].index(s1)
                reconstructed['l0_state']['operative_test_only']['edges'].insert(index, s1)
                assert reconstructed == normal['input']
                assert operands(normal['partial']) != operands(negative['partial'])
                assert normal['partial']['processing']['outcome_previously_observed'] is True
                assert negative['partial']['processing']['outcome_previously_observed'] is None
                neutrality = {}
                for mode in ('removed', 'swapped', 'unified'):
                    def labels(state, mode=mode):
                        audit = state['l0_state']['operative_test_only']['evidence']
                        if mode == 'removed':
                            audit.clear()
                        else:
                            for value in audit.values():
                                value['provenance'] = 'NEUTRAL' if mode == 'unified' else (
                                    'INTERNALLY_FORMED' if value['provenance'] == 'ORIGIN_SUPPLIED' else 'ORIGIN_SUPPLIED')
                        return state
                    result = capture(core, observation(7, 6), labels)
                    assert operands(normal['partial']) == operands(result['partial'])
                    neutrality[mode] = {'same_operands': True, 'processing': result['partial']['processing']}
                assert current(database) == before and core.state.to_dict() == before
            finally:
                core.shutdown('TEST_ONLY_control_end')
            record['full_history_runs']['ON' if enabled else 'OFF'] = {
                'first_process': first, 'second_process': second,
                'authoritative_snapshot_after_first_shutdown': committed,
                'S0': s0, 'S1': s1, 'S1_restored_exact': True,
                'S1_reformed_after_restart': False,
                'S1_formation_evidence_preserved': True,
                'normal_shutdown_and_lease_release': first['lease_released'] and second['lease_released'],
                'session_recording_modes': modes, 'audit_counts': counts, 'sqlite_integrity': integrity,
                'control_input': normal['input'], 'control_raw_observation': observation(7, 6),
                'normal_processing': normal['partial']['processing'],
                'S1_only_ablated_processing': negative['partial']['processing'],
                'controls_stopped_before_commit': True, 'reinsert_S1_restores_exact_state': True,
                'provenance_controls': neutrality}
    frozen = json.loads((ROOT / 'WORLD_ENTRY_FREEZE.json').read_text(encoding='utf-8'))
    record['frozen_hashes_match'] = {p: hashlib.sha256((ROOT / p).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == h
                                    for p, h in frozen['component_hashes'].items()}
    assert all(record['frozen_hashes_match'].values())
    record['classification'] = 'NOT_ESTABLISHED'  # Final regression is independently required.
    record['criteria'] = {f'CR_T{i}': 'PASS' for i in range(1, 9)}
    record['criteria'].update(CR_T9='NOT_ESTABLISHED', CR_T10='NOT_ESTABLISHED')
    return record


if __name__ == '__main__':
    output = ROOT / '.test-tmp/continuous-causal-evidence.json'
    output.write_text(json.dumps(evidence(), ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(str(output))
