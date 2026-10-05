"""CEC-0 TEST_ONLY report entry. Immutable reads of ended databases; no A startup."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import unittest

from experimental.cec0.codec import canonical, encode_records, produce, query, record_from_events
from experimental.cec0.consumer import consume, screen_witnesses
from experimental.cec0.fixtures import fixture
from experimental.cec0.tests import CEC0Tests

BASELINE = '3568901b5c41394e355a63c2654b994452967d1f'
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'storage/individuals/A-71bc612c-8f2c-4f70-8d4d-3d38bed52942/individual.db'
SESSION = 'S-09272552-fb87-4078-871b-1c752b1d4862'


def file_hash(path):
    h = sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def existing_history(path, session_id):
    """Fixed entire session, every admissible parameter stratum; no outcome search."""
    wal = Path(str(path) + '-wal')
    if wal.exists() and wal.stat().st_size:
        return {'status': 'MATERIAL_UNAVAILABLE', 'reason': 'Immutable source requires checkpointed, quiescent WAL'}
    paths = [p for p in path.parent.iterdir() if p.is_file()]
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns, file_hash(p)) for p in paths}
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        row = db.execute('SELECT start_version FROM sessions WHERE session_id=?', (session_id,)).fetchone()
        end = db.execute('SELECT end_version,reason FROM session_ends WHERE session_id=?', (session_id,)).fetchone()
        if row is None or end is None:
            raise ValueError('Source session must exist and be ended')
        start, stop = row[0], end[0]
        versions = {r[0] for r in db.execute("SELECT json_extract(payload,'$.after.version') FROM events WHERE event_type='BODY_CAPABILITIES_PROVISIONED' AND state_version<=?", (stop,))}
        if versions != {2}:
            raise ValueError('Frozen action-space version unavailable or ambiguous')
        excluded, records, failures = Counter(), [], []
        def event(kind, field, value):
            # Fields are fixed internal constants; input values are SQLite-bound.
            rows = list(db.execute(f"SELECT event_id,individual_id,event_sequence,state_version,event_type,payload FROM events WHERE event_type=? AND json_extract(payload,'$.{field}')=? AND state_version<=?", (kind, value, stop)))
            if len(rows) != 1:
                raise ValueError('Missing/ambiguous exact source: ' + kind)
            r = rows[0]
            return dict(zip(('event_id', 'individual_id', 'event_sequence', 'state_version', 'event_type', 'payload'), (*r[:5], json.loads(r[5]))))
        raw = db.execute("SELECT event_id,individual_id,event_sequence,state_version,event_type,payload FROM events WHERE event_type='EXPERIENCE_FORMED' AND state_version BETWEEN ? AND ? ORDER BY event_sequence", (start, stop))
        # Only small experience rows materialized; never session snapshots or formed graph logs.
        experiences = list(raw)
        for r in experiences:
            x = json.loads(r[5])
            if x['action_code'] < 0 or len(x['action_ids']) != 1:
                excluded['no_single_actual_control'] += 1; continue
            if x['action_statuses'] != ['executed']:
                excluded['action_not_executed'] += 1; continue
            e = dict(zip(('event_id', 'individual_id', 'event_sequence', 'state_version', 'event_type', 'payload'), (*r[:5], x)))
            try:
                sources = (e, event('ACTION_REQUESTED', 'action_id', x['action_ids'][0]),
                           event('ACTION_EXECUTED', 'action_id', x['action_ids'][0]),
                           *(event('OBSERVATION_FRAME', 'frame_id', f) for f in x['frame_ids']))
                records.append(record_from_events(*sources, 2))
            except (ValueError, KeyError) as error:
                failures.append({'event_id': r[0], 'reason': str(error)})
        strata = defaultdict(list)
        for r in records:
            strata[(r.relation.scope, r.parameters_json)].append(r)
        summaries = []
        sufficient = []
        for (scope, parameters), rows in sorted(strata.items()):
            controls, consequences = defaultdict(list), defaultdict(list)
            for r in rows:
                controls[r.relation.ports[1].key].append(r)
                consequences[r.relation.ports[2].key].append(r)
            t1 = any(len({r.relation.ports[0].key for r in rs}) >= 2 for rs in controls.values())
            t2 = any(len(rs) >= 2 for rs in consequences.values())
            summary = {'scope': scope, 'parameters': json.loads(parameters), 'records': len(rows),
                       'T1_input_precondition': t1, 'T2_input_precondition': t2,
                       'experience_ids': [r.relation.name for r in rows],
                       'control_multiplicities': sorted(len(rs) for rs in controls.values()),
                       'consequence_multiplicities': sorted(len(rs) for rs in consequences.values())}
            summaries.append(summary)
            if t1 and t2:
                sufficient.append(rows)
        # No selection of favorable records within a stratum: all admissible material is used.
        empirical = []
        for rows in sufficient:
            endpoints = {n.key:n for r in rows for n in r.relation.ports[1:]}
            qs = tuple(query(endpoints[k]) for k in sorted(endpoints))
            from experimental.gsc0.engine import Caps
            org = produce(encode_records(rows, qs), Caps(nodes=256, inputs=512))
            empirical.append({'status': org.status, 'statistics': json.loads(org.statistics_json),
                              'reads': [asdict(consume(org, q)) for q in qs] if org.status=='COMPLETE' else []})
    after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns, file_hash(p)) for p in paths}
    if before != after:
        raise AssertionError('Historical evidence changed during read-only measurement')
    status = 'INSUFFICIENT_CLEAN_HISTORY' if not sufficient else 'PARTIAL'
    return {'status': status, 'database': path.relative_to(ROOT).as_posix(), 'session': session_id,
            'individual_id': path.parent.name, 'state_range': [start, stop], 'end_reason': end[1],
            'database_sha256': before[path.name][2], 'source_unchanged': True,
            'selection': 'Whole fixed ended session; all single executed controls; exact parameter/scope strata; no outcome-based record subset',
            'total_experiences': len(experiences), 'validated_executed_records': len(records),
            'excluded': dict(excluded), 'invalid_sources': failures, 'strata': summaries,
            'empirical_closures': empirical,
            'T1': 'NOT_EXECUTED', 'T2': 'NOT_TESTABLE' if not sufficient else 'UNRESOLVED',
            'T3': 'NOT_EXECUTED', 'T4': 'NOT_EXECUTED', 'T5': 'NOT_EXECUTED',
            'reason': 'No parameter-controlled stratum satisfies both T1 and T2 input preconditions' if not sufficient else 'Additional empirical item verification not claimed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--session', default=SESSION)
    args = parser.parse_args()
    targets = [ROOT/'CEC0_CONTROL_EFFECT_CORRESPONDENCE.json', ROOT/'CEC0_CONTROL_EFFECT_CORRESPONDENCE.md']
    if any(p.exists() for p in targets):
        parser.error('Never overwrite an existing validation result')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CEC0Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        print('FIRST_BLOCKING_EDGE: independent controls did not all pass; inspect trace; no rule repair')
        return 1
    records = fixture()
    queries = (query(records[0].relation.ports[1]), query(records[0].relation.ports[2]))
    org = produce(encode_records(records, queries))
    reads = [consume(org, q) for q in queries]
    screened = [consume(screen_witnesses(org, r.witness_keys), q) for q, r in zip(queries, reads)]
    history = existing_history(args.database, args.session)
    baseline_files = set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE], cwd=ROOT,text=True).splitlines())
    changed = subprocess.check_output(['git','diff',BASELINE,'--name-only'], cwd=ROOT,text=True).splitlines()
    protected_changes = sorted(baseline_files.intersection(changed))
    if protected_changes:
        raise AssertionError('Baseline tracked files were modified: ' + repr(protected_changes))
    report = {'baseline': BASELINE, 'branch': subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
              'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'implementation_at_measurement': 'UNCOMMITTED_ADDITIONS', 'test_only': True,
              'causality': 'temporal_association_only', 'fixture_structural_validation': 'PASS',
              'tests': {'executed': result.testsRun, 'failures': 0, 'errors': 0},
              'fixture_T1_T6': {f'T{i}':'PASS' for i in range(1,7)},
              'fixture_sources': [json.loads(t) for r in records for t in r.source_events_json],
              'fixture_parameter_stratum': {}, 'formed_statistics': json.loads(org.statistics_json),
              'fixture_reads': [asdict(r) for r in reads], 'screened_reads': [asdict(r) for r in screened],
              'input_vs_derived': {'records':'INPUT', 'Shared':'GSC_DERIVED', 'query_results':'CONSUMER_READ'},
              'organization_direct_supports': org.supports, 'organization_root_witnesses': org.roots,
              'source_registry': [(k,json.loads(t)) for k,t in org.sources],
              'existing_A_empirical_validation': history, 'CEC0': history['status'],
              'runtime_changed': False, 'GSC_rules_changed': False, 'Minecraft_started': False,
              'scope': 'Exact identity temporal correspondence only; UnitRef is compressed channel/kind pattern, not full numerical world consequence; no causal control efficacy or behavioral authorship claim',
              'regression_commands': ['python -B -m unittest experimental.gsc0.tests experimental.gsc1.tests tests.test_froi tests.test_froi_scheduling tests.test_read_checkpoint -v', 'python -B -m unittest discover -s tests -v']}
    with targets[0].open('x',encoding='utf8') as f:
        json.dump(report,f,ensure_ascii=True,indent=2);f.write('\n')
    text = f'''# CEC-0 Control–Effect Correspondence — TEST_ONLY

Baseline: `{BASELINE}`. Branch: `{report['branch']}`. Measurement HEAD: `{report['commit']}`.
Implementation was uncommitted additions when measured; this document does not invent a future commit SHA.

## Frozen test boundary

T1 exact control identity across contexts; T2 exact consequence identity across records;
T3 all forward results; T4 all reverse results; T5 detached Shared-only access screening;
T6 no selection, semantics, ranking, execution, or parameter completion.
No GSC production rule or formal runtime changed. The codec uses the frozen Engine directly.

## Actual results

Independent tests: {result.testsRun}/{result.testsRun} passed. Fixture T1–T6: PASS.
Forward fixture read returns both Y1 and Y7; reverse returns both C3 and C9.
Screening all corresponding query/record Shared witnesses produces empty results;
screening one endpoint's witnesses reduces the set by one. Input/Condition/records/proofs
remain unchanged and closure is not re-executed during screening.
Negative pair has different control and consequence and no matching Shared incidence.
Source-ID, source-order and seed-order controls preserve results; distinct catalog versions
produce distinct control identities. Parameter mismatch is rejected, not silently pooled.

Fixture is fully synthetic legal-source material from experimental/cec0/fixtures.py.
It is not existing-A empirical validation. Exact events, supports, roots, and returned endpoint
→ record → Shared evidence are saved in the adjacent JSON. Consumer takes no raw history;
removing raw producer material from its view does not change answers.

## Existing formal source

Database: `{history['database']}`. Individual: `{history['individual_id']}`.
Session: `{history['session']}`. State range: {history['state_range']}.
End reason: `{history['end_reason']}`. Entire fixed ended session examined, no favorable checkpoint search.
{history['total_experiences']} experiences; {history['validated_executed_records']} single executed
records with exact action and before/after frame provenance validated. Parameter strata are
fully separated; records with no actual control and failed requests are not acknowledgments
of an executed control. All source files in the individual directory retain hashes/mtimes.

Empirical status: **{history['status']}**. {history['reason']}.
Empirical T1/T3/T4/T5 NOT_EXECUTED; T2 input precondition NOT_TESTABLE where insufficient.
No empirical closure or successful empirical consumer claim is substituted with fixture output.

## Provenance and limitations

EXPERIENCE_FORMED + exact ACTION_REQUESTED/ACTION_EXECUTED + before/after OBSERVATION_FRAME
→ input CECRecord(context Node, control Node, consequence Node)
→ frozen GSC Shared with direct supports and finite roots
→ consumer follows only formed exact query/record incidence and returns all endpoint identities.
Control identity is catalog version + numeric code, with no debug action name.
Consequence identity retains baseline UnitRef/pattern_id compression; raw frames/deltas remain
provenance, and are not claimed to be complete numerical consequences.
Correspondence is temporal_association_only, not proof that the control caused the effect.

Regressions are run separately after this report; their executed results are reported in chat,
not silently recorded here as passed in advance. No Minecraft or formal A was started by CEC-0.

Final: **CEC0 = {history['status']}**; **fixture structural validation = PASS**.
No behavior authorship, correct-control choice, parameter solution or learning claim is made.
'''
    with targets[1].open('x',encoding='utf8') as f:
        f.write(text)
    print(json.dumps({'CEC0': report['CEC0'], 'fixture': 'PASS', 'tests': result.testsRun}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
