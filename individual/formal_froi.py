"""FROI-1 formal interpreter profile; frozen original FormalL0 stays byte-identical.

The base advance orchestration is retained here with the relation-read source
replaced by the formed-organization interface. No sampler or binder is defined.
"""
from copy import deepcopy
from dataclasses import asdict
from uuid import uuid4

from .change_detection import detect_changes
from .internal_state import InternalState
from .observation import ObservationFrame
from .policies import CATALOG, PolicyRegistry
from .structure import pattern_id
from .formal_boundary import boundary_for, validate_boundary
from .limit_consequences import PORT_IDS, OP_IDS, raw_consequence, auditor_metadata


from .formal_l0 import FormalL0Engine, digest


class FormalFROIEngine(FormalL0Engine):
    def __init__(self, caps=None, resource_caps=None, froi_caps=None):
        super().__init__(caps, resource_caps)
        from integration.froi import load_caps
        self.froi_caps = froi_caps if froi_caps is not None else load_caps()

    def advance(self, current, frame, state_version, pending_actions, *, organization=None):
        checkpoint = self.prepare_read_checkpoint(current, frame, state_version, pending_actions,
                                                  organization=organization)
        result = organization.read(checkpoint.frame, checkpoint.feedback, state_version) if checkpoint.requires_read else (None, None, {})
        return self.resume_from_read_checkpoint(checkpoint, *result)

    def advance_steps(self, current, frame, state_version, pending_actions, *, organization=None):
        """Compatibility adapter only; all post-read logic is in resume()."""
        checkpoint = self.prepare_read_checkpoint(current, frame, state_version, pending_actions,
                                                  organization=organization)
        result = (yield (checkpoint.frame, checkpoint.feedback, state_version)) if checkpoint.requires_read else (None, None, {})
        return self.resume_from_read_checkpoint(checkpoint, *result)

    def _failure(self, frame, state_version, journal, new_limits):
        def failure(code, resource, operation, used, capacity, requested, refs=(), metadata=None):
            record = {'limit_id': str(uuid4()), 'resource_port_id': PORT_IDS[resource],
                      'operation_id': OP_IDS[operation], 'used': used, 'capacity': capacity,
                      'requested': requested, 'operation_performed': False,
                      'source_state_version': state_version, 'frame_id': frame.frame_id,
                      'object_refs': list(refs)}
            record = raw_consequence(record)
            new_limits.append(record)
            journal.append(('CURRENT_LIMIT_ENCOUNTER', {
                'limit_id': record['limit_id'], 'a_facing_payload': deepcopy(record),
                'auditor_metadata': metadata if metadata is not None else auditor_metadata(code, resource, operation)}))
            return record

        return failure

    def prepare_read_checkpoint(self, current, frame, state_version, pending_actions, *, organization=None):
        """Run the prefix once; capture all continuation-live values as immutable JSON."""
        from integration.read_checkpoint import ReadCheckpoint
        frame = deepcopy(frame)
        experience, feedback, root, action_code = None, {}, None, None
        validate_boundary(current, self.caps, self.resource_caps)
        internal = InternalState.from_dict(current) if current else InternalState()
        local = internal.l0_state
        local.update(boundary_for(current, self.caps, self.resource_caps))
        journal, new_limits = [], []

        if organization is None:
            raise ValueError('FROI requires formed-organization reads; no legacy fallback')
        if organization.caps != self.froi_caps:
            raise ValueError('Organization session capacities differ from this interpreter')
        if organization is not None:
            from integration.froi import VERSION
            boundary = {'version': VERSION, 'caps': asdict(organization.caps)}
            if local.get('froi_boundary') not in (None, boundary):
                raise ValueError('FROI capacities cannot change during a lifetime')
            if local.get('froi_boundary') is None:
                local['froi_boundary'] = boundary
                journal.append(('FROI_INITIAL_CONDITION', {'boundary': boundary,
                    'raw_history_retained': True, 'source': 'EXTERNAL_FIXED_MECHANISM',
                    'universal_memory_axiom': False}))
            if organization.test_only:
                local['froi_detached_test_only'] = True

        failure = self._failure(frame, state_version, journal, new_limits)

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
        elif previous and delta['sample_gap']:
            journal.append(('TEMPORAL_LINK_UNRESOLVED', {'frame_ids': [previous.frame_id, frame.frame_id],
                'reason': 'carrier_epoch_or_encoding_changed', 'action_ids': delta['after_action_ids']}))
            if pid:
                internal.active_processes[pid]['status'] = 'PAUSED'
            # Never turn a world/body sampling gap into a consecutive-world experience.


        return ReadCheckpoint.capture(self, organization, internal, frame, state_version,
            journal, experience, feedback, prior_limits, new_limits, retained_frame,
            delta, unit_id, pid, root, action_code)

    def resume_from_read_checkpoint(self, checkpoint, handle, read, diagnostics, *, detached=False):
        """The sole post-read interpreter for live and TEST_ONLY consumers."""
        checkpoint.verify_engine(self)
        checkpoint.verify_handle(handle)
        saved = checkpoint.payload
        internal = InternalState.from_dict(saved['internal'])
        local = internal.l0_state
        frame = ObservationFrame(**saved['frame'])
        state_version = saved['state_version']
        journal = [(kind, payload) for kind, payload in saved['journal']]
        new_limits, prior_limits = saved['new_limits'], saved['prior_limits']
        retained_frame, delta = saved['retained_frame'], saved['delta']
        unit_id, pid = saved['unit_id'], saved['pid']
        experience, feedback = saved['experience'], saved['feedback']
        root, action_code = saved['root'], saved['action_code']
        reference = feedback.get('next_relation_ref')
        test_only = detached or saved['test_only']
        if test_only:
            local['froi_detached_test_only'] = True
        failure = self._failure(frame, state_version, journal, new_limits)
        if experience is not None:
            process = internal.active_processes[pid]
            organization_read = None
            if reference:
                organization_read = {'status': read.status,
                    'organization_status': handle.status if handle else 'INVALID',
                    'closure_complete': bool(handle and handle.complete),
                    'consumed_keys': read.consumed_keys, 'direct_supports': read.supports,
                    'root_witnesses': read.roots, 'conflicts': read.conflicts,
                    'diagnostics': diagnostics, 'test_only': test_only}
                journal.append(('FROI_ORGANIZATION_FORMED', handle.audit() if handle else {
                    'status': 'INVALID', 'closure_complete': False, 'diagnostic': diagnostics}))
                journal.append(('FROI_ORGANIZATION_CONSUMED', deepcopy(organization_read)))
                read_relation = {'outcomes': read.outcomes} if read.succeeded else None
                expected = list(read.outcomes)
                if not read.succeeded:
                    failure('FROI_' + read.status, 'organization_memory', 'read_organization',
                        len(handle.graph) if handle else 0, self.froi_caps.structures, 1, [reference],
                        metadata={'semantic_code': 'FROI_' + read.status,
                            'classification': 'TEST_ONLY_INTERVENTION' if test_only else 'READ_OPERATION_UNAVAILABLE',
                            'source': 'TEST_ONLY' if test_only else 'EXTERNAL_FIXED_MECHANISM',
                            'organization_status': handle.status if handle else 'INVALID',
                            'physical_capacity_exhaustion_claimed': bool(handle and handle.status == 'RESOURCE_LIMIT')})
                    frame.internal_observations = prior_limits + deepcopy(new_limits)
                    experience['limit_consequences'] = deepcopy(frame.internal_observations)
            else:
                # No real reference: no manufactured query, value or read failure.
                read_relation, expected = None, []
            journal.append(('EXPERIENCE_FORMED', deepcopy(experience)))
            process['attempts'] += 1
            partial = {'partial_id': str(uuid4()), 'process_id': pid, 'layer': 'L0',
                'publication_number': process['attempts'], 'experience': deepcopy(experience),
                'question': deepcopy(process['question']), 'consumed_feedback': feedback,
                'processing': {'requested_relation_ref': reference, 'read_succeeded': read_relation is not None,
                    'expected_outcomes': expected, 'same_context_as_prediction': reference == root,
                    'outcome_previously_observed': unit_id in expected if reference == root else None,
                    'consumed_limit_ids': [x['limit_id'] for x in frame.internal_observations]},
                'provisional': True, 'source': 'EXTERNAL_FIXED_MECHANISM'}
            partial['processing']['organization_read'] = organization_read
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
            if relation is None:
                if len(internal.relations) >= self.caps.relations:
                    failure('RELATION_CAPACITY_REACHED', 'relation_memory', 'insert_relation',
                            len(internal.relations), self.caps.relations, len(internal.relations) + 1, [root])
                else:
                    relation = {'relation_id': root, 'antecedent': experience['antecedent'],
                        'action_code': action_code, 'outcomes': {}, 'evidence_count': 0,
                        'last_sequence': frame.sequence_id, 'evidence_refs': []}
                    internal.relations[root] = relation
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
                'state_version': state_version, 'next_relation_ref': root,
                'expected_outcomes': list(relation['outcomes']) if relation else [],
                'model_after_hash': result['model_after_hash'],
                'observed_limit_ids': partial['processing']['consumed_limit_ids']}
            internal.latest_feedback = deepcopy(local['feedback'])
            journal.append(('RECURSIVE_FEEDBACK_STORED', deepcopy(local['feedback'])))
        # Failures created during integration become the NEXT input, not a solved problem.
        local['pending_consequences'] = deepcopy(new_limits)
        local['previous_frame'] = {**retained_frame, 'self_channels': {}, 'spatial_data': {}, 'nearby_data': {}}
        local['previous_unit'] = unit_id
        frame.internal_observations = prior_limits + deepcopy(new_limits)
        internal.structure_revision += 1
        internal.latest_structure_changes = {'new': [], 'removed': [], 'merged': []}
        journal.append(('OBSERVATION_FRAME', frame.to_dict()))
        journal.append(('CHANGE_DETECTED', delta))
        if checkpoint.requires_read:
            from integration.read_checkpoint import AUDIT_EVENT
            artifact = checkpoint.artifact(handle)
            artifact['test_only'] = test_only
            journal.append((AUDIT_EVENT, artifact))
        return internal, frame, journal
