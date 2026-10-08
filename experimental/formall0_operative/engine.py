"""Isolated opt-in FormalL0 operative integration, never imported by production.

The enabled transition is the pre-isolation validated FormalL0 transition copied
from base 0cd29715 + the documented operative hooks. No detached executor or
post-advance answer is used. See ISOLATION.md for scope and source comparison.
"""
from copy import deepcopy
from dataclasses import asdict
from uuid import uuid4

from individual.formal_l0 import FormalL0Engine as FrozenFormalL0Engine, FormalLimits, digest
from individual.change_detection import detect_changes
from individual.internal_state import InternalState
from individual.observation import ObservationFrame
from individual.policies import CATALOG, PolicyRegistry
from individual.structure import pattern_id
from individual.formal_boundary import boundary_for, validate_boundary
from individual.limit_consequences import PORT_IDS, OP_IDS, raw_consequence, auditor_metadata


class TestOnlyFormalL0Engine(FrozenFormalL0Engine):
    __test__ = False

    def __init__(self, caps=None, resource_caps=None, *, test_only_operative_adoption=False):
        FrozenFormalL0Engine.__init__(self, caps, resource_caps)
        if type(test_only_operative_adoption) is not bool:
            raise ValueError('TEST_ONLY operative option must be boolean')
        self._test_only_operative_adoption = test_only_operative_adoption

    def advance(self, current, frame, state_version, pending_actions):
        if not self._test_only_operative_adoption:
            if 'operative_test_only' in (current or {}).get('l0_state', {}):
                raise ValueError('TEST_ONLY operative state requires explicit opt-in')
            return FrozenFormalL0Engine.advance(self, current, frame, state_version, pending_actions)
        return self._advance_operative(current, frame, state_version, pending_actions)

    @property
    def caps(self):
        return self._caps

    def _read_operative_operands(self, internal, reference):
        """TEST_ONLY dependency interpretation at the ordinary operand read.

        Only relation references and edges are executable inputs. Audit evidence
        is deliberately not accessed. All reachable records supply the actual
        comparison operands; no separate runtime/consumer supplies an answer.
        """
        graph = internal.l0_state.get('operative_test_only')
        if (not isinstance(graph, dict) or graph.get('schema') != 'FORMALL0-OPERATIVE-TEST_ONLY-1'
                or not isinstance(graph.get('edges'), list)):
            raise ValueError('Missing TEST_ONLY operative state')
        edges = set()
        for edge in graph.get('edges', ()):
            if (not isinstance(edge, dict) or set(edge) != {'source', 'target'}
                    or any(type(edge[k]) is not str or not edge[k] for k in edge)):
                raise ValueError('Malformed operative dependency')
            pair = (edge['source'], edge['target'])
            if any(p not in internal.relations for p in pair) or pair in edges:
                raise ValueError('Missing or duplicate operative endpoint')
            edges.add(pair)
        if reference not in internal.relations:
            raise ValueError('Unresolved TEST_ONLY operative entry; no fallback')
        if len(edges) + len(internal.relations) > self.caps.relations:
            raise ValueError('TEST_ONLY operative state exceeds locked relation capacity')
        queue, reached, dependencies, outcomes = [reference], set(), [], {}
        while queue:
            operand = queue.pop(0)
            if operand in reached:
                continue
            reached.add(operand)
            record = internal.relations[operand]
            if record.get('relation_id') != operand or not isinstance(record.get('outcomes'), dict):
                raise ValueError('Invalid operative relation record')
            for key, value in record['outcomes'].items():
                if value.get('unit_id') != key:
                    raise ValueError('Invalid operative outcome identity')
                outcomes.setdefault(key, value)
            for source, target in sorted(edges):
                if source == operand:
                    dependencies.append({'source': source, 'target': target})
                    queue.append(target)
        return {'outcomes': outcomes}, {'relations': sorted(reached), 'dependencies': dependencies}

    def _form_operative_dependencies(self, internal, read, experience, partial, integration,
                                    state_version, failure):
        """Scoped candidate: executed terminal operands -> newly created relation.

        Called only after actual FormalL0 insertion. The current read is already
        finished; new edges first affect a later ordinary advance.
        """
        graph = internal.l0_state['operative_test_only']
        existing = {(e['source'], e['target']) for e in graph['edges']}
        terminals = set(read['relations']) - {a for a, _ in existing}
        target = experience['root']
        formed = sorted({(source, target) for source in terminals if source != target} - existing)
        used = len(internal.relations) + len(existing)
        if used + len(formed) > self.caps.relations:
            failure('TEST_ONLY_OPERATIVE_CAPACITY', 'relation_memory', 'insert_relation',
                    used, self.caps.relations, used + len(formed), [target])
            return
        for source, target in formed:
            edge = {'source': source, 'target': target}
            graph['edges'].append(edge)
            graph.setdefault('evidence', {})[digest(edge)] = {
                'provenance': 'INTERNALLY_FORMED', 'state_version': state_version,
                'supports': {'experience_id': experience['experience_id'],
                    'partial_id': partial['partial_id'], 'integration_id': integration['integration_id'],
                    'frame_ids': deepcopy(experience['frame_ids']), 'executed_operand': source,
                    'new_relation': target, 'read_dependencies': deepcopy(read['dependencies'])}}

    def _advance_operative(self, current, frame, state_version, pending_actions):
        if not self._test_only_operative_adoption and 'operative_test_only' in (current or {}).get('l0_state', {}):
            raise ValueError('TEST_ONLY operative state requires explicit opt-in')
        validate_boundary(current, self.caps, self.resource_caps)
        internal = InternalState.from_dict(current) if current else InternalState()
        local = internal.l0_state
        local.update(boundary_for(current, self.caps, self.resource_caps))
        journal, new_limits = [], []

        def failure(code, resource, operation, used, capacity, requested, refs=()):
            record = {'limit_id': str(uuid4()), 'resource_port_id': PORT_IDS[resource],
                      'operation_id': OP_IDS[operation], 'used': used, 'capacity': capacity,
                      'requested': requested, 'operation_performed': False,
                      'source_state_version': state_version, 'frame_id': frame.frame_id,
                      'object_refs': list(refs)}
            record = raw_consequence(record)
            new_limits.append(record)
            journal.append(('CURRENT_LIMIT_ENCOUNTER', {
                'limit_id': record['limit_id'], 'a_facing_payload': deepcopy(record),
                'auditor_metadata': auditor_metadata(code, resource, operation)}))
            return record

        if local.get('profile') != 'formal_l0':
            # Preserve legacy history/lineage. Suspend its execution, never erase or repurpose it.
            for process in internal.active_processes.values():
                process['status'] = 'PAUSED'
                journal.append(('RECURSIVE_PROCESS_STATUS', {'process_id': process['process_id'],
                    'status': 'PAUSED', 'reason': 'external_experiment_profile_change',
                    'source': 'EXTERNAL_FIXED_POLICY'}))
            local.update(profile='formal_l0', active_layer='L0', process_id=None,
                         previous_frame=None, previous_unit=None, feedback={}, pending_consequences=[])
            journal.append(('EXPERIMENT_PROFILE_SELECTED', {
                'profile': 'formal_l0', 'active_layers': ['L0'], 'k_actual_initial': 1,
                'k_capacity': self.caps.processes, 'physical_caps': asdict(self.caps),
                'source': 'EXTERNAL_FIXED_POLICY', 'old_history_preserved': True}))
            journal.append(('EXTERNAL_POLICY_EFFECT', {'policy_id': 'formal.process_initialization',
                'source': 'EXTERNAL_FIXED_POLICY', 'effect': 'initial_single_process',
                'quantity': 1, 'dynamic_branching': False, 'profile': 'formal_l0'}))
        registry = PolicyRegistry(internal)
        for key in ('formal.process_initialization', 'formal.action_sampling'):
            if key not in internal.policy_registry:
                category, parameters, location = CATALOG[key]
                internal.policy_registry[key] = {'policy_id': key, 'category': category,
                    'parameters': deepcopy(parameters), 'created_at': f'A{state_version}',
                    'implementation': location, 'revision': 0}
                internal.policy_migration_status[key] = {'current_source': category,
                    'modification_count': 0, 'migration_count': 0, 'last_reason': None,
                    'provenance': None, 'status': 'external_profile_initialization', 'historical_origin_verified': True}
                for parameter, value in parameters.items():
                    internal.parameter_sources[f'{key}.{parameter}'] = {
                        'policy_id': key, 'source': category, 'created_at': f'A{state_version}',
                        'modified_by': None, 'modification_count': 0, 'value': deepcopy(value),
                        'value_origin': 'external_profile_initialization', 'provenance': None}
                journal.append(('POLICY_REGISTERED', deepcopy(internal.policy_registry[key])))
        for entry in internal.policy_registry.values():
            entry['formal_path_enabled'] = entry['category'] != 'INITIAL_EXTERNAL_POLICY'
        for key in ('formal.process_initialization', 'formal.action_sampling', 'action.parameter_binding'):
            if key in internal.policy_registry:
                internal.policy_registry[key]['formal_path_enabled'] = True

        old_frame = local.get('previous_frame')
        previous = ObservationFrame(**old_frame) if old_frame else None
        delta = detect_changes(previous, frame, [a['action_id'] for a in pending_actions]).to_dict()
        frame.delta = delta
        unit_id = pattern_id(delta)
        if unit_id not in internal.units:
            if len(internal.units) < self.caps.units:
                internal.units[unit_id] = {'unit_id': unit_id, 'pattern': deepcopy(delta['changes']),
                    'observations': 0, 'first_frame_id': frame.frame_id, 'last_sequence': frame.sequence_id}
                journal.append(('UNIT_CREATED', deepcopy(internal.units[unit_id])))
            else:
                failure('WRITE_FAILED_CAPACITY', 'active_memory_units', 'insert_unit',
                        len(internal.units), self.caps.units, len(internal.units) + 1, [unit_id])
        if unit_id in internal.units:
            unit = internal.units[unit_id]
            unit['observations'] += 1
            unit['last_sequence'] = frame.sequence_id
        internal.detected_changes = delta
        retained_frame = {key: deepcopy(getattr(frame, key)) for key in (
            'frame_id', 'sequence_id', 'timestamp', 'encoding_namespace', 'body_epoch', 'numeric_channels', 'coverage')}
        record = {'unit_id': unit_id, 'frame': retained_frame, 'state_version': state_version}
        if len(internal.observation_history_window) < self.caps.history:
            internal.observation_history_window.append(record)
        else:
            failure('ACTIVE_MEMORY_LIMIT', 'observation_history', 'retain_frame',
                    len(internal.observation_history_window), self.caps.history,
                    len(internal.observation_history_window) + 1, [frame.frame_id])
        # Two live input registers are explicitly separate from retained episodic memory.
        # They are replaced by incoming signals, never used to evict a retained record.
        local['current_pattern'] = unit_id
        prior_limits = [raw_consequence(value) for value in local.get('pending_consequences', [])]
        frame.internal_observations = prior_limits + deepcopy(new_limits)

        pid = local.get('process_id')
        if pid is None:
            if len(internal.active_processes) >= self.caps.processes:
                failure('PROCESS_SLOT_UNAVAILABLE', 'process_slots', 'create_initial_process',
                        len(internal.active_processes), self.caps.processes,
                        len(internal.active_processes) + 1)
            else:
                pid = str(uuid4())
                local['process_id'] = pid
                process = {'process_id': pid, 'origin_state_version': state_version,
                    'input_pattern': 'L0:observation_stream', 'question': {
                        'kind': 'temporal_relation_evaluation', 'layer': 'L0'},
                    'hypothesis': {}, 'attempts': 0, 'observations': [], 'output': {},
                    'status': 'ACTIVE', 'last_information_sequence': frame.sequence_id,
                    'policy_provenance': {'initialization': registry.reference('formal.process_initialization')}}
                internal.active_processes[pid] = process
                journal.append(('RECURSIVE_PROCESS_CREATED', deepcopy(process)))
                internal.latest_generation = {'generation_id': str(uuid4()), 'root': 'L0:observation_stream',
                    'requested_quantity': 1, 'granted_quantity': 1, 'process_ids': [pid],
                    'physical_capacity': self.caps.processes, 'layer': 'L0',
                    'source': 'EXTERNAL_FIXED_POLICY', 'subsequent_quantity_adjustment': False}
                journal.append(('RECURSION_GENERATED', deepcopy(internal.latest_generation)))

        if previous and not delta['sample_gap'] and pid:
            action_code = pending_actions[-1].get('action_code', -1) if pending_actions else -1
            root = f'{local["previous_unit"]}:{action_code}'
            channels = list(previous.numeric_channels)
            # Fixed sensor serialization order is visible, not a learned question preference.
            context = {key: previous.numeric_channels[key] for key in channels[:self.caps.condition_channels]}
            if len(channels) > self.caps.condition_channels:
                failure('INFORMATION_NOT_SIMULTANEOUSLY_AVAILABLE', 'condition_channels',
                        'read_context', self.caps.condition_channels, self.caps.condition_channels,
                        len(channels), channels[self.caps.condition_channels:])
            frame.internal_observations = prior_limits + deepcopy(new_limits)
            experience = {'experience_id': str(uuid4()), 'root': root,
                'antecedent': local['previous_unit'], 'outcome': unit_id, 'action_code': action_code,
                'action_ids': [a['action_id'] for a in pending_actions],
                'action_statuses': [a['status'] for a in pending_actions],
                'action_parameters': [deepcopy(a.get('parameters', {})) for a in pending_actions],
                'action_reason_codes': [a.get('reason_code') for a in pending_actions],
                'context': context, 'context_is_finite_sample': len(channels) > self.caps.condition_channels,
                'frame_ids': [previous.frame_id, frame.frame_id], 'frame_id': frame.frame_id,
                'sequence_id': frame.sequence_id, 'change_id': delta['change_id'],
                'limit_consequences': deepcopy(frame.internal_observations),
                'causality': 'temporal_association_only', 'layer': 'L0'}
            process = internal.active_processes[pid]
            process['status'] = 'ACTIVE'
            feedback = deepcopy(local.get('feedback', {}))
            reference = feedback.get('next_relation_ref')
            operative_read = None
            if self._test_only_operative_adoption:
                read_relation, operative_read = self._read_operative_operands(internal, reference)
            else:
                read_relation = internal.relations.get(reference) if reference else None
            expected = list(read_relation.get('outcomes', {})) if read_relation else []
            prediction_context = (root in operative_read['relations'] if operative_read is not None
                                  else reference == root)
            if reference and read_relation is None:
                failure('INFORMATION_NOT_SIMULTANEOUSLY_AVAILABLE', 'relation_memory', 'read_relation',
                        len(internal.relations), self.caps.relations, 1, [reference])
                frame.internal_observations = prior_limits + deepcopy(new_limits)
                experience['limit_consequences'] = deepcopy(frame.internal_observations)
            journal.append(('EXPERIENCE_FORMED', deepcopy(experience)))
            process['attempts'] += 1
            partial = {'partial_id': str(uuid4()), 'process_id': pid, 'layer': 'L0',
                'publication_number': process['attempts'], 'experience': deepcopy(experience),
                'question': deepcopy(process['question']), 'consumed_feedback': feedback,
                'processing': {'requested_relation_ref': reference, 'read_succeeded': read_relation is not None,
                    'expected_outcomes': expected, 'same_context_as_prediction': prediction_context,
                    'outcome_previously_observed': unit_id in expected if prediction_context else None,
                    'consumed_limit_ids': [x['limit_id'] for x in frame.internal_observations]},
                'provisional': True, 'source': 'EXTERNAL_FIXED_MECHANISM'}
            if operative_read is not None:
                partial['processing']['operative_dependencies'] = deepcopy(operative_read)
            process['last_information_sequence'] = frame.sequence_id
            process['output'] = {'partial_id': partial['partial_id'], 'publication_number': process['attempts']}
            journal.append(('RECURSIVE_PARTIAL_OUTPUT', deepcopy(partial)))
            if prior_limits:
                journal.append(('LIMIT_FEEDBACK_REENTERED_RECURSION', {
                    'process_id': pid, 'partial_id': partial['partial_id'],
                    'limit_ids': [x['limit_id'] for x in prior_limits], 'frame_id': frame.frame_id, 'layer': 'L0'}))
            # Evidence insertion changes the later read state. Capacity failure gives no fallback.
            before_hash = digest(internal.relations)
            relation = internal.relations.get(root)
            relation_created = False
            if relation is None:
                relation_used = len(internal.relations)
                if operative_read is not None:
                    relation_used += len(local['operative_test_only']['edges'])
                if relation_used >= self.caps.relations:
                    failure('RELATION_CAPACITY_REACHED', 'relation_memory', 'insert_relation',
                            relation_used, self.caps.relations, relation_used + 1, [root])
                else:
                    relation = {'relation_id': root, 'antecedent': experience['antecedent'],
                        'action_code': action_code, 'outcomes': {}, 'evidence_count': 0,
                        'last_sequence': frame.sequence_id, 'evidence_refs': []}
                    internal.relations[root] = relation
                    relation_created = True
            operations = []
            if relation is not None:
                if unit_id not in relation['outcomes'] and len(relation['outcomes']) >= self.caps.outcomes_per_relation:
                    failure('WRITE_FAILED_CAPACITY', 'relation_outcomes', 'insert_outcome',
                            len(relation['outcomes']), self.caps.outcomes_per_relation,
                            len(relation['outcomes']) + 1, [root, unit_id])
                else:
                    outcome = relation['outcomes'].setdefault(unit_id, {'unit_id': unit_id, 'evidence_count': 0, 'evidence_refs': []})
                    outcome['evidence_count'] += 1
                    relation['evidence_count'] += 1
                    relation['last_sequence'] = frame.sequence_id
                    ref = {'experience_id': experience['experience_id'], 'partial_id': partial['partial_id'],
                           'limit_ids': partial['processing']['consumed_limit_ids']}
                    if len(outcome['evidence_refs']) < self.caps.evidence_window:
                        outcome['evidence_refs'].append(ref)
                    else:
                        failure('ACTIVE_MEMORY_LIMIT', 'evidence_references', 'retain_evidence_reference',
                                len(outcome['evidence_refs']), self.caps.evidence_window,
                                len(outcome['evidence_refs']) + 1, [root, unit_id])
                    operations.append({'operation': 'record_distinct_experience', 'relation_id': root, 'outcome': unit_id})
            integration_id = str(uuid4())
            result = {'integration_id': integration_id, 'state_version': state_version, 'layer': 'L0',
                'input_partial_ids': [partial['partial_id']], 'experience_ids': [experience['experience_id']],
                'operations': operations, 'model_before_hash': before_hash,
                'model_after_hash': digest(internal.relations),
                'parameters_before': deepcopy(internal.generation_parameters),
                'parameters_after': deepcopy(internal.generation_parameters),
                'source': 'EXTERNAL_FIXED_MECHANISM', 'organization_changed': False}
            internal.latest_integration = result
            journal.append(('INTEGRATION_COMPLETED', deepcopy(result)))
            if before_hash != result['model_after_hash']:
                journal.append(('INTERNAL_VARIABLE_STRUCTURE_CHANGE', {
                    'integration_id': integration_id, 'experience_ids': result['experience_ids'],
                    'input_partial_ids': result['input_partial_ids'], 'change_kind': 'RELATION_EVIDENCE_UPDATE',
                    'organization_changed': False, 'source': 'INTERNAL_VARIABLE_STRUCTURE',
                    'updater_source': 'EXTERNAL_FIXED_MECHANISM',
                    'before_hash': before_hash, 'after_hash': result['model_after_hash']}))
            local['feedback'] = {'integration_id': integration_id, 'partial_id': partial['partial_id'],
                'state_version': state_version, 'next_relation_ref': reference if operative_read is not None else root,
                'expected_outcomes': list(relation['outcomes']) if relation else [],
                'model_after_hash': result['model_after_hash'],
                'observed_limit_ids': partial['processing']['consumed_limit_ids']}
            internal.latest_feedback = deepcopy(local['feedback'])
            journal.append(('RECURSIVE_FEEDBACK_STORED', deepcopy(local['feedback'])))
            if operative_read is not None and relation_created:
                self._form_operative_dependencies(internal, operative_read, experience, partial,
                                                 result, state_version, failure)
        elif previous and delta['sample_gap']:
            journal.append(('TEMPORAL_LINK_UNRESOLVED', {'frame_ids': [previous.frame_id, frame.frame_id],
                'reason': 'carrier_epoch_or_encoding_changed', 'action_ids': delta['after_action_ids']}))
            if pid:
                internal.active_processes[pid]['status'] = 'PAUSED'
            # Never turn a world/body sampling gap into a consecutive-world experience.

        # Failures created during integration become the NEXT input, not a solved problem.
        local['pending_consequences'] = deepcopy(new_limits)
        local['previous_frame'] = {**retained_frame, 'self_channels': {}, 'spatial_data': {}, 'nearby_data': {}}
        local['previous_unit'] = unit_id
        frame.internal_observations = prior_limits + deepcopy(new_limits)
        internal.structure_revision += 1
        internal.latest_structure_changes = {'new': [], 'removed': [], 'merged': []}
        journal.append(('OBSERVATION_FRAME', frame.to_dict()))
        journal.append(('CHANGE_DETECTED', delta))
        return internal, frame, journal
