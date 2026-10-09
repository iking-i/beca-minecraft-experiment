"""Preserve isolated fresh-DB admission/construction/restart evidence, no body."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from individual.internal_state import InternalState
from individual.formal_l0 import digest
from .runner import create, setup, sample, binding_values
from .references import KEY, body_ref
from .engine import connection, value_ref

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main(destination=None):
    folder = Path(tempfile.mkdtemp(dir=ROOT/'.test-tmp', prefix='body-reference-evidence-'))
    core = create(folder/'canonical.db')
    report = {'classification': 'PENDING_REGRESSION', 'scope': 'TEST_ONLY_reference_admission_and_use',
        'baseline': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
        'minecraft_run': False, 'body_execution': False, 'selector_added': False,
        'adoption_added': False, 'mechanism_version': core._reference_config.version,
        'database': str(folder/'canonical.db'), 'spec_sha256': hashlib.sha256((HERE/'SPEC.md').read_bytes()).hexdigest()}
    try:
        report['history'] = setup(core)
        before = core.state.to_dict()
        report['authoritative_checkpoint'] = core._store.latest_state().to_dict()
        assert report['authoritative_checkpoint'] == before
        pool = before['internal_state']['l0_state'][KEY]
        slot = body_ref(pool['catalog'], 'slot', 16, 'slot')
        target = digest(connection(slot, value_ref(1)))
        variants = {}
        for name in ('present', 'ablated', 'restored'):
            internal = deepcopy(before['internal_state'])
            if name == 'ablated':
                del internal['l0_state'][KEY]['edges'][target]
            frame = core._encoder.encode(sample(4, 1), core.state.environment_sequence + 1, core._body_epoch)
            after, _, journal = core._engine.advance(internal, frame, before['state_version']+1, [])
            variants[name] = {'after': after.to_dict(), 'journal': journal,
                'executed_binding_values': binding_values(after, executed_only=True),
                'post_integration_binding_values': binding_values(after)}
        assert [variants[n]['executed_binding_values'] for n in variants] == [[0, 1], [0], [0, 1]]
        report['edge_only_controls'] = variants
        report['canonical_unchanged_by_controls'] = before == core.state.to_dict()
        core.accept_observation(sample(4, 1))
        report['later_state'] = core._store.latest_state().to_dict()
        assert report['later_state'] == core.state.to_dict()
        report['stored_body_operand_count'] = sum(n['type'] == 'BodyRef' for n in pool['nodes'].values())
        report['unit_counts'] = [len(r['after']['internal_state']['units']) for r in report['history']]
        report['constructed_node_counts'] = [len(r['after']['internal_state']['l0_state'][KEY]['nodes']) for r in report['history']]
    finally:
        core.shutdown('TEST_ONLY_body_reference_evidence_close')
    process_records = []
    for phase in ('create', 'resume'):
        command = [sys.executable, '-X', 'utf8', '-m', 'experimental.body_interface_references.runner',
                   phase, str(folder/'cross-process.db')]
        done = subprocess.run(command, cwd=ROOT, text=True, encoding='utf-8', capture_output=True)
        (folder/f'{phase}.stdout.json').write_text(done.stdout, encoding='utf-8')
        (folder/f'{phase}.stderr.txt').write_text(done.stderr, encoding='utf-8')
        assert done.returncode == 0, done.stderr
        process_records.append(json.loads(done.stdout))
    a, b = process_records
    assert a['pid'] != b['pid']
    assert a['end']['individual_id'] == b['end']['individual_id']
    assert a['end']['internal_state']['l0_state'][KEY] == b['start']['internal_state']['l0_state'][KEY]
    assert b['end']['internal_state']['l0_state']['body_reference_execution']['reused_content']
    report['cross_process'] = process_records
    report['raw_evidence_directory'] = str(folder)
    report['source_sha256'] = {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [*HERE.glob('*.py'), ROOT/'tests/test_body_interface_references.py']}
    path = Path(destination) if destination else HERE/'VALIDATION.json'
    with path.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({'units': report['unit_counts'], 'content_nodes': report['constructed_node_counts'],
        'cross_process_identity': b['end']['individual_id'], 'candidate_values': [0, 1],
        'raw_evidence': str(folder)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
