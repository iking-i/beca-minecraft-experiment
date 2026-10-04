"""Persistent, numerically framed questions; publications are evidence, not votes."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import math
from uuid import uuid4

from .policies import PolicyRegistry


@dataclass
class RecursiveProcess:
    process_id: str
    origin_state_version: int
    input_pattern: str
    question: dict
    hypothesis: dict = field(default_factory=dict)
    attempts: int = 0
    observations: list = field(default_factory=list)
    output: dict = field(default_factory=dict)
    status: str = 'ACTIVE'
    last_information_sequence: int = 0
    policy_provenance: dict = field(default_factory=dict)

    def publish_partial_result(self, experience, window=4):
        if self.status != 'ACTIVE' or experience['root'] != self.input_pattern:
            return None
        self.attempts += 1
        self.last_information_sequence = experience['sequence_id']
        self.observations = (self.observations + [experience['frame_id']])[-window:]
        counts = self.hypothesis.setdefault('outcomes', {})
        outcome = experience['outcome']
        counts[outcome] = counts.get(outcome, 0) + 1
        channel = self.question.get('context_channel')
        value = experience['context'].get(channel)
        resolution = self.question['resolution']
        condition = {'channel_id': channel, 'observed_value': value, 'resolution': resolution,
                     'interval_index': math.floor(value / resolution) if value is not None else None,
                     'provisional': True}
        bucket = str(condition['interval_index'])
        conditional = self.hypothesis.setdefault('conditional_outcomes', {})
        grouped = conditional.setdefault(bucket, {})
        grouped[outcome] = grouped.get(outcome, 0) + 1
        if len(conditional) > 16:
            del conditional[next(iter(conditional))]
        self.output = {'partial_id': str(uuid4()), 'process_id': self.process_id,
                       'origin_state_version': self.origin_state_version,
                       'publication_number': self.attempts, 'question': deepcopy(self.question),
                       'experience': deepcopy(experience), 'outcome_counts': deepcopy(counts),
                       'condition': condition, 'conditional_outcome_counts': deepcopy(grouped),
                       'policy_provenance': deepcopy(self.policy_provenance),
                       'provisional': True}
        return deepcopy(self.output)

    def to_dict(self):
        return deepcopy(asdict(self))


def finish_process(internal, process_id, status, reason, journal):
    if status not in ('PAUSED', 'MERGED', 'SUPERSEDED', 'TERMINATED'):
        raise ValueError('Invalid lifecycle status')
    process = internal.active_processes[process_id]
    process['status'] = status
    record = {'process_id': process_id, 'status': status, 'reason': reason,
              'attempts': process['attempts'], 'origin_state_version': process['origin_state_version']}
    registry = PolicyRegistry(internal)
    owner = ('recursion.allocation' if reason == 'physical_working_capacity' else
             'recursion.merge' if reason.startswith('equivalent_question:') else
             'environment.supervisor' if reason == 'external_experiment_terminated' else
             'sensor.difference' if reason == 'observation_conditions_changed' else 'recursion.retirement')
    record['policy_provenance'] = {'rule': registry.reference(owner),
        'parameters': registry.parameter_references(owner),
        'stagnation_window': registry.parameter_reference('generation_parameters.stagnation_window',
            internal.generation_parameters['stagnation_window'], 'recursion.retirement')}
    journal.append(('RECURSIVE_PROCESS_STATUS', record))
    if status != 'PAUSED':
        internal.active_processes.pop(process_id)
        internal.process_archive = (internal.process_archive + [record])[-16:]


def generate_processes(internal, experience, state_version, caps, journal):
    root = experience['root']
    registry = PolicyRegistry(internal)
    gating = registry.parameters('recursion.gating')
    for process in internal.active_processes.values():
        if process['input_pattern'] == root and process['status'] == 'PAUSED':
            process['status'] = 'ACTIVE'
            journal.append(('RECURSIVE_PROCESS_STATUS', {'process_id': process['process_id'],
                            'status': 'ACTIVE', 'reason': 'condition_observed_again'}))
    existing = [p for p in internal.active_processes.values() if p['input_pattern'] == root]
    if existing and gating['reuse_existing_process']:
        return
    relation = internal.relations.get(root)
    novel_outcome = relation and experience['outcome'] not in relation['outcomes']
    if relation and not relation.get('unresolved') and not novel_outcome and gating['skip_settled_without_new_outcome']:
        return  # A settled question is not continually restarted.
    params = internal.generation_parameters
    policy_quantity = registry.parameters('generation.quantity')
    selected_parameter = (f'generation_parameters.pattern_quantities.{root}' if root in params['pattern_quantities']
                          else 'generation_parameters.default_quantity')
    state_quantity = params['pattern_quantities'].get(root, params['default_quantity'])
    requested = max(policy_quantity['minimum_quantity'], int(state_quantity))
    pressure = internal.resource_state.get('pressure', 0)
    allocation = registry.parameters('recursion.allocation')
    budget = max(1, caps.processes // allocation['pressure_divisor']) if pressure >= allocation['pressure_threshold'] else caps.processes
    if allocation['eviction'] != 'oldest_information':
        raise ValueError('Unsupported eviction strategy')
    active_before = len(internal.active_processes)
    # Finite physical room; retired evidence remains in the append-only journal.
    while len(internal.active_processes) >= budget:
        oldest = min(internal.active_processes,
                     key=lambda key: internal.active_processes[key]['last_information_sequence'])
        finish_process(internal, oldest, 'TERMINATED', 'physical_working_capacity', journal)
    granted = min(requested, budget - len(internal.active_processes))
    ordering = registry.parameters('recursion.channels')
    if ordering['ordering'] != 'numeric_id':
        raise ValueError('Unsupported channel ordering')
    selectors = sorted(experience['context'], key=int)
    candidates = relation.get('condition_candidates', []) if relation else []
    candidate_channels = [item['channel'] for item in candidates]
    selectors = list(dict.fromkeys((candidate_channels + selectors) if ordering['candidate_first'] else selectors))
    feedback = deepcopy(internal.latest_feedback)
    generation_id = str(uuid4())
    quantity_decision = {
        'resource_limit': {'source': registry.reference('environment.capacity'), 'physical_capacity': caps.processes,
            'pressure': pressure, 'effective_budget': budget, 'active_before': active_before,
            'available_after_eviction': budget - len(internal.active_processes),
            'allocation_policy': registry.reference('recursion.allocation'),
            'allocation_parameters': registry.parameter_references('recursion.allocation'),
            'resource_sample_timestamp': internal.resource_state.get('timestamp')},
        'current_internal_state': {'root': root, 'relation_present': bool(relation),
            'unresolved': relation.get('unresolved') if relation else None, 'novel_outcome': bool(novel_outcome),
            'selected_parameter': registry.parameter_reference(selected_parameter, state_quantity, 'generation.quantity')},
        'initial_policy_influence': {'quantity': registry.reference('generation.quantity'),
            'gating': registry.reference('recursion.gating'), 'minimum_quantity': policy_quantity['minimum_quantity'],
            'parameters': registry.parameter_references('generation.quantity')},
        'requested_quantity': requested, 'granted_quantity': granted}
    policy_provenance = {'generation_id': generation_id, 'quantity_decision': deepcopy(quantity_decision),
        'resolution': registry.parameter_reference('generation_parameters.condition_resolution',
            params['condition_resolution'], 'generation.resolution'),
        'channels': registry.reference('recursion.channels'),
        'channel_parameters': registry.parameter_references('recursion.channels'),
        'source_experience_id': experience['experience_id']}
    ids = []
    for index in range(granted):
        process = RecursiveProcess(str(uuid4()), state_version, root,
                    {'context_channel': selectors[index % len(selectors)] if selectors else None,
                     'resolution': params['condition_resolution'], 'branch_index': index},
                    last_information_sequence=experience['sequence_id'], policy_provenance=deepcopy(policy_provenance))
        internal.active_processes[process.process_id] = process.to_dict()
        ids.append(process.process_id)
        journal.append(('RECURSIVE_PROCESS_CREATED', process.to_dict()))
    generation = {'generation_id': generation_id, 'root': root, 'requested_quantity': requested,
                  'granted_quantity': granted, 'process_ids': ids,
                  'parameters': deepcopy(params), 'physical_capacity': caps.processes,
                  'feedback_integration_id': feedback.get('integration_id'),
                  'feedback_state_version': feedback.get('state_version'),
                  'origin_state_version': state_version,
                  'condition_channels': selectors[:granted],
                  'quantity_decision': quantity_decision, 'policy_provenance': policy_provenance}
    internal.latest_generation = generation
    journal.append(('RECURSION_GENERATED', generation))


def advance_processes(internal, experience, caps, journal):
    outputs = []
    for process_id, value in list(internal.active_processes.items()):
        process = RecursiveProcess(**value)
        partial = process.publish_partial_result(experience, caps.evidence_window)
        if partial:
            outputs.append(partial)
            # The full publication lives in SQLite; working process retains only its link.
            process.output = {key: partial[key] for key in ('partial_id', 'publication_number', 'provisional')}
            internal.active_processes[process_id] = process.to_dict()
            journal.append(('RECURSIVE_PARTIAL_OUTPUT', partial))
        elif experience['sequence_id'] - process.last_information_sequence >= internal.generation_parameters['stagnation_window']:
            finish_process(internal, process_id, 'TERMINATED', 'no_new_information_for_question', journal)
    return outputs
