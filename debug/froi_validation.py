"""FROI-1 implementation regressions, not substitute live T1--T5 acceptance.

Run with local test-network access. Existing validation files are never written.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_EDITS = {'individual/core.py', 'individual/limit_consequences.py', 'supervisor/supervisor.py'}


def guard():
    names = subprocess.check_output(['git', 'ls-files'], cwd=ROOT).decode('utf-8').splitlines()
    return {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in names if name not in IMPLEMENTATION_EDITS}


def run_suite(suite):
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return {'run':result.testsRun, 'failures':[{'test':t.id(),'detail':s} for t,s in result.failures],
            'errors':[{'test':t.id(),'detail':s} for t,s in result.errors], 'successful':result.wasSuccessful()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, help='Verified GitHub main source checkpoint')
    parser.add_argument('--output', required=True, help='New JSON path; existing reports are never overwritten')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        parser.error('Output exists; use a new report path to preserve the previous result')
    before = guard()
    loader = unittest.defaultTestLoader
    formal = run_suite(loader.discover(str(ROOT/'tests'), top_level_dir=str(ROOT)))
    gsc = run_suite(loader.loadTestsFromNames(['experimental.gsc0.tests', 'experimental.gsc1.tests']))
    # This historical control suite requires experiments, not bare unittest import.
    from experimental import gsc0_result_dependence as dependence
    data, classes = [], []
    for case in dependence.cases():
        report, record = dependence.experiment(*case)
        classes.append(report['classification'])
        if record is not None:
            data.append(record)
    dependence.ControlTests.data = data
    persisted = run_suite(loader.loadTestsFromTestCase(dependence.ControlTests))
    node = subprocess.run(['npm.cmd', 'test'], cwd=ROOT/'minecraft', capture_output=True,
                          text=True, encoding='utf-8', errors='replace')
    numbers = re.findall(r'(?m)^.*tests (\d+)\s*$', node.stdout)
    body = {'run':int(numbers[-1]) if numbers else None, 'exit_code':node.returncode,
            'successful':node.returncode==0, 'stdout':node.stdout, 'stderr':node.stderr}
    after = guard()
    changed = [name for name,value in before.items() if after.get(name)!=value]
    success = all(x['successful'] for x in (formal,gsc,persisted,body)) and not changed
    databases = sorted(str(p.relative_to(ROOT)) for p in (ROOT/'storage').rglob('*.db'))
    missing = [
        'Real Minecraft ObservationFrames and their unmodified raw WORLD_OBSERVATION sources',
        'Two actual complete histories H_A/H_B plus their EXPERIENCE_FORMED and partial/action provenance',
        'A real fixed FormalL0 read checkpoint, identical current frame, and next real input for consequence re-entry',
    ]
    report = {'version':'FROI-1', 'baseline_main':args.baseline,
        'implementation_status':'IMPLEMENTED',
        'regression_status':'PASSED' if success else 'FAILED',
        'regression':{'formal_and_integration':formal, 'frozen_gsc':gsc,
            'persisted_result_controls':persisted, 'minecraft_body':body},
        'persisted_result_regression_classifications':classes,
        'test_fixture_scope':'TEST_ONLY FakeBridge controls are not real T1--T5 acceptance',
        'T1':{'status':'NOT_EXECUTED','missing':'real full ObservationFrame/raw history and source verification'},
        'T2':{'status':'NOT_EXECUTED','missing':'real H_A/H_B and a fixed real read checkpoint/current frame'},
        'T3':{'status':'NOT_EXECUTED','missing':'already COMPLETE organization formed from those actual inputs'},
        'T4':{'status':'NOT_EXECUTED','missing':'next real observation consuming the unchanged read-failure consequence'},
        'T5':{'status':'NOT_EXECUTED','missing':'full live T1--T4 context for completeness/pollution controls'},
        'live_data_inventory':databases, 'missing_real_inputs':missing,
        'integrity':{'protected_tracked_files':len(before),'changed':changed,
            'protected_sha256':after},
        'final_FROI_1_classification':'READY_FOR_LIVE_FROI_VALIDATION' if success else 'BLOCKED_BY_REGRESSION_FAILURE',
        'behavioral_authorship_claimed':False, 'official_FROI_pass_claimed':False}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'classification':report['final_FROI_1_classification'],
        'counts':[formal['run'],gsc['run'],persisted['run'],body['run']], 'report':str(output)},ensure_ascii=True))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
