"""Two disjoint views of physical operation consequences. Labels never enter raw input."""

from copy import deepcopy

# These opaque port/op addresses are fixed independently of human audit labels.
PORT_IDS = {'active_memory_units': 101, 'observation_history': 102, 'process_slots': 103,
            'condition_channels': 104, 'relation_memory': 105,
            'relation_outcomes': 106, 'evidence_references': 107}
OP_IDS = {'insert_unit': 201, 'retain_frame': 202, 'create_initial_process': 203,
          'read_context': 204, 'read_relation': 205, 'insert_relation': 206,
          'insert_outcome': 207, 'retain_evidence_reference': 208}
RAW_FIELDS = frozenset({'limit_id', 'resource_port_id', 'operation_id', 'used', 'capacity',
                       'requested', 'operation_performed', 'object_refs', 'source_state_version', 'frame_id'})


def raw_consequence(value):
    if set(value) != RAW_FIELDS or value['operation_performed'] is not False:
        raise ValueError('Invalid A-facing consequence: semantic metadata is not an input')
    if not isinstance(value['resource_port_id'], int) or not isinstance(value['operation_id'], int):
        raise ValueError('Consequence ports must be opaque numeric addresses')
    return deepcopy(value)


def auditor_metadata(code, resource, operation):
    return {'semantic_code': code, 'resource_name': resource, 'operation_name': operation,
            'organization_ref': f'L0.{resource}', 'representation_name': 'bounded_keyed_records_v1',
            'classification': 'CURRENT_LIMIT_ENCOUNTER', 'source': 'ENVIRONMENT_CONSTRAINT'}
