"""Read-only, evidence-linked stage-3 acceptance; event counts alone are insufficient."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sqlite3

from .inspect import verify


KINDS = ('RECURSIVE_PROCESS_CREATED', 'RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED',
         'DOWNWARD_FEEDBACK_UPDATED', 'RECURSION_GENERATED', 'COUNTEREXAMPLE_RETAINED',
         'ACTION_REQUESTED', 'ACTION_EXECUTED', 'EXPERIENCE_FORMED', 'OBSERVATION_FRAME',
         'UNIT_CREATED', 'UNIT_ARCHIVED', 'RECURSIVE_PROCESS_STATUS', 'RESOURCE_OBSERVED')


def audit_legacy(database, include_sample=False, check_chain=True, session_id=None):
    db = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('BEGIN')
        if db.execute('SELECT 1 FROM states LIMIT 1').fetchone() is None:
            raise ValueError('Experiment initialization is not committed yet')
        result = verify(database, connection=db) if check_chain else {}
        from .lifetime import history_summary
        histories = history_summary(database, db)
        if session_id == 'latest':
            if not histories['Experiment_session_history']:
                raise ValueError('No recorded sessions')
            session_id = histories['Experiment_session_history'][-1]['session_id']
        if session_id and not any(s['session_id'] == session_id for s in histories['Experiment_session_history']):
            raise ValueError('Unknown session_id')
        query = f"SELECT e.event_sequence,e.state_version,e.event_type,e.payload FROM events e WHERE event_type IN ({','.join('?' for _ in KINDS)})"
        arguments = KINDS
        if session_id:
            query += ' AND e.state_version IN (SELECT state_version FROM state_sessions WHERE session_id=?)'
            arguments = (*KINDS, session_id)
        rows = list(db.execute(query + ' ORDER BY event_sequence', arguments))
        events = [(seq, version, kind, json.loads(raw)) for seq, version, kind, raw in rows]
        counts = Counter(kind for _, _, kind, _ in events)
        publications, partials, integrations, feedbacks = defaultdict(list), {}, {}, {}
        actions, frames, experiences = {}, {}, {}
        feedback_generations = []
        for seq, version, kind, payload in events:
            record = {'event_sequence': seq, 'state_version': version, 'payload': payload}
            if kind == 'RECURSIVE_PARTIAL_OUTPUT':
                publications[payload['process_id']].append(record)
                partials[payload['partial_id']] = record
            elif kind == 'INTEGRATION_COMPLETED':
                integrations[payload['integration_id']] = record
            elif kind == 'DOWNWARD_FEEDBACK_UPDATED':
                feedbacks[payload['integration_id']] = record
            elif kind == 'RECURSION_GENERATED':
                feedback_id = payload.get('feedback_integration_id')
                prior = feedbacks.get(feedback_id)
                if prior and prior['state_version'] < version and payload['granted_quantity'] > 0:
                    before, after = prior['payload']['before'], prior['payload']['after']
                    root = payload['root']
                    old_q = before['pattern_quantities'].get(root, before['default_quantity'])
                    new_q = after['pattern_quantities'].get(root, after['default_quantity'])
                    if payload['requested_quantity'] == new_q and (old_q != new_q or
                        payload['parameters']['condition_resolution'] == after['condition_resolution'] != before['condition_resolution']):
                        feedback_generations.append({'feedback': prior, 'generation': record,
                            'previous_requested_quantity': old_q, 'actual_requested_quantity': new_q})
            elif kind == 'ACTION_EXECUTED' and payload.get('initiator') in ('internal_structure', 'external_fixed_policy', 'mixed_policy'):
                actions[payload['action_id']] = record
            elif kind == 'OBSERVATION_FRAME':
                frames[payload['frame_id']] = record
            elif kind == 'EXPERIENCE_FORMED':
                experiences[payload['experience_id']] = record
        repeated = {pid: values for pid, values in publications.items() if len(values) >= 2 and
                    len({v['payload']['experience']['frame_id'] for v in values}) >= 2}
        integrated_process_outputs = []
        for record in integrations.values():
            p = record['payload']
            linked = [partials[pid] for pid in p['input_partial_ids'] if pid in partials]
            if linked and p['operations'] and record['state_version'] >= linked[0]['state_version']:
                integrated_process_outputs.append(record)
        # Structural revisions and generation feedback must be persisted, not just printed.
        persisted_feedback = []
        integration_ids = {record['payload']['integration_id'] for record in integrated_process_outputs}
        for item in feedback_generations:
            if item['feedback']['payload']['integration_id'] not in integration_ids:
                continue
            v = item['feedback']['state_version']
            row = db.execute('SELECT snapshot FROM states WHERE state_version=?', (v,)).fetchone()
            state = json.loads(row[0])
            if state['internal_state']['generation_parameters'] == item['feedback']['payload']['after']:
                persisted_feedback.append(item)
        checks = {'first_recursion_created': counts['RECURSIVE_PROCESS_CREATED'] > 0,
                  'same_process_returns_information_repeatedly': bool(repeated),
                  'information_integration_from_process_output': bool(integrated_process_outputs),
                  'internal_structure_changes_persisted': bool(persisted_feedback),
                  'changed_structure_used_in_later_generation': bool(persisted_feedback)}
        sample = None
        if include_sample:
            for integration in integrated_process_outputs:
                for pid in integration['payload']['input_partial_ids']:
                    partial = partials.get(pid)
                    if not partial:
                        continue
                    exp = partial['payload']['experience']
                    if not exp['action_ids']:
                        continue
                    action = actions.get(exp['action_ids'][-1])
                    if not action or action['payload']['action_code'] not in (1, 2) or not action['payload']['provenance'].get('integration_id'):
                        continue
                    upstream = integrations.get(action['payload']['provenance']['integration_id'])
                    first, second = (frames.get(fid) for fid in exp['frame_ids'])
                    earlier_partials = [partials[p] for p in upstream['payload']['input_partial_ids'] if p in partials] if upstream else []
                    changed_position = first and second and first['payload']['spatial_data']['position'] != second['payload']['spatial_data']['position']
                    if upstream and earlier_partials and changed_position and upstream['state_version'] <= action['state_version'] < second['state_version']:
                        sample = {'observation_before_action': first, 'recursive_output_before_action': earlier_partials[0],
                                  'earlier_information_integration': upstream,
                                  'action': action, 'new_observation': second,
                                  'partial_output_after_action': partial, 'information_integration_after_action': integration}
                        break
                if sample:
                    break
        final_row = db.execute('SELECT snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
        final = json.loads(final_row[0])
        retained = 0
        archived = {}
        for raw, in db.execute("SELECT payload FROM events WHERE event_type='RELATION_ARCHIVED'"):
            relation = json.loads(raw)['relation']
            archived.setdefault(relation['relation_id'], set()).update(relation['outcomes'])
        for _, _, kind, payload in events:
            if kind != 'COUNTEREXAMPLE_RETAINED':
                continue
            available = set(final['internal_state']['relations'].get(payload['relation_id'], {}).get('outcomes', {})) | archived.get(payload['relation_id'], set())
            retained += set(payload['preserved_outcomes']) <= available
        result.update(histories)
        result.update({'audit_scope': 'session' if session_id else 'lifetime', 'session_id': session_id,
                       'closed_loop_observed': False,
                       'legacy_engineering_closed_loop_observed': all(checks.values()), 'checks': checks,
                       'counts': dict(counts), 'processes_with_repeated_publications': len(repeated),
                       'feedback_generations': persisted_feedback[:3],
                       'counterexamples_observed': counts['COUNTEREXAMPLE_RETAINED'],
                       'counterexamples_still_represented': retained,
                       'counterexample_preservation': ('all_recorded_exceptions_retained' if retained == counts['COUNTEREXAMPLE_RETAINED'] else 'requires_review') if counts['COUNTEREXAMPLE_RETAINED'] else 'not_observed_in_this_run',
                       'final_structure': {key: len(final['internal_state'][key]) for key in ('units', 'relations', 'active_processes')},
                       'test_world_properties_verified_by_this_tool': False,
                       'note': 'Historical engineering feedback only: fixed policies are not internal authorship or upward recursion.',
                       'profile': 'legacy_policy_debug', 'formal_stage_goal_observed': False,
                       'upward_recursion_observed': False, 'upward_recursion_count': 0,
                       'classifications': {'WITHIN_LAYER_RECURSION': False,
                           'CURRENT_LIMIT_ENCOUNTER': False, 'LIMIT_FEEDBACK_REENTERED_RECURSION': False,
                           'ARCHITECTURE_LIMIT_RECOGNITION_CANDIDATE': False,
                           'EXTERNAL_POLICY_EFFECT': bool(persisted_feedback),
                           'INTERNAL_VARIABLE_STRUCTURE_CHANGE': False},
                       'classification_scope': 'formal L0 evidence not established by legacy adapter; old engineering loop reported separately',
                       'layer_evidence': 'no higher-layer evidence; historical layer semantics unverified'})
        if include_sample:
            result['actual_event_sample'] = sample
        return result
    finally:
        db.close()


def audit(database, include_sample=False, check_chain=True, session_id=None):
    from .l0_audit import audit_l0, has_formal_history
    # Both adapters classify historical evidence; old fixed-policy successes cannot pass this stage.
    if has_formal_history(database, session_id):
        return audit_l0(database, include_sample, check_chain, session_id)
    return audit_legacy(database, include_sample, check_chain, session_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', help='Defaults to the selected individual lifetime')
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--session-id', help='Session ID or latest; omitted means lifetime history')
    parser.add_argument('--output', help='Save the complete linked result as JSON')
    args = parser.parse_args()
    if args.db is None:
        from .lifetime import resolve_runtime_database
        args.db = str(resolve_runtime_database())
    result = audit(args.db, args.sample, session_id=args.session_id)
    from .storage import save_report
    output = save_report(args.db, 'experiment-audit', result, args.output)
    print(f'Report: {output}')
    print(json.dumps({k: v for k, v in result.items() if k not in ('actual_event_sample', 'feedback_generations')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
