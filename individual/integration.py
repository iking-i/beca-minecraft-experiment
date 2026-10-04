"""Integrate distinct experiences once; contradictory outcomes stay distinct."""

from copy import deepcopy
from uuid import uuid4

from .recursion import finish_process
from .policies import PolicyRegistry


def integrate(internal, outputs, state_version, caps, journal):
    if not outputs:
        return None
    integration_id = str(uuid4())
    operations = []
    experiences = {}
    for output in outputs:
        experiences.setdefault(output['experience']['experience_id'], output['experience'])
    before = deepcopy(internal.generation_parameters)
    registry = PolicyRegistry(internal)
    quantity_policy = registry.parameters('generation.quantity')
    resolution_policy = registry.parameters('generation.resolution')
    stability_policy = registry.parameters('generation.stability')
    retirement_policy = registry.parameters('recursion.retirement')
    archival_policy = registry.parameters('structure.archival')
    if archival_policy['method'] != 'oldest_sequence':
        raise ValueError('Unsupported archival strategy')
    reasons = []
    for experience in experiences.values():
        root, outcome = experience['root'], experience['outcome']
        existing = internal.relations.get(root)
        if existing and outcome not in existing['outcomes'] and len(existing['outcomes']) >= caps.outcomes_per_relation:
            # Archive the entire relation, never select only its majority outcomes.
            journal.append(('RELATION_ARCHIVED', {'reason': 'physical_outcome_capacity', 'relation': internal.relations.pop(root)}))
            operations.append({'operation': 'remove_from_working_set', 'relation_id': root})
        if root not in internal.relations:
            if len(internal.relations) >= caps.relations:
                oldest = min(internal.relations, key=lambda key: internal.relations[key]['last_sequence'])
                archived = internal.relations.pop(oldest)
                journal.append(('RELATION_ARCHIVED', {'reason': 'physical_working_capacity', 'relation': archived}))
                operations.append({'operation': 'remove_from_working_set', 'relation_id': oldest})
            internal.relations[root] = {'relation_id': root, 'antecedent': experience['antecedent'],
                'action_code': experience['action_code'], 'outcomes': {}, 'evidence_count': 0,
                'unresolved': stability_policy['initial_unresolved'], 'condition_candidates': [], 'last_sequence': 0}
            operations.append({'operation': 'add_relation', 'relation_id': root})
        relation = internal.relations[root]
        # Duplicated publications from parallel questions are not independent evidence.
        if experience['experience_id'] in relation.get('recent_experience_ids', []):
            continue
        previous_outcomes = list(relation['outcomes'])
        is_counterexample = bool(previous_outcomes and outcome not in previous_outcomes)
        if outcome not in relation['outcomes']:
            relation['outcomes'][outcome] = {'unit_id': outcome, 'evidence_count': 0, 'evidence_refs': [],
                                            'first_context': deepcopy(experience['context'])}
        evidence = relation['outcomes'][outcome]
        evidence['evidence_count'] += 1
        evidence['evidence_refs'] = (evidence['evidence_refs'] + [{
            'experience_id': experience['experience_id'], 'frame_ids': experience['frame_ids'],
            'action_ids': experience['action_ids'], 'integration_id': integration_id}])[-caps.evidence_window:]
        relation['evidence_count'] += 1
        relation['last_sequence'] = experience['sequence_id']
        relation['recent_experience_ids'] = (relation.get('recent_experience_ids', []) + [experience['experience_id']])[-caps.evidence_window:]
        conditional = relation.setdefault('conditional_evidence', {})
        seen_conditions = set()
        for output in outputs:
            if output['experience']['experience_id'] != experience['experience_id'] or 'condition' not in output:
                continue
            condition = output['condition']
            key = f"{condition['channel_id']}:{condition['resolution']}:{condition['interval_index']}:{outcome}"
            if key in seen_conditions:
                continue
            seen_conditions.add(key)
            entry = conditional.setdefault(key, {'condition': deepcopy(condition), 'outcome': outcome, 'evidence_count': 0})
            entry['evidence_count'] += 1
            entry['last_partial_id'] = output['partial_id']
            entry['last_frame_id'] = experience['frame_id']
        while len(conditional) > caps.outcomes_per_relation:
            del conditional[next(iter(conditional))]
        operations.append({'operation': 'reinforce', 'relation_id': root, 'outcome': outcome,
                           'evidence_count': evidence['evidence_count']})
        params = internal.generation_parameters
        if is_counterexample:
            reasons.append({'reason': 'previous_relation_received_new_outcome', 'root': root,
                'previous_outcomes': previous_outcomes, 'new_outcome': outcome,
                'previous_evidence_refs': {old: deepcopy(relation['outcomes'][old]['evidence_refs']) for old in previous_outcomes},
                'experience_id': experience['experience_id'], 'rule_source': 'INITIAL_EXTERNAL_POLICY'})
            # Keep every outcome. Conditions are questions, not asserted causal answers.
            candidates = []
            for older in previous_outcomes:
                context = relation['outcomes'][older]['first_context']
                for channel in sorted(set(context) & set(experience['context']), key=int):
                    a, b = context[channel], experience['context'][channel]
                    if a != b:
                        candidates.append({'channel': channel, 'outcomes': [older, outcome],
                            'values': [a, b], 'resolution': params['condition_resolution'], 'provisional': True,
                            'source_experience_id': experience['experience_id']})
            relation['condition_candidates'] = (relation['condition_candidates'] + candidates)[:16]
            params['pattern_quantities'][root] = min(caps.processes, max(quantity_policy['counterexample_floor'],
                params['default_quantity'] + quantity_policy['counterexample_increment']))
            params['default_quantity'] = min(caps.processes, max(quantity_policy['counterexample_floor'], params['default_quantity']))
            params['condition_resolution'] = max(resolution_policy['minimum_resolution'],
                params['condition_resolution'] / resolution_policy['counterexample_divisor'])
            operations.extend([{'operation': name, 'relation_id': root, 'preserved_outcomes': list(relation['outcomes'])}
                               for name in ('weaken', 'split', 'unresolved')])
            journal.append(('COUNTEREXAMPLE_RETAINED', {'relation_id': root, 'experience': experience,
                            'preserved_outcomes': list(relation['outcomes']), 'condition_candidates': candidates[:16]}))
            # Replace coarse questions with higher-resolution ones on the next exposure.
            for pid, process in list(internal.active_processes.items()):
                if process['input_pattern'] == root and retirement_policy['supersede_on_counterexample']:
                    finish_process(internal, pid, 'SUPERSEDED', 'conditional_question_requires_finer_resolution', journal)
        stable = (not stability_policy['single_outcome_required'] or len(relation['outcomes']) == 1) and relation['evidence_count'] >= params['evidence_before_consolidation']
        relation['unresolved'] = not stable
        if stable:
            reasons.append({'reason': 'provisional_stability_threshold_reached', 'root': root,
                'experience_id': experience['experience_id'], 'evidence_count': relation['evidence_count'],
                'threshold': params['evidence_before_consolidation'], 'rule_source': 'INITIAL_EXTERNAL_POLICY'})
            params['pattern_quantities'][root] = quantity_policy['consolidated_quantity']
            params['default_quantity'] = quantity_policy['consolidated_quantity']
            for pid, process in list(internal.active_processes.items()):
                if retirement_policy['terminate_when_stable'] and process['input_pattern'] == root and process['attempts'] >= params['evidence_before_consolidation']:
                    finish_process(internal, pid, 'TERMINATED', 'sufficient_provisional_information', journal)
    # Only semantically identical questions may merge; different context questions stay separate.
    seen = {}
    merge_fields = registry.parameters('recursion.merge')['signature']
    for pid, process in list(internal.active_processes.items()):
        signature = tuple(process[key] if key in process else process['question'].get(key) for key in merge_fields)
        if signature in seen:
            finish_process(internal, pid, 'MERGED', f'equivalent_question:{seen[signature]}', journal)
            operations.append({'operation': 'merge', 'process_ids': [seen[signature], pid]})
        else:
            seen[signature] = pid
    # Policy memory is finite; the complete successive parameter values remain in SQLite.
    params = internal.generation_parameters
    while len(params['pattern_quantities']) > caps.relations:
        del params['pattern_quantities'][next(iter(params['pattern_quantities']))]
    internal.structure_revision += 1
    result = {'integration_id': integration_id, 'state_version': state_version,
              'input_partial_ids': [o['partial_id'] for o in outputs],
              'experience_ids': list(experiences), 'operations': operations,
              'parameters_before': before, 'parameters_after': deepcopy(params),
              'policy_provenance': {policy_id: {'policy': registry.reference(policy_id),
                  'parameters': registry.parameter_references(policy_id)} for policy_id in (
                      'generation.quantity', 'generation.resolution', 'generation.stability',
                      'recursion.retirement', 'recursion.merge', 'structure.archival')},
              'evidence_rule': 'one_experience_once; repetition_is_not_truth; exceptions_retained'}
    internal.latest_integration = result
    journal.append(('INTEGRATION_COMPLETED', result))
    if before != params:
        internal.latest_feedback = {'integration_id': integration_id, 'state_version': state_version,
                                    'parameters_after': deepcopy(params)}
        journal.append(('DOWNWARD_FEEDBACK_UPDATED', {'integration_id': integration_id,
                        'state_version': state_version, 'before': before, 'after': deepcopy(params)}))
        registry.record_generation_changes(before, state_version, integration_id, list(experiences),
            [o['partial_id'] for o in outputs], reasons, journal)
    return result
