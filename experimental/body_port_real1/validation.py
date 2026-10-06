"""BPC-R1 offline acceptance. Writes only new measurement reports."""
from dataclasses import asdict, replace, is_dataclass, fields
from hashlib import sha256
from pathlib import Path
import argparse
import json

from .prototype import (load_candidates, encode_real, connections, screen, canonical,
                        BodyPort, Member, Support, Organization, Shared, form)


DEFAULT_DATABASE = 'storage/individuals/A-71bc612c-8f2c-4f70-8d4d-3d38bed52942/individual.db'


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def structural(value):
    if is_dataclass(value):
        return {'type': type(value).__name__, 'fields': {f.name: structural(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, (set, frozenset)):
        return {'set': sorted((structural(x) for x in value), key=canonical)}
    if isinstance(value, tuple):
        return {'tuple': [structural(x) for x in value]}
    return value


def fact_id(value):
    return sha256(canonical(structural(value)).encode()).hexdigest()


def run(database):
    before_hash = digest(database)
    candidates, rejected, cutoff = load_candidates(database)
    report = {'stage': 'BPC-R1', 'scope': 'TEST_ONLY offline real formal history; formation only',
              'selection_rule': 'lexicographically smallest eligible experience_id, event_id tie-break; no formation-result search',
              'source_database': str(Path(database).resolve()), 'source_database_sha256': before_hash,
              'cutoff': cutoff, 'eligible_experiences': len(candidates), 'rejected': rejected,
              'classification': 'NOT_TESTABLE', 'Minecraft_started': False, 'formed_execution_connected': False,
              'bootstrap_authorship': 'EXTERNAL_FIXED_POLICY / TEST_ONLY as recorded; not internally authored',
              'causality': 'temporal_association_only', 'runtime_changed': False}
    if candidates:
        e = candidates[0]
        material, c = encode_real(e)
        organization = form(material)
        edge = Shared(frozenset((c, e.port)))
        result = connections(organization, c)
        controls = {}
        for name, item in (('experience_deleted_before_formation', e.experience),
                           ('port_deleted_before_formation', e.port),
                           ('observation_deleted_before_formation', e.after)):
            controls[name] = connections(form(screen(material, (item,))), c)['status'] == 'UNRESOLVED'
        for name, damaged in (('input_experience_absent', replace(e, experience=None)),
                              ('input_port_absent', replace(e, port=None))):
            try:
                encode_real(damaged)
            except ValueError:
                controls[name] = True
            else:
                controls[name] = False
        absent_change = json.loads(e.after.content)
        absent_change['payload']['delta']['changes'] = []
        try:
            encode_real(replace(e, after=replace(e.after, content=canonical(absent_change))))
        except ValueError:
            controls['input_change_absent'] = True
        else:
            controls['input_change_absent'] = False
        controls['experience_root_removed'] = connections(screen(organization, (e.experience,)), c)['status'] == 'UNRESOLVED'
        controls['port_identity_removed'] = connections(screen(organization, (e.port,)), c)['status'] == 'UNRESOLVED'
        controls['necessary_observation_removed'] = connections(screen(organization, (e.after,)), c)['status'] == 'UNRESOLVED'
        controls['formed_edge_removed'] = connections(screen(organization, (edge,)), c)['status'] == 'UNRESOLVED'
        # Disconnected material is explicitly TEST_ONLY, not a new real experience.
        marker_a, marker_b = ('TEST_ONLY_DISTRACTOR', 1), ('TEST_ONLY_DISTRACTOR', 2)
        distractor = Member('TEST_ONLY_DISCONNECTED_GROUP', marker_a), Member('TEST_ONLY_DISCONNECTED_GROUP', marker_b)
        dmaterial = Organization(material.facts | frozenset(distractor), material.supports |
                                 frozenset(Support(f, 'TEST_ONLY_INPUT', frozenset()) for f in distractor), False)
        dorg = form(dmaterial)
        controls['unrelated_distractor'] = (connections(dorg, c) == result and
            {s for s in dorg.supports if s.conclusion == edge} == {s for s in organization.supports if s.conclusion == edge})
        # Ambiguity is a detached reader control, never represented as real history.
        alternative = BodyPort(e.port.version, 0 if e.port.code != 0 else 1)
        ambiguous_edge = Shared(frozenset((c, alternative)))
        amb = Organization(organization.facts | {alternative, ambiguous_edge}, organization.supports |
                          {Support(alternative, 'TEST_ONLY_INPUT', frozenset()),
                           Support(ambiguous_edge, 'TEST_ONLY_READER_INTERVENTION', frozenset((c, alternative)))})
        ambiguous = connections(amb, c)
        controls['multiple_ports_no_selection'] = ambiguous['status'] == 'AMBIGUOUS' and len(ambiguous['ports']) == 2
        proofs = tuple(p for p in organization.supports if p.conclusion == edge)
        formation_ok = (edge not in material.facts and edge in organization.facts and
                        result == {'status': 'CONNECTED', 'ports': (e.port,)} and
                        any(p.rule == 'SHARED_INCIDENCE' for p in proofs))
        report.update({'witness': {'individual_id': e.individual_id, 'session_id': e.session_id,
                                  'experience_id': e.experience_id, 'action_id': e.action_id,
                                  'port': asdict(e.port), 'execution_status': e.execution_status,
                                  'action_authorship': json.loads(e.request.content)['payload']['provenance']['decision_authorship'],
                                  'before_frame_id': json.loads(e.before.content)['payload']['frame_id'],
                                  'after_frame_id': json.loads(e.after.content)['payload']['frame_id']},
                       'real_experience': asdict(e), 'change': asdict(c),
                       'source_event_digests': {r.identity: sha256(r.content.encode()).hexdigest() for r in e.roots},
                       'formed_fact_index': {fact_id(f): structural(f) for f in organization.facts},
                       'all_direct_supports': sorted(({'conclusion': fact_id(p.conclusion), 'rule': p.rule,
                                                     'premises': sorted(fact_id(x) for x in p.premises)}
                                                    for p in organization.supports), key=canonical),
                       'formation': {'seed_has_connection': False, 'formed_has_connection': edge in organization.facts,
                                     'direct_supports': [repr(p) for p in proofs],
                                     'change_fact_count': len(c.changes), 'consumer_status': result['status']},
                       'negative_controls': controls,
                       'negative_control_scope': 'detached real-witness support screening; distractor and ambiguity reader intervention TEST_ONLY',
                       'classification': 'PASS' if formation_ok and all(controls.values()) else 'FAIL'})
    report['source_database_unchanged'] = digest(database) == before_hash
    if not report['source_database_unchanged']:
        report['classification'] = 'FAIL'
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', default=DEFAULT_DATABASE)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    directory = Path(args.output)
    directory.mkdir(parents=True, exist_ok=False)
    report = run(args.database)
    (directory / 'validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding='utf-8')
    summary = {k: v for k, v in report.items() if k not in ('real_experience', 'change', 'rejected', 'source_event_digests',
                                                         'formed_fact_index', 'all_direct_supports')}
    (directory / 'validation.md').write_text('# BPC-R1 real-history acceptance\n\n```json\n' + json.dumps(summary, indent=2) + '\n```\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
