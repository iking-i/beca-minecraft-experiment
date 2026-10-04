"""Numeric observation → descriptive units → ongoing questions → integration."""

from copy import deepcopy
import hashlib
import json
from uuid import uuid4

from .change_detection import detect_changes
from .internal_state import InternalState, PhysicalCaps
from .integration import integrate
from .observation import ObservationFrame
from .recursion import advance_processes, generate_processes, finish_process
from .policies import PolicyRegistry


def pattern_id(delta):
    # Channel identities and direction, never names or Minecraft categories.
    shape = [(item['channel_id'], item['kind']) for item in delta['changes']]
    encoded = json.dumps(shape, separators=(',', ':')).encode()
    return 'U-' + hashlib.sha256(encoded).hexdigest()[:20]


class StructuralEngine:
    def __init__(self, caps=None):
        self.caps = caps or PhysicalCaps()

    def advance(self, current, frame, state_version, pending_actions):
        internal = InternalState.from_dict(current) if current else InternalState()
        strength_policy = PolicyRegistry(internal).parameters('structure.strength')
        if PolicyRegistry(internal).parameters('structure.archival')['method'] != 'oldest_sequence':
            raise ValueError('Unsupported archival strategy')
        journal = []
        previous_record = internal.observation_history_window[-1] if internal.observation_history_window else None
        previous = ObservationFrame(**previous_record['frame'], self_channels={}, spatial_data={}, nearby_data={}) if previous_record else None
        delta = detect_changes(previous, frame, [a['action_id'] for a in pending_actions]).to_dict()
        frame.delta = delta
        unit_id = pattern_id(delta)
        for key, unit in internal.units.items():
            if key != unit_id:
                unit['strength'] *= strength_policy['decay']
        if unit_id not in internal.units:
            if len(internal.units) >= self.caps.units:
                oldest = min(internal.units, key=lambda key: internal.units[key]['last_sequence'])
                journal.append(('UNIT_ARCHIVED', {'unit': internal.archive_unit(oldest), 'reason': 'physical_working_capacity'}))
            internal.units[unit_id] = {'unit_id': unit_id, 'pattern': [(c['channel_id'], c['kind']) for c in delta['changes']],
                'strength': 0, 'observations': 0, 'first_frame_id': frame.frame_id, 'last_sequence': frame.sequence_id}
            journal.append(('UNIT_CREATED', deepcopy(internal.units[unit_id])))
        unit = internal.units[unit_id]
        unit['strength'] += strength_policy['increment']
        unit['observations'] += 1
        unit['last_sequence'] = frame.sequence_id
        internal.detected_changes = delta
        journal.append(('OBSERVATION_FRAME', frame.to_dict()))
        journal.append(('CHANGE_DETECTED', delta))
        journal.append(('STRUCTURE_POLICY_APPLIED', {'frame_id': frame.frame_id,
            'strength_policy': PolicyRegistry(internal).reference('structure.strength'),
            'strength_parameters': PolicyRegistry(internal).parameter_references('structure.strength'),
            'archival_policy': PolicyRegistry(internal).reference('structure.archival')}))
        if previous_record and not delta['sample_gap']:
            antecedent = previous_record['unit_id']
            action_code = pending_actions[-1].get('action_code', -1) if pending_actions else -1
            experience = {'experience_id': str(uuid4()), 'root': f'{antecedent}:{action_code}',
                'antecedent': antecedent, 'outcome': unit_id, 'action_code': action_code,
                'action_ids': [a['action_id'] for a in pending_actions],
                'action_statuses': [a['status'] for a in pending_actions],
                'action_parameters': [deepcopy(a.get('parameters', {})) for a in pending_actions],
                'action_reason_codes': [a.get('reason_code') for a in pending_actions],
                'frame_ids': [previous.frame_id, frame.frame_id], 'frame_id': frame.frame_id,
                'sequence_id': frame.sequence_id,
                'context': {key: previous.numeric_channels[key] for key in sorted(previous.numeric_channels, key=int)[:self.caps.condition_channels]},
                'context_source_frame_id': previous.frame_id,
                'context_is_finite_sample': len(previous.numeric_channels) > self.caps.condition_channels,
                'change_id': delta['change_id'], 'causality': 'temporal_association_only'}
            journal.append(('EXPERIENCE_FORMED', experience))
            generate_processes(internal, experience, state_version, self.caps, journal)
            outputs = advance_processes(internal, experience, self.caps, journal)
            result = integrate(internal, outputs, state_version, self.caps, journal)
            # Even a provisionally settled relation must monitor rare counterexamples.
            if not outputs and experience['root'] in internal.relations:
                output = {'partial_id': f'direct:{experience["experience_id"]}', 'process_id': None,
                          'experience': experience, 'provisional': True}
                journal.append(('DIRECT_EVIDENCE_INPUT', output))
                result = integrate(internal, [output], state_version, self.caps, journal)
        elif previous_record:
            journal.append(('TEMPORAL_LINK_UNRESOLVED', {'frame_ids': [previous.frame_id, frame.frame_id],
                            'reason': 'carrier_epoch_or_encoding_changed', 'action_ids': delta['after_action_ids']}))
            for pid in list(internal.active_processes):
                finish_process(internal, pid, 'PAUSED', 'observation_conditions_changed', journal)
        internal.structure_revision += 1
        size = max(1, min(self.caps.history, int(internal.generation_parameters['history_window'])))
        # Keep numeric working data once. Full original frames are permanently in events.
        working_frame = {key: deepcopy(getattr(frame, key)) for key in (
            'frame_id', 'sequence_id', 'timestamp', 'encoding_namespace', 'body_epoch', 'numeric_channels', 'coverage')}
        internal.observation_history_window = (internal.observation_history_window + [{
            'unit_id': unit_id, 'frame': working_frame, 'state_version': state_version}])[-size:]
        internal.action_history_window = (internal.action_history_window + deepcopy(pending_actions))[-size:]
        internal.latest_structure_changes = {
            'frame_id': frame.frame_id,
            'new': [{'kind': kind, 'id': value.get('unit_id')} for kind, value in journal if kind == 'UNIT_CREATED'],
            'removed': [{'kind': kind, 'id': value['unit'].get('unit_id')} for kind, value in journal if kind == 'UNIT_ARCHIVED'],
            'merged': []}
        for kind, value in journal:
            if kind == 'INTEGRATION_COMPLETED':
                for operation in value['operations']:
                    if operation['operation'] == 'add_relation':
                        internal.latest_structure_changes['new'].append(deepcopy(operation))
                    elif operation['operation'] == 'remove_from_working_set':
                        internal.latest_structure_changes['removed'].append(deepcopy(operation))
                    elif operation['operation'] == 'merge':
                        internal.latest_structure_changes['merged'].append(deepcopy(operation))
        return internal, frame, journal
