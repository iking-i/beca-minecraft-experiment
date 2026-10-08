"""Record ordinary-Core causal evidence and unmodified test execution logs."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from individual.internal_state import InternalState
from experimental.formall0_continuous.runner import observation
from .runner import create, reopen, capture
from .engine import KEY, VERSION, evaluate

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    output = {'version': VERSION, 'baseline': 'b155848bcd335453189d6ec0d6c426d4dedb4d5a',
        'scope': 'independent TEST_ONLY ACore, synthetic observations, generic Pair construction',
        'spec_sha256': hashlib.sha256((HERE / 'SPEC.md').read_bytes()).hexdigest(),
        'minecraft_run': False, 'real_mainline_a_created': False,
        'sampler_binder_used': False, 'body_expression_formed': False,
        'verification_environment': {'python': sys.executable,
            'TCL_LIBRARY': os.environ.get('TCL_LIBRARY'),
            'TK_LIBRARY': os.environ.get('TK_LIBRARY'),
            'existing_library_manifest': 'experimental/formall0_continuous/TK_LIBRARY_MANIFEST.json'},
        'criteria': {}, 'verification': {}, 'lifecycle': {}, 'causal_pair': {}}
    scratch = ROOT / '.test-tmp'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='content-evidence-') as temporary:
        directory = Path(temporary)
        for history in (True, False):
            database = directory / ('on.db' if history else 'off.db')
            phases = []
            for phase in ('create', 'resume'):
                command = [sys.executable, '-m', 'experimental.operative_content.runner', phase, str(database)]
                if not history: command.append('--history-off')
                process = subprocess.run(command, capture_output=True, encoding='utf-8',
                    env={**os.environ, 'PYTHONUTF8': '1'}, timeout=40)
                if process.returncode: raise RuntimeError(process.stderr)
                phases.append(json.loads(process.stdout))
            first, second = phases
            assert first['pid'] != second['pid']
            assert first['shutdown']['individual_id'] == second['start']['individual_id']
            assert first['shutdown']['internal_state']['l0_state'][KEY] == second['start']['internal_state']['l0_state'][KEY]
            output['lifecycle']['ON' if history else 'OFF'] = phases
        database = directory / 'paired.db'
        core = create(database)
        try:
            core.accept_observation(observation(1, 0))
            core.accept_observation(observation(2, 1))
            checkpoint = core.state.to_dict()
            s0, s1 = checkpoint['internal_state']['l0_state']['operative_test_only']['edges']
            normal = capture(core, observation(3, 2))
            def ablate(state):
                state['l0_state']['operative_test_only']['edges'].remove(s1)
                return state
            ablated = capture(core, observation(3, 2), ablate)
            restored = capture(core, observation(3, 2))
            def products(record):
                local = record['after']['l0_state']
                refs = local['content_execution']['constructed']
                internal = InternalState.from_dict(record['after'])
                return {key: {'node': local[KEY]['nodes'][key], 'value': evaluate(internal, key)} for key in refs}
            assert products(normal) != products(ablated)
            assert products(normal) == products(restored)
            assert normal['partial']['processing']['expected_outcomes'] != ablated['partial']['processing']['expected_outcomes']
            assert core.state.to_dict() == checkpoint
            output['causal_pair'] = {'checkpoint': checkpoint, 's0': s0, 's1': s1,
                'normal': normal, 's1_only_ablated': ablated, 'reinserted': restored,
                'normal_products': products(normal), 'ablated_products': products(ablated),
                'canonical_state_unchanged': True}
        finally:
            core.shutdown()
    # Do not exclude Monitor or change any historical test. Each basetemp is fresh.
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    commands = {
        'focused': ['tests/test_operative_content.py'],
        'related': ['tests/test_formal_continuous_operative.py', 'tests/test_formall0_operative_adoption.py',
                    'tests/test_formal_l0.py', 'tests/test_live_evidence.py'],
        'full': [],
    }
    for name, targets in commands.items():
        command = [sys.executable, '-m', 'pytest', *targets, '-q', '--tb=short',
                   '--basetemp=' + str(scratch / ('content-' + name + '-' + stamp))]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8',
            errors='replace', env={**os.environ, 'PYTHONUTF8': '1'}, timeout=900)
        output['verification'][name] = {'command': command, 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr,
            'stdout_sha256': hashlib.sha256(result.stdout.encode()).hexdigest()}
        (HERE / 'VALIDATION.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(name + ': ' + result.stdout.strip().split('\n')[-1], flush=True)
        if result.returncode:
            output['status'] = 'NOT_TESTABLE' if 'TclError' in result.stdout else 'FAIL'
            break
    else:
        output['status'] = 'PASS'
        output['criteria'] = {f'GC_T{i}': 'PASS' for i in range(1, 11)}
    (HERE / 'VALIDATION.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if output['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
