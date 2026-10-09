"""Post-run read-only evidence summary; never called by A or the real runner."""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3

from individual.current_state import current_row
from .run import ROOT, write_json


def summarize(directory):
    directory = Path(directory).resolve()
    report = json.loads((directory / 'REPORT.json').read_text(encoding='utf-8'))
    database = directory / 'individual.db'
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        state = json.loads(current_row(connection)[3])
        events = []
        for seq, kind, version, timestamp, payload in connection.execute(
                'SELECT event_sequence,event_type,state_version,timestamp,payload FROM events ORDER BY event_sequence'):
            events.append({'event_sequence': seq, 'event_type': kind, 'state_version': version,
                           'timestamp': timestamp, 'payload': json.loads(payload)})
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert state == report['shutdown_state']
    assert events[-1]['event_sequence'] == report['final_event_sequence']
    counts = Counter(e['event_type'] for e in events)
    assert dict(counts) == report['event_counts']
    final = report['final_before_shutdown']['internal_state']
    from experimental.observation_interface_references.reference.references import KEY as REF
    from experimental.observation_interface_references.effects.engine import KEY as FX
    rows = []
    source_counts, content_identity, preservation = [], {}, []
    for record in report['records']:
        path = directory / 'frames' / f"E{record['frame']:02d}.json"
        frame = json.loads(path.read_text(encoding='utf-8'))
        assert frame['measurement'] == record
        source = frame['state_after']['internal_state']['l0_state'][REF]['current_source']
        source_counts.append({'frame': record['frame'], 'numeric_channels': len(source['numeric_channels']),
                              'references': len(source['references']), 'body_capabilities': len(source['declarations']),
                              'raw_health': frame['raw_observation'].get('health'),
                              'raw_body_state': frame['raw_observation'].get('bodyState')})
        delta, inventory = record['delta'], record['inventory']
        for ref, material in delta['new_content'].items():
            content_identity[ref] = {'first_frame': record['frame'], **material}
        preservation.append(delta['old_content_unchanged'])
        rows.append({
            'frame': record['frame'], 'version': record['state_version'],
            **inventory, 'new_unit_count': len(delta['new_units']),
            'new_content_count': len(delta['new_content']),
            'new_pair_count': sum(n['node']['type'] == 'Pair' for n in delta['new_content'].values()),
            'read_relations': len(delta['actual_relation_read']),
            'recomputed_old_pairs': len(delta['existing_direct_pairs_recomputed_by_constructor']),
            'explicit_pair_operands': len(delta['explicit_pair_operands_returned_by_ordinary_read']),
            'retained_old_pairs': len(delta['retained_old_pair_ids']),
            'limit_codes': [e['payload']['auditor_metadata']['semantic_code'] for e in delta['limit_events']],
        })
    pairs = {ref for ref, node in final['l0_state'][REF]['nodes'].items() if node['type'] == 'Pair'}
    explicit = set()
    recomputed = set()
    for record in report['records']:
        explicit.update(record['delta']['explicit_pair_operands_returned_by_ordinary_read'])
        recomputed.update(record['delta']['existing_direct_pairs_recomputed_by_constructor'])
    executions = [e for e in events if e['event_type'] == 'ACTION_EXECUTED']
    external = [e for e in executions if e['payload']['initiator'] == 'EXPERIMENTER_SUPPLIED_REAL_BOOTSTRAP']
    recursive = [e for e in executions if e['payload']['initiator'] == 'TEST_ONLY_ORDINARY_OCCURRENCE_EFFECT']
    experiences = [e for e in events if e['event_type'] == 'EXPERIENCE_FORMED']
    membership = {e['payload']['action_id']: [x['event_sequence'] for x in experiences
                    if e['payload']['action_id'] in x['payload']['action_ids']] for e in executions}
    limits = [e for e in events if e['event_type'] == 'CURRENT_LIMIT_ENCOUNTER']
    death = [e for e in events if e['event_type'] == 'BODY_DIED']
    summary = {
        'classification': report['classification'], 'budget_completed': report['committed_frames'] == 32,
        'committed_frames': report['committed_frames'], 'recursive_rounds': len(experiences),
        'ordinary_advance_count': report['committed_frames'],
        'temporal_link_unresolved_events': [e for e in events if e['event_type'] == 'TEMPORAL_LINK_UNRESOLVED'],
        'body_continuity_across_death_claimed': False,
        'individual_id': state['individual_id'], 'session_id': state['session_id'],
        'pre_shutdown_version': report['final_before_shutdown']['state_version'],
        'shutdown_version': state['state_version'], 'final_event_sequence': events[-1]['event_sequence'],
        'same_individual_and_session': all(r['individual_id'] == state['individual_id']
            and r['session_id'] == state['session_id'] for r in report['records']),
        'strictly_increasing_committed_versions': all(a['version'] < b['version'] for a, b in zip(rows, rows[1:])),
        'continuous_runtime_interrupted': report['runtime_interrupted'],
        'started_at': report['started_at'], 'ended_at': report['ended_at'],
        'elapsed_seconds_including_startup_and_shutdown': (
            datetime.fromisoformat(report['ended_at']) - datetime.fromisoformat(report['started_at'])).total_seconds(),
        'rows': rows, 'external_observation_sources': source_counts,
        'content_identity_and_creation_supports': content_identity,
        'all_previous_content_preserved': all(preservation),
        'retained_pairs_actually_returned_as_explicit_read_operands': sorted(pairs & explicit),
        'retained_pairs_recomputed_as_direct_constructor_results': sorted(pairs & recomputed),
        'retained_pairs_never_explicit_ordinary_read_operands': sorted(pairs - explicit),
        'retained_pairs_never_recomputed_in_later_rounds': sorted(pairs - recomputed),
        'external_bootstrap_executions': len(external), 'recursive_body_executions': len(recursive),
        'receipt_experience_membership': membership,
        'body_death_events': death, 'raw_limits': limits,
        'final_inventory': report['final_inventory'],
        'formed_effect_routes': len(final['l0_state'][FX]['routes']),
        'sampler_calls': report['sampler_calls'], 'binder_calls': report['binder_calls'],
        'purpose_need_origin': 'No formed need/purpose representation or allocation/retention mechanism in these engines; temporal_relation_evaluation question is externally initialized',
        'all_external_sources_retained_in_authoritative_internal_state': len(final['l0_state'][REF]['observations']),
        'source_retention_not_unit_charged': True,
        'serialized_size_is_not_RSS': True,
        'database_sha256': before, 'readonly_database_verified': True,
        'report_sha256': hashlib.sha256((directory / 'REPORT.json').read_bytes()).hexdigest(),
        'raw_frame_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (directory / 'frames').glob('*.json')},
    }
    write_json(directory / 'SUMMARY.json', summary)
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    result = summarize(args.directory)
    print(json.dumps({key: result[key] for key in ('classification', 'committed_frames', 'recursive_rounds',
        'individual_id', 'session_id', 'final_inventory', 'external_bootstrap_executions', 'recursive_body_executions')}, ensure_ascii=False))
