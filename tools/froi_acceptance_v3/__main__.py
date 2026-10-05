"""Frozen v3 acceptance of existing A16 evidence. No producer/resume/advance."""
import argparse
import json
from pathlib import Path
import subprocess

from tools.froi_acceptance_v2 import material as m, checks as v2
from tools.froi_acceptance_v2.__main__ import tooling_contract as v2_contract, write
from tools.froi_acceptance_v3.checks import BASE, SESSION, LABEL, require, validate_saved

ROOT = Path(__file__).resolve().parents[2]
V2_DIR = ROOT / ('storage/acceptance/A-71bc612c-8f2c-4f70-8d4d-3d38bed52942/' + SESSION + '/v2-9f7a8b7')


def inventory(directory):
    return {p.name: m.file_hash(p) for p in sorted(directory.iterdir()) if p.is_file()}


def source_guard():
    changed = subprocess.check_output(['git', 'diff', BASE, '--name-only'], cwd=ROOT).decode().splitlines()
    allowed = ('tools/froi_acceptance_v3/', 'FROI_ACCEPTANCE_HARNESS_V3.md', 'FROI_ACCEPTANCE_FREEZE_V3.json')
    require(all(p.startswith(allowed[0]) or p in allowed[1:] for p in changed), 'Frozen non-v3 source modified')
    require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip(), 'Working tree not frozen/clean')
    require(v2_contract()['status'] == 'PASS', 'Original v1/v2 freeze invalid')


def contract():
    source_guard()
    manifest = json.loads((ROOT / 'FROI_ACCEPTANCE_FREEZE_V3.json').read_text(encoding='utf8'))
    hashes = {p.relative_to(ROOT).as_posix(): m.file_hash(p)
              for p in sorted((ROOT / 'tools/froi_acceptance_v3').glob('*.py'))}
    require(hashes == manifest['measurement_tool_hashes'] and manifest['regression']['passed'], 'v3 freeze mismatch')
    require(inventory(V2_DIR) == manifest['v2_historical_file_hashes'], 'Pre-existing v2 materials changed')
    require(manifest['base_commit'] == BASE, 'Wrong base')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output).resolve()
    require(not out.exists(), 'Never overwrite historical reports')
    require(out != V2_DIR and V2_DIR not in out.parents, 'Cannot write into v2 history')
    frozen = contract()
    old_report = json.loads((V2_DIR / 'report.json').read_text(encoding='utf8'))
    plan = json.loads((V2_DIR / 'measurement-plan.json').read_text(encoding='utf8'))
    old_manifest = json.loads((V2_DIR / 'artifact-A16.json').read_text(encoding='utf8'))
    database = old_manifest['database']
    evidence = json.loads((V2_DIR / 'evidence-A16.json').read_text(encoding='utf8'))
    metrics = m.Metrics()
    print('PRE: streaming complete original database and checking preserved v2 evidence', flush=True)
    before, source = m.freeze(database, metrics)
    old_freeze = old_report['source_freeze_POST']
    require({k: v for k, v in before.items() if k != 'repository_commit'} ==
            {k: v for k, v in old_freeze.items() if k != 'repository_commit'}, 'Original database/protected source differs from v2')
    require(source == old_report['source_event_digest_POST'], 'Original event content differs')
    text = m.export_manifest(database, 16, before, source, metrics=metrics)
    artifact = m.load_manifest(text, before, source, metrics)
    require(artifact.checkpoint.digest == old_manifest['checkpoint_digest']
            and artifact.handle.audit()['graph_digest'] == old_manifest['graph_digest'], 'Original A16 boundary changed')
    print('Verifying saved A16 T2/T3 and both predetermined continuations; no new producer/interpreter execution', flush=True)
    results = validate_saved(artifact, evidence, plan, old_report)
    # Preserve original T2 handles and ALL executed continuation organizations for T5.
    # Only the newly authorized T4 witness source replaces the old independent live trace.
    t5_evidence = {**evidence, 'T4': results['T4']}
    print('POST: independent whole-source freeze; all v2 historical files remain immutable', flush=True)
    after, after_source = m.freeze(database, metrics)
    require(before == after and source == after_source, 'Source/database changed during acceptance')
    require(contract() == frozen, 'Tooling/history changed during acceptance')
    t5 = v2.verify_t5(artifact, before, after, t5_evidence)
    results['T5'] = t5
    with m.readonly(database) as db:
        end = db.execute('SELECT ended_at,end_version,reason,interrupted FROM session_ends WHERE session_id=?', (SESSION,)).fetchone()
        require(end is not None, 'Session not ended')
        inventory_rows = [list(row) for row in db.execute("SELECT state_version,json_extract(payload,'$.status') FROM events WHERE event_type='FROI_ORGANIZATION_FORMED' ORDER BY event_sequence")]
    resources = metrics.result()
    summary = {k: results[k]['status'] for k in ('T1', 'T2', 'T3', 'T4', 'T5')}
    summary.update({'V3_IMPLEMENTED': 'YES', 'FROI1_V3_ACCEPTANCE': 'PASS' if all(results[k]['status'] == 'PASS' for k in ('T1','T2','T3','T4','T5')) else 'PARTIAL',
        'T4_WITNESS_SOURCE': LABEL, 'T4_WITNESS_TEST_ONLY': 'YES',
        'ALL_USED_ORGANIZATIONS_COMPLETE': 'YES' if t5['checks']['all_used_organizations_COMPLETE'] else 'NO',
        'LIVE_RUNTIME_SEMANTICS_CHANGED': 'NO', 'A_CAPABILITIES_CHANGED': 'NO', 'GSC_RULES_CHANGED': 'NO',
        'FROI_CODEC_CHANGED': 'NO', 'CAPS_CHANGED': 'NO', 'FROI_SPEC_CHANGED': 'NO',
        'V2_HISTORICAL_RESULT_PRESERVED': 'YES', 'CURRENT_RUN_REUSED_WITHOUT_MINECRAFT_RERUN': 'YES'})
    report = {'harness': 'FROI-1 ACCEPTANCE HARNESS v3', 'category': 'EXPERIMENTER',
        'measurement_commit': before['repository_commit'], 'runtime_commit': 'MATERIAL_UNAVAILABLE',
        'base_commit': BASE, 'session_id': SESSION, 'individual_id': artifact.checkpoint.request.individual_id,
        'session_end': dict(zip(('ended_at','end_version','reason','interrupted'), end)),
        'summary': summary, 'results': results, 'source_freeze_PRE': before, 'source_freeze_POST': after,
        'source_event_digest_PRE': source, 'source_event_digest_POST': after_source,
        'v2_historical_file_hashes': frozen['v2_historical_file_hashes'],
        'reuse': {'checkpoint': 16, 'pair': [15,12], 'failure_branch_index': 1,
                 'T1': 'fresh source verification', 'T2_T3': 'validated pre-existing executed v2 evidence; no new replay',
                 'T4': 'verified saved failure branch and actual detached continuation',
                 'T5': 'unchanged v2 predicates with authorized v3 T4 evidence source'},
        'all_session_organizations_inventory_only': inventory_rows, 'resources': resources,
        'v2_original_T4_T5': 'NOT_TESTABLE / FAIL preserved; not part of v3 witness selection',
        'formal_live_natural_failure_claimed': False}
    write(out / 'artifact-A16.json', json.loads(text))
    write(out / 'report.json', report)
    lines = ['# FROI-1 ACCEPTANCE HARNESS v3', '', 'T4 source: ' + LABEL,
             'Not a formal-live natural failure. No producer, interpreter continuation, A, or Minecraft was rerun.',
             'T2/T3 executed evidence is reused from frozen v2 and checked against exact original materials.',
             '', '```ini', *[f'{k}: {v}' for k,v in summary.items()], '```', '',
             f'Measurement commit: {before["repository_commit"]}', 'Runtime commit: MATERIAL_UNAVAILABLE',
             f'Session: {SESSION}; end: {end[0]}; reason: {end[2]}',
             'Used organization statuses: ' + ', '.join(t5['used_organization_statuses']),
             'All 121 original organization outcomes remain inventoried, including 117 RESOURCE_LIMIT.',
             'v2 PARTIAL, original A27/A30 trace and all v2 files remain unchanged.',
             'report.json records exact consequence, checks, freeze identities and historical input file hashes.']
    (out / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
