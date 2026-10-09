"""Native projection only: no trigger formation, candidate search or selection."""
from copy import deepcopy
import math

from experimental.observation_interface_references.reference.references import resolve


def project(internal, frame, effects):
    arguments, ports, support = {}, {}, {}
    for ref, effect in effects.items():
        if effect['receiver']['type'] != 'BodyRef':
            continue
        slot = resolve(internal, effect['receiver'])
        port = slot['port']
        key = (port['catalog_id'], port['code'])
        ports[key] = port
        schema = resolve(internal, slot['domain'])['schema']
        value = resolve(internal, effect['operand'])
        if value.get('type') == 'ObservedValue':
            scalar = value['value']
        elif value.get('type') == 'ObservedReference':
            scalar = value['token']
        else:
            raise ValueError('No native effect value')
        if (schema['type'] == 'integer' and type(scalar) is not int
                or schema['type'] == 'number' and type(scalar) not in (int, float)
                or schema['type'] == 'string' and (type(scalar) is not str or not 0 < len(scalar) <= 128)
                or type(scalar) in (int, float) and (not math.isfinite(scalar)
                    or scalar < schema.get('minimum', -math.inf)
                    or scalar > schema.get('maximum', math.inf))):
            raise ValueError('Activated operand violates native slot schema')
        parameters = arguments.setdefault(key, {})
        if slot['name'] in parameters and (type(parameters[slot['name']]) is not type(scalar)
                                          or parameters[slot['name']] != scalar):
            return 'CONFLICTING_ACTIVATIONS', []
        parameters[slot['name']] = scalar
        support.setdefault(key, []).append(ref)
    operations = []
    for key, parameters in arguments.items():
        port = ports[key]
        declarations = [d for d in frame.nearby_data['body']['action_space'] if d['code'] == port['code']]
        if len(declarations) != 1 or not declarations[0]['formal_enabled'] or not declarations[0]['currently_available']:
            return 'UNAVAILABLE', []
        schema = declarations[0]['parameter_schema']
        if not set(schema['required']) <= parameters.keys() or not parameters.keys() <= schema['properties'].keys():
            return 'INCOMPLETE', []
        operations.append({'type': 'NativeOperation', 'port': deepcopy(port),
                           'expression': {'code': port['code'], 'parameters': deepcopy(parameters)},
                           'effect_refs': sorted(support[key])})
    if len(operations) > 1:
        # No host-authored execution order for competing physical operations.
        return 'CONCURRENT_PHYSICAL_OPERATIONS', []
    return ('READY' if operations else 'NO_BODY_ACTIVATION'), operations
