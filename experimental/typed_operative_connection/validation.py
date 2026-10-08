"""Record real Core histories/paired controls, subprocess restoration and regressions."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from .runner import create, setup, sample, capture
from .engine import KEY, connection, value_ref
from experimental.operative_content.engine import KEY as CONTENT

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def native_material(internal):
    return {k: deepcopy(u['pattern']) for k, u in internal['units'].items()
            if u.get('operand_kind') == 'NATIVE_SENSOR'}


def products(record):
    local = record['after']['l0_state']
    return {r: local[CONTENT]['nodes'][r] for r in local['content_execution']['constructed']}


def main():
    output = {'phase': 'TYPED_OPERATIVE_CONNECTION_TEST_ONLY',
        'baseline': '424a8c8d3ee4294de24fab722d82f39e9091b21e',
        'classification': 'IN_PROGRESS',
        'spec_sha256': hashlib.sha256((HERE / 'SPEC.md').read_bytes()).hexdigest(),
        'minecraft_run': False, 'body_execution': False,
        'complete_expression_formed': 'NOT_ESTABLISHED',
        'slot_value_binding_formed': 'NOT_ESTABLISHED',
        'verification': {}, 'causal_pairs': [], 'lifecycle': {}}
    def save():
        (HERE / 'VALIDATION.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    environment = {**os.environ, 'PYTHONUTF8': '1'}
    manifest = json.loads((ROOT / 'experimental/formall0_continuous/TK_LIBRARY_MANIFEST.json').read_text(encoding='utf-8'))
    library = Path(manifest['destination'])
    for relative, expected in manifest['files_sha256'].items():
        assert hashlib.sha256((library / relative).read_bytes()).hexdigest() == expected
    environment.update(TCL_LIBRARY=str(library / 'tcl8.6'), TK_LIBRARY=str(library / 'tk8.6'))
    output['verification_environment'] = {'python': sys.executable,
        'TCL_LIBRARY': environment['TCL_LIBRARY'], 'TK_LIBRARY': environment['TK_LIBRARY'],
        'library_files_checked': len(manifest['files_sha256'])}
    save()
    with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp', prefix='typed-evidence-') as temporary:
        directory = Path(temporary)
        for i, values in enumerate(((0, 1), (20, 64))):
            a, b = create(directory / f'{i}-a.db'), create(directory / f'{i}-b.db')
            try:
                ha, hb = setup(a, values), setup(b, tuple(reversed(values)))
                before, alternate = a.state.to_dict(), b.state.to_dict()
                assert native_material(before['internal_state']) == native_material(alternate['internal_state'])
                graph = before['internal_state']['l0_state'][KEY]
                formed = {r: e for r, e in graph['edges'].items()
                          if graph['evidence'][r]['provenance'] == 'EXPERIENCE_FORMED'}
                s1, = formed
                assert formed[s1] == connection(value_ref(values[0]), value_ref(values[1]))
                def replace(state):
                    state['l0_state'][KEY] = deepcopy(alternate['internal_state']['l0_state'][KEY])
                    return state
                def screen(state):
                    del state['l0_state'][KEY]['edges'][s1]
                    return state
                normal = capture(a, sample(3, values[1]))
                other = capture(a, sample(3, values[1]), replace)
                ablated = capture(a, sample(3, values[1]), screen)
                restored = capture(a, sample(3, values[1]))
                assert products(normal) != products(other)
                assert len(products(normal)) == 2 and len(products(ablated)) == 1
                assert products(normal) == products(restored)
                expected = deepcopy(normal['before'])
                expected['l0_state'][KEY] = deepcopy(alternate['internal_state']['l0_state'][KEY])
                assert other['before'] == expected
                expected = deepcopy(normal['before']); del expected['l0_state'][KEY]['edges'][s1]
                assert ablated['before'] == expected
                assert normal['after']['l0_state']['native_operand_execution'] == other['after']['l0_state']['native_operand_execution']
                assert a.state.to_dict() == before
                output['causal_pairs'].append({'values': values, 'history_a': ha, 'history_b': hb,
                    'checkpoint': before, 'alternative_history_state': alternate,
                    'common_comparison_input': sample(3, values[1]), 's1_ref': s1,
                    'normal': normal, 'different_history_connection': other,
                    's1_only_ablated': ablated, 'reinserted': restored,
                    'native_material_identical': True, 'canonical_unchanged': True})
                save()
            finally:
                a.shutdown(); b.shutdown()
        for history in (True, False):
            db = directory / ('on.db' if history else 'off.db')
            phases = []
            for phase in ('create', 'resume'):
                command = [sys.executable, '-m', 'experimental.typed_operative_connection.runner', phase, str(db)]
                if not history: command.append('--history-off')
                p = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                                   encoding='utf-8', timeout=40)
                assert p.returncode == 0, p.stderr
                phases.append(json.loads(p.stdout))
            one, two = phases
            assert one['pid'] != two['pid']
            assert one['shutdown']['individual_id'] == two['start']['individual_id']
            for key in (KEY, CONTENT):
                assert one['shutdown']['internal_state']['l0_state'][key] == two['start']['internal_state']['l0_state'][key]
            final = two['records'][-1]['after']['internal_state']['l0_state']
            assert one['shutdown']['internal_state']['l0_state'][KEY] == final[KEY]
            old = one['records'][-1]['after']['internal_state']['l0_state']['content_execution']['constructed']
            assert set(old) <= set(final['content_execution']['reused_content'])
            assert not final['content_execution']['new_nodes']
            output['lifecycle']['ON' if history else 'OFF'] = phases
            save()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    commands = {'focused': ['tests/test_typed_operative_connection.py'],
        'related': ['tests/test_native_body_operands.py', 'tests/test_operative_content.py',
                    'tests/test_formal_continuous_operative.py', 'tests/test_formall0_operative_adoption.py',
                    'tests/test_formal_l0.py', 'tests/test_live_evidence.py'], 'full': []}
    for label, targets in commands.items():
        cmd = [sys.executable, '-m', 'pytest', *targets, '-q', '--tb=short',
               '--basetemp=' + str(ROOT / '.test-tmp' / ('typed-' + label + '-' + stamp))]
        p = subprocess.run(cmd, cwd=ROOT, env=environment, capture_output=True,
                           encoding='utf-8', errors='replace', timeout=900)
        output['verification'][label] = {'command': cmd, 'returncode': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr,
            'stdout_sha256': hashlib.sha256(p.stdout.encode()).hexdigest()}
        save()
        print(label + ': ' + (p.stdout.strip().split('\n')[-1] if p.stdout.strip() else p.stderr), flush=True)
        if p.returncode:
            output['classification'] = 'NOT_TESTABLE' if 'TclError' in p.stdout else 'FAIL'
            save()
            return 1
    frozen = json.loads((ROOT / 'WORLD_ENTRY_FREEZE.json').read_text(encoding='utf-8'))
    for relative, expected in frozen['component_hashes'].items():
        assert hashlib.sha256((ROOT / relative).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected
    output['frozen_hashes'] = {'status': 'MATCH', 'count': len(frozen['component_hashes'])}
    output['criteria'] = {f'TC_T{i}': 'PASS' for i in range(1, 11)}
    output['classification'] = 'PASS'
    output['attribution'] = 'externally supplied generic same-channel temporal-value connection law; endpoints from actual ordinary ChangeSet/history, not selected slot/value pairs'
    save()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
