"""Policy inventory and provenance. Fixed-rule updates never imply internal authorship."""

from copy import deepcopy
from datetime import datetime, timezone
import math
from uuid import uuid4


CATEGORIES = frozenset({'CORE_MECHANISM', 'ENVIRONMENT_CONSTRAINT',
                        'INITIAL_EXTERNAL_POLICY', 'INTERNAL_VARIABLE_POLICY'})

# These are experiment initialization data. Runtime decisions read the copies in AState.
CATALOG = {
    'formal.process_initialization': ('INITIAL_EXTERNAL_POLICY', {'initial_quantity': 1, 'dynamic_branching': False}, 'formal_l0.py: one process; no automatic quantity changes'),
    'formal.action_sampling': ('INITIAL_EXTERNAL_POLICY', {'method': 'uniform_available_capability',
        'multiplier': 1664525, 'increment': 1013904223, 'modulus': 4294967296}, 'formal_l0.py: explicit initial sampler, no novelty/unresolved scoring'),
    'core.identity': ('CORE_MECHANISM', {}, 'identity.py / events.py: one experiment marker and state chain'),
    'core.scheduler': ('CORE_MECHANISM', {}, 'core.py: observe/action/observe; external pause and shutdown'),
    'core.events': ('CORE_MECHANISM', {}, 'events.py: atomic append-only storage'),
    'body.bridge': ('CORE_MECHANISM', {}, 'bridge.py / server.js: body RPC and transport'),
    'body.lifecycle': ('CORE_MECHANISM', {}, 'body.js: reconnect and respawn without individual replacement'),
    'body.actions': ('CORE_MECHANISM', {'action_codes': [0, 1, 2], 'duration_ms': 120}, 'actions.py: existing action codecs'),
    'sensor.encoding': ('CORE_MECHANISM', {}, 'observation.py: protocol/numeric sensor encoding'),
    'sensor.difference': ('CORE_MECHANISM', {}, 'change_detection.py: numeric comparison'),
    'structure.encoding': ('CORE_MECHANISM', {}, 'structure.py: hash channel/direction pattern and temporal roots'),
    'recursion.interpreter': ('CORE_MECHANISM', {}, 'recursion.py: question lifecycle and partial publication'),
    'integration.evidence': ('CORE_MECHANISM', {}, 'integration.py: count distinct experiences and retain outcomes'),
    'environment.capacity': ('ENVIRONMENT_CONSTRAINT', {}, 'internal_state.py: externally allocated working capacity'),
    'environment.sensor': ('ENVIRONMENT_CONSTRAINT', {}, 'observation coverage: sampling limits supplied by body'),
    'environment.resources': ('ENVIRONMENT_CONSTRAINT', {}, 'Supervisor: measured pressure and external limits'),
    'environment.supervisor': ('ENVIRONMENT_CONSTRAINT', {}, 'Supervisor: experimenter pause/termination authority'),
    'environment.action_interface': ('ENVIRONMENT_CONSTRAINT', {'available_codes': [0, 1, 2]}, 'current experimental body action interface'),
    'action.scoring': ('INITIAL_EXTERNAL_POLICY', {
        'base_score': 1.0, 'unresolved_weight': 1.0, 'attempt_offset': 1.0,
        'attempt_exponent': 1.0, 'temporary_score': 0.0}, 'actions.py: prefer less-tested/unresolved associations'),
    'action.selection': ('INITIAL_EXTERNAL_POLICY', {
        'method': 'max_score_lcg_tie', 'multiplier': 1664525, 'increment': 1013904223,
        'modulus': 4294967296, 'attempt_capacity': 192}, 'actions.py: fixed scoring selection and tie procedure'),
    'action.parameter_binding': ('INITIAL_EXTERNAL_POLICY', {
        'method': 'numeric_domain_lcg', 'look_deltas': [-0.15, 0.0, 0.15],
        'use_durations_ms': [120, 2000], 'amount_cap': 128},
        'action_space.py: explicit fixed numeric/ref sampling; no semantic or learned choice'),
    'generation.quantity': ('INITIAL_EXTERNAL_POLICY', {
        'initial_quantity': 2, 'minimum_quantity': 1, 'counterexample_floor': 3,
        'counterexample_increment': 1, 'consolidated_quantity': 1}, 'integration.py: initial and revised branching influence'),
    'generation.resolution': ('INITIAL_EXTERNAL_POLICY', {
        'initial_resolution': 1.0, 'counterexample_divisor': 2.0,
        'minimum_resolution': 0.00001}, 'integration.py: fixed resolution adjustment'),
    'generation.stability': ('INITIAL_EXTERNAL_POLICY', {
        'initial_evidence_threshold': 3, 'single_outcome_required': True,
        'initial_unresolved': True}, 'integration.py: provisional stability and process completion'),
    'recursion.gating': ('INITIAL_EXTERNAL_POLICY', {
        'reuse_existing_process': True, 'skip_settled_without_new_outcome': True}, 'recursion.py: when to generate'),
    'recursion.channels': ('INITIAL_EXTERNAL_POLICY', {
        'ordering': 'numeric_id', 'candidate_first': True}, 'recursion.py: question channel ordering'),
    'recursion.allocation': ('INITIAL_EXTERNAL_POLICY', {
        'pressure_threshold': 0.8, 'pressure_divisor': 2,
        'eviction': 'oldest_information'}, 'recursion.py: how to use external allocation'),
    'recursion.retirement': ('INITIAL_EXTERNAL_POLICY', {
        'initial_stagnation_window': 6, 'supersede_on_counterexample': True,
        'terminate_when_stable': True}, 'recursion.py / integration.py: provisional lifecycle decisions'),
    'recursion.merge': ('INITIAL_EXTERNAL_POLICY', {
        'signature': ['input_pattern', 'context_channel', 'resolution']}, 'integration.py: identical-question merge'),
    'structure.strength': ('INITIAL_EXTERNAL_POLICY', {
        'increment': 1.0, 'decay': 0.98}, 'structure.py: strength update'),
    'structure.archival': ('INITIAL_EXTERNAL_POLICY', {
        'method': 'oldest_sequence'}, 'structure.py / integration.py: select working records for archival'),
    'memory.window': ('INITIAL_EXTERNAL_POLICY', {
        'initial_history_window': 6}, 'structure.py: retained working window'),
    'debug.smoke': ('INITIAL_EXTERNAL_POLICY', {'enabled_by_default': False}, 'explicit --smoke-policy: deterministic debug task'),
    'experiment.verification': ('INITIAL_EXTERNAL_POLICY', {'enabled_by_default': False}, 'external --verify-loop stopping criterion; never an A goal'),
}


GENERATION_OWNERS = {
    'default_quantity': 'generation.quantity', 'pattern_quantities': 'generation.quantity',
    'condition_resolution': 'generation.resolution',
    'evidence_before_consolidation': 'generation.stability',
    'stagnation_window': 'recursion.retirement', 'history_window': 'memory.window',
}


def initial_generation_parameters():
    return {'default_quantity': CATALOG['generation.quantity'][1]['initial_quantity'],
            'pattern_quantities': {},
            'condition_resolution': CATALOG['generation.resolution'][1]['initial_resolution'],
            'evidence_before_consolidation': CATALOG['generation.stability'][1]['initial_evidence_threshold'],
            'stagnation_window': CATALOG['recursion.retirement'][1]['initial_stagnation_window'],
            'history_window': CATALOG['memory.window'][1]['initial_history_window']}


class PolicyRegistry:
    """A view over the policy data owned by one InternalState, never a global policy singleton."""

    def __init__(self, internal):
        self.internal = internal

    def initialize(self, legacy=False):
        if self.internal.policy_registry:
            return
        created_at = 'legacy_tracking_start' if legacy else 'experiment_start'
        for policy_id, (category, parameters, location) in CATALOG.items():
            self.internal.policy_registry[policy_id] = {
                'policy_id': policy_id, 'category': category, 'parameters': deepcopy(parameters),
                'created_at': created_at, 'implementation': location, 'revision': 0}
            self.internal.policy_migration_status[policy_id] = {
                'current_source': category, 'modification_count': 0, 'migration_count': 0,
                'last_reason': None, 'provenance': None,
                'status': 'legacy_history_untracked' if legacy else 'initialized',
                'historical_origin_verified': not legacy}
            for key, value in parameters.items():
                self.internal.parameter_sources[f'{policy_id}.{key}'] = self._metadata(
                    policy_id, value, created_at, legacy)
        for key, value in self.internal.generation_parameters.items():
            if key == 'pattern_quantities':
                for root, quantity in value.items():
                    self.internal.parameter_sources[f'generation_parameters.pattern_quantities.{root}'] = self._metadata(
                        GENERATION_OWNERS[key], quantity, created_at, legacy)
            else:
                self.internal.parameter_sources[f'generation_parameters.{key}'] = self._metadata(
                    GENERATION_OWNERS[key], value, created_at, legacy)

    def bind_experiment(self, individual_id, started_at):
        for record in self.internal.policy_registry.values():
            record['created_at'] = started_at
            record['individual_id'] = individual_id
        for source in self.internal.parameter_sources.values():
            source['created_at'] = started_at

    def _metadata(self, policy_id, value, created_at, legacy=False):
        return {'policy_id': policy_id, 'source': self.internal.policy_registry[policy_id]['category'],
                'created_at': created_at, 'modified_by': None, 'modification_count': 0,
                'value': deepcopy(value), 'value_origin': 'legacy_untracked' if legacy else 'initialization',
                'provenance': None}

    def parameters(self, policy_id):
        return self.internal.policy_registry[policy_id]['parameters']

    def reference(self, policy_id):
        record = self.internal.policy_registry[policy_id]
        return {'policy_id': policy_id, 'category': record['category'], 'revision': record['revision']}

    def parameter_reference(self, parameter, actual_value, policy_id):
        source = self.internal.parameter_sources.get(parameter)
        if source is None or source['value'] != actual_value:
            return {'parameter': parameter, 'value': deepcopy(actual_value), 'policy_id': policy_id,
                    'source': self.internal.policy_registry[policy_id]['category'],
                    'value_origin': 'untracked_state_assignment', 'modified_by': None}
        return {'parameter': parameter, **deepcopy(source)}

    def parameter_references(self, policy_id):
        return {key: self.parameter_reference(f'{policy_id}.{key}', value, policy_id)
                for key, value in self.parameters(policy_id).items()}

    def record_generation_changes(self, before, state_version, integration_id, experience_ids,
                                  partial_ids, reasons, journal):
        """Attribute the existing fixed formulas honestly, including their historical triggers."""
        after = self.internal.generation_parameters
        for key, owner in GENERATION_OWNERS.items():
            if key == 'pattern_quantities':
                old, new = before[key], after[key]
                changes = [(f'generation_parameters.{key}.{root}', old.get(root), new.get(root))
                           for root in sorted(old.keys() | new.keys()) if old.get(root) != new.get(root)]
            else:
                changes = [(f'generation_parameters.{key}', before[key], after[key])] if before[key] != after[key] else []
            for path, previous, current in changes:
                change_id = str(uuid4())
                old_meta = self.internal.parameter_sources.get(path)
                count = (old_meta or {}).get('modification_count', 0) + 1
                provenance = {'integration_id': integration_id, 'experience_ids': list(experience_ids),
                              'input_partial_ids': list(partial_ids), 'source_state_version': state_version,
                              'updater': self.reference(owner), 'trigger_reasons': deepcopy(reasons)}
                metadata = {'policy_id': owner, 'source': self.internal.policy_registry[owner]['category'],
                    'created_at': old_meta['created_at'] if old_meta else self.internal.policy_registry[owner]['created_at'],
                    'modified_by': integration_id, 'modification_count': count, 'value': deepcopy(current),
                    'value_origin': 'experience_triggered_external_policy',
                    'provenance': provenance, 'change_id': change_id}
                self.internal.parameter_sources[path] = metadata
                status = self.internal.policy_migration_status[owner]
                status['modification_count'] += 1
                status['last_reason'] = deepcopy(reasons)
                status['provenance'] = {'change_id': change_id, **deepcopy(provenance)}
                status['status'] = 'external_rule_changed_parameter'
                journal.append(('POLICY_PARAMETER_UPDATED', {'change_id': change_id, 'parameter': path,
                    'before': deepcopy(previous), 'after': deepcopy(current), 'metadata': deepcopy(metadata),
                    'policy_migration_status': deepcopy(status)}))
                if current is None:
                    self.internal.parameter_sources.pop(path, None)

    def validate_internal_proposal(self, proposal):
        """Preparation only: no auto-promotion, activation, RPC, or new learning procedure."""
        policy_id = proposal.get('policy_id')
        if policy_id not in self.internal.policy_registry:
            raise ValueError('Unknown policy')
        if self.internal.policy_registry[policy_id]['category'] in ('CORE_MECHANISM', 'ENVIRONMENT_CONSTRAINT'):
            raise ValueError('Internal proposals cannot rewrite core or environment boundaries')
        provenance = proposal.get('provenance', {})
        if provenance.get('producer_category') != 'INTERNAL_VARIABLE_POLICY':
            raise ValueError('An initial fixed-rule update is not an internal policy proposal')
        if not all(provenance.get(key) for key in ('process_id', 'partial_ids', 'experience_ids', 'evaluation_id')):
            raise ValueError('Internal policy proposal needs production and evaluation evidence')
        # A future integrator must also resolve these references in real history before adoption.
        # Merely presenting strings must never change the current source or activate a policy.
        return {'eligible_for_future_review': True, 'activated': False,
                'history_references_verified': False, 'proposal': deepcopy(proposal)}

    def summary(self):
        statuses = self.internal.policy_migration_status
        return {'registered': len(self.internal.policy_registry),
                'formal_enabled_initial_policies': [key for key, value in self.internal.policy_registry.items()
                    if value['category']=='INITIAL_EXTERNAL_POLICY' and value.get('formal_path_enabled') is True],
                'formal_disabled_initial_policies': [key for key, value in self.internal.policy_registry.items()
                    if value['category']=='INITIAL_EXTERNAL_POLICY' and value.get('formal_path_enabled') is False],
                'initial_external_policies': sum(r['category'] == 'INITIAL_EXTERNAL_POLICY'
                    for r in self.internal.policy_registry.values()),
                'internal_variable_policies': sum(r['category'] == 'INTERNAL_VARIABLE_POLICY'
                    for r in self.internal.policy_registry.values()),
                'parameter_modifications': sum(s['modification_count'] for s in statuses.values()),
                'source_migrations': sum(s['migration_count'] for s in statuses.values()),
                'untracked_parameters': [key for key, value in self.internal.generation_parameters.items()
                    if key != 'pattern_quantities' and self.parameter_reference(
                        f'generation_parameters.{key}', value, GENERATION_OWNERS[key])['value_origin'] == 'untracked_state_assignment']}


def positive_number(value, label, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (
        value < 0 if allow_zero else value <= 0):
        raise ValueError(f'Invalid policy parameter: {label}')
    return value
