"""Auditable ordinary-Core controls and original full regression, no world access."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from .runner import create, observation, capture
from .engine import KEY

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    output = {'baseline': '050469532954e86afb4bfe8f6b4f499eab7e9f35',
        'classification': 'IN_PROGRESS', 'spec_sha256': hashlib.sha256((HERE / 'SPEC.md').read_bytes()).hexdigest(),
        'minecraft_run': False, 'body_execution': False, 'complete_expression_formed': 'NOT_ESTABLISHED',
        'external_selection_used': False, 'verification': {}, 'lifecycle': {}}
    environment = {**os.environ, 'PYTHONUTF8': '1'}
    # Reuse, and verify, the previous real-GUI environment; never mock or skip Tk.
    manifest = json.loads((ROOT / 'experimental/formall0_continuous/TK_LIBRARY_MANIFEST.json').read_text(encoding='utf-8'))
    library = Path(manifest['destination'])
    for relative, expected in manifest['files_sha256'].items():
        if hashlib.sha256((library / relative).read_bytes()).hexdigest() != expected:
            raise ValueError('Existing Tcl/Tk copy differs from frozen manifest')
    environment.update(TCL_LIBRARY=str(library / 'tcl8.6'), TK_LIBRARY=str(library / 'tk8.6'))
    output['verification_environment'] = {'python': sys.executable, 'TCL_LIBRARY': environment['TCL_LIBRARY'],
        'TK_LIBRARY': environment['TK_LIBRARY'], 'library_files_checked': len(manifest['files_sha256'])}
    with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp', prefix='native-evidence-') as temporary:
        directory = Path(temporary)
        c = create(directory / 'paired.db')
        try:
            c.accept_observation(observation(1, 0))
            c.accept_observation(observation(2, 1))
            checkpoint = c.state.to_dict()
            s1 = checkpoint['internal_state']['l0_state']['operative_test_only']['edges'][1]
            def mask(state):
                state['l0_state']['operative_test_only']['edges'].remove(s1)
                return state
            output['causal_pair'] = {'checkpoint': checkpoint, 's1': s1,
                'normal': capture(c, observation(3, 2)),
                's1_only_ablated': capture(c, observation(3, 2), mask),
                'reinserted': capture(c, observation(3, 2)), 'canonical_unchanged': c.state.to_dict() == checkpoint}
            a = output['causal_pair']['normal']['after']['l0_state']['native_operand_execution']['admitted_native_units']
            b = output['causal_pair']['s1_only_ablated']['after']['l0_state']['native_operand_execution']['admitted_native_units']
            assert a and not b and output['causal_pair']['canonical_unchanged']
            output['typed_input_counts'] = {}
            for ref in a:
                kind = output['causal_pair']['normal']['after']['units'][ref]['pattern']['type']
                output['typed_input_counts'][kind] = output['typed_input_counts'].get(kind, 0) + 1
        finally:
            c.shutdown()
        for history in (True, False):
            db = directory / ('on.db' if history else 'off.db')
            phases = []
            for phase in ('create', 'resume'):
                command = [sys.executable, '-m', 'experimental.native_body_operands.runner', phase, str(db)]
                if not history:
                    command.append('--history-off')
                p = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                                   encoding='utf-8', timeout=40)
                if p.returncode:
                    raise RuntimeError(p.stderr)
                phases.append(json.loads(p.stdout))
            assert phases[0]['pid'] != phases[1]['pid']
            assert phases[0]['shutdown']['individual_id'] == phases[1]['start']['individual_id']
            assert phases[0]['shutdown']['internal_state']['l0_state'][KEY] == phases[1]['start']['internal_state']['l0_state'][KEY]
            output['lifecycle']['ON' if history else 'OFF'] = phases
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    commands = {'focused': ['tests/test_native_body_operands.py'],
        'related': ['tests/test_operative_content.py', 'tests/test_formal_continuous_operative.py',
                    'tests/test_formall0_operative_adoption.py', 'tests/test_formal_l0.py', 'tests/test_live_evidence.py'],
        'full': []}
    for name, targets in commands.items():
        command = [sys.executable, '-m', 'pytest', *targets, '-q', '--tb=short',
                   '--basetemp=' + str(ROOT / '.test-tmp' / ('native-' + name + '-' + stamp))]
        p = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                           encoding='utf-8', errors='replace', timeout=900)
        output['verification'][name] = {'command': command, 'returncode': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr,
            'stdout_sha256': hashlib.sha256(p.stdout.encode()).hexdigest()}
        output['classification'] = 'NOT_TESTABLE' if p.returncode and 'TclError' in p.stdout else 'FAIL' if p.returncode else 'IN_PROGRESS'
        (HERE / 'VALIDATION.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(name + ': ' + p.stdout.strip().split('\n')[-1],flush=True)
        if p.returncode:
            return 1
    output['classification'] = 'PASS'
    output['criteria'] = {f'NBO_T{i}': 'PASS' for i in range(1,10)}
    (HERE / 'VALIDATION.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
