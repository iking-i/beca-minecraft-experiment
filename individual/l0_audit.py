"""Evidence-based L0 audit. No capacity failure is automatically called recognition."""

from collections import Counter, defaultdict
from contextlib import closing
import json
from pathlib import Path
import sqlite3


def connect(database):
    return sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)


def scope(db, session_id):
    if session_id == 'latest':
        row = db.execute('SELECT session_id FROM sessions ORDER BY start_version DESC LIMIT 1').fetchone()
        if not row:
            raise ValueError('No recorded sessions')
        session_id = row[0]
    if session_id and not db.execute('SELECT 1 FROM sessions WHERE session_id=?', (session_id,)).fetchone():
        raise ValueError('Unknown session_id')
    suffix = ' WHERE state_version IN (SELECT state_version FROM state_sessions WHERE session_id=?)' if session_id else ''
    return session_id, suffix, (session_id,) if session_id else ()


def has_formal_history(database, session_id=None):
    with closing(connect(database)) as db:
        # Empty/incomplete databases go through the existing initialization rejection.
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='sessions'").fetchone():
            return False
        session_id, suffix, args = scope(db, session_id)
        if session_id:
            environment = json.loads(db.execute('SELECT environment FROM sessions WHERE session_id=?', (session_id,)).fetchone()[0])
            if environment.get('experiment_profile') == 'formal_l0':
                return True
        query = 'SELECT 1 FROM events' + suffix
        query += (' AND' if suffix else ' WHERE') + " (event_type='EXPERIMENT_PROFILE_SELECTED' OR (event_type='RECURSIVE_PARTIAL_OUTPUT' AND json_extract(payload,'$.layer')='L0')) LIMIT 1"
        return db.execute(query, args).fetchone() is not None


def audit_l0(database, include_sample=False, check_chain=True, session_id=None):
    from .inspect import verify
    from .lifetime import history_summary
    from .formal_l0 import digest
    with closing(connect(database)) as db:
        db.execute('BEGIN')
        result = verify(database, connection=db) if check_chain else {}
        histories = history_summary(database, db)
        session_id, suffix, args = scope(db, session_id)
        kinds = ('EXPERIMENT_PROFILE_SELECTED', 'CURRENT_LIMIT_ENCOUNTER', 'LIMIT_FEEDBACK_REENTERED_RECURSION',
                 'RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED', 'RECURSIVE_FEEDBACK_STORED',
                 'OBSERVATION_FRAME', 'EXTERNAL_POLICY_EFFECT', 'INTERNAL_VARIABLE_STRUCTURE_CHANGE',
                 'ARCHITECTURE_HYPOTHESIS_PROPOSED', 'RECURSIVE_PROCESS_CREATED', 'RECURSION_GENERATED')
        query = 'SELECT event_sequence,state_version,event_type,payload FROM events' + suffix
        query += (' AND' if suffix else ' WHERE') + f" event_type IN ({','.join('?' for _ in kinds)}) ORDER BY event_sequence"
        records = [{'event_sequence': n, 'state_version': v, 'kind': k, 'payload': json.loads(p)}
                   for n, v, k, p in db.execute(query, (*args, *kinds))]
        counts = Counter(r['kind'] for r in records)
        tables = defaultdict(dict)
        keys = {'CURRENT_LIMIT_ENCOUNTER': 'limit_id', 'RECURSIVE_PARTIAL_OUTPUT': 'partial_id',
                'INTEGRATION_COMPLETED': 'integration_id', 'OBSERVATION_FRAME': 'frame_id'}
        for record in records:
            key = keys.get(record['kind'])
            if key:
                tables[record['kind']][record['payload'][key]] = record
        partials, integrations, frames, limits = [tables[k] for k in (
            'RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED', 'OBSERVATION_FRAME', 'CURRENT_LIMIT_ENCOUNTER')]
        recurrences, reentries, changes, binding_limits = [], [], [], []
        for partial in partials.values():
            p = partial['payload']
            if p.get('layer') != 'L0':
                continue  # Historical/debug publications are separate evidence.
            feedback = p.get('consumed_feedback', {})
            prior = integrations.get(feedback.get('integration_id'))
            read = p.get('processing', {})
            if read.get('requested_relation_ref') and read.get('read_succeeded') is False:
                for limit in limits.values():
                    failure = limit['payload']
                    if (failure['code']=='RELATION_CAPACITY_REACHED' and
                        failure['used'] >= failure['capacity'] and failure['requested'] > failure['capacity'] and
                        read['requested_relation_ref'] in failure['object_refs'] and
                        limit['state_version'] < partial['state_version']):
                        binding_limits.append({'failed_write': limit, 'later_failed_read': partial,
                            'consequence': 'prior_recursive_result_requested_a_relation_that_capacity_prevented_retaining',
                            'solution_prescribed': False})
            if prior and prior['state_version'] < partial['state_version'] and read.get('requested_relation_ref') == feedback.get('next_relation_ref') and read.get('requested_relation_ref'):
                saved = json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=?', (prior['state_version'],)).fetchone()[0])
                recorded = saved['internal_state'].get('l0_state', {}).get('feedback', {})
                if recorded == feedback and prior['payload']['input_partial_ids'] == [feedback.get('partial_id')]:
                    recurrences.append({'previous_integration': prior, 'later_partial': partial,
                        'processing_dependency': 'previous_recursive_result_selects_later_relation_read',
                        'mechanism_source': 'EXTERNAL_FIXED_MECHANISM',
                        'data_source': 'INTERNAL_VARIABLE_STRUCTURE', 'organization_changed': False})
            frame = frames.get(p['experience']['frame_id'])
            observed = {x['limit_id'] for x in frame['payload'].get('internal_observations', [])} if frame else set()
            for limit_id in read.get('consumed_limit_ids', []):
                limit = limits.get(limit_id)
                if limit and limit['state_version'] < partial['state_version'] and limit_id in observed:
                    # Require the raw consequence inside the actual partial input, not just an ID in telemetry.
                    inputs = {x['limit_id']: x for x in p['experience'].get('limit_consequences', [])}
                    if inputs.get(limit_id) == limit['payload']:
                        reentries.append({'limit': limit, 'later_partial': partial, 'observation': frame,
                            'effect': 'recursive_input_processing',
                            'effect_source': 'EXTERNAL_FIXED_MECHANISM', 'adaptive_strategy_formed': False})
        for record in records:
            if record['kind'] == 'INTERNAL_VARIABLE_STRUCTURE_CHANGE':
                p = record['payload']
                integration = integrations.get(p.get('integration_id'))
                if integration and p.get('before_hash') != p.get('after_hash') and p.get('after_hash') == integration['payload'].get('model_after_hash'):
                    saved = json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=?', (record['state_version'],)).fetchone()[0])
                    if digest(saved['internal_state']['relations']) == p.get('after_hash'):
                        changes.append(record)
        candidates, rejected = [], []
        for record in records:
            if record['kind'] != 'ARCHITECTURE_HYPOTHESIS_PROPOSED':
                continue
            proposal = record['payload']
            producer = partials.get(proposal.get('producer_partial_id'))
            representation = producer['payload'].get('derived_problem_representation') if producer else None
            refs = proposal.get('evidence_limit_ids', [])
            valid = (proposal.get('source') == 'INTERNAL_VARIABLE_STRUCTURE' and representation == proposal.get('problem_representation')
                     and isinstance(representation, dict) and representation.get('target_kind') == 'current_organization'
                     and len(set(refs)) >= 2 and all(ref in limits for ref in refs)
                     and proposal.get('evaluation', {}).get('external_policy_excluded') is True)
            (candidates if valid else rejected).append(record)
        classifications = {'WITHIN_LAYER_RECURSION': bool(recurrences),
            'CURRENT_LIMIT_ENCOUNTER': bool(limits),
            'LIMIT_FEEDBACK_REENTERED_RECURSION': bool(reentries),
            'ARCHITECTURE_LIMIT_RECOGNITION_CANDIDATE': bool(candidates),
            'EXTERNAL_POLICY_EFFECT': counts['EXTERNAL_POLICY_EFFECT'] > 0,
            'INTERNAL_VARIABLE_STRUCTURE_CHANGE': bool(changes)}
        repeated = Counter(p['payload']['process_id'] for p in partials.values() if p['payload'].get('layer') == 'L0')
        result.update(histories)
        result.update({'profile': 'formal_l0', 'audit_scope': 'session' if session_id else 'lifetime',
            'session_id': session_id, 'classifications': classifications, 'checks': classifications,
            'closed_loop_observed': bool(recurrences),
            'formal_stage_goal_observed': bool(recurrences and binding_limits and reentries and candidates),
            'active_recursive_layers': ['L0'], 'upward_recursion_observed': False, 'upward_recursion_count': 0,
            'revision_meaning': 'ordinary_state_evidence_revision_not_layer_count',
            'counts': dict(counts), 'processes_with_repeated_publications': sum(n >= 2 for n in repeated.values()),
            'feedback_generations': [], 'within_layer_witnesses': recurrences[:3], 'limit_reentry_witnesses': reentries[:3],
            'recognition_candidates': candidates, 'rejected_recognition_claims': rejected,
            'behaviorally_binding_limit_observed': bool(binding_limits),
            'binding_limit_witnesses': binding_limits[:3],
            'recognition_status': 'candidate_requires_independent_review' if candidates else 'not_observed',
            'recognition_capability_boundary': 'Current numeric interpreter does not generate organization-level problem proposals. Raw failure/association alone is insufficient.',
            'external_policy_effects': [r for r in records if r['kind']=='EXTERNAL_POLICY_EFFECT'][:3],
            'organization_change_observed': False, 'real_minecraft_verified_by_this_tool': False,
            'note': 'Evidence insertion and information integration do not establish architecture change or upward recursion.'})
        if include_sample:
            result['actual_event_sample'] = {'within_layer': recurrences[:1], 'limit_reentry': reentries[:1]}
        return result


