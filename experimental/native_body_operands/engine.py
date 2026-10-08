"""Declared typed sensor incidence feeds the existing ordinary Pair semantics."""
from copy import deepcopy
import math

from individual.action_space import CATALOG_DATA, DEFINITIONS
from individual.change_detection import detect_changes
from individual.observation import ObservationFrame
from individual.structure import pattern_id
from individual.formal_l0 import digest
from experimental.formall0_operative.engine import TestOnlyFormalL0Engine
from experimental.operative_content.engine import (
    ContentEngine, ContentCapacityError, identity, leaves, validate_content,
)

KEY = 'native_body_operands_test_only'
VERSION = 'NATIVE-BODY-OPERANDS-TEST_ONLY-1'


def unit_identity(node):
    return 'N-' + digest(node)


def sensor_source(frame):
    body = frame.nearby_data.get('body', {})
    return {'frame_id': frame.frame_id, 'namespace': frame.encoding_namespace,
            'body_epoch': frame.body_epoch,
            'declarations': deepcopy(body.get('action_space', [])),
            'numeric_channels': deepcopy(frame.numeric_channels),
            'references': [{'kind': family, 'token': item['target_ref']}
                for family in ('blocks', 'entities')
                for item in frame.nearby_data.get(family, []) if item.get('target_ref')]}


def typed_inputs(source):
    """All declared/observed materials, not an action recipe or domain sampler."""
    if (set(source) != {'frame_id', 'namespace', 'body_epoch', 'declarations', 'numeric_channels', 'references'}
            or type(source['frame_id']) is not str or not source['frame_id']
            or type(source['namespace']) is not str or type(source['body_epoch']) is not int
            or source['body_epoch'] < 0 or not isinstance(source['declarations'], list)
            or not isinstance(source['numeric_channels'], dict) or not isinstance(source['references'], list)):
        raise ValueError('Invalid native sensor source')
    nodes = {}
    def add(node):
        key = unit_identity(node)
        nodes[key] = node
        return key
    codes = set()
    for entry in source['declarations']:
        code = entry.get('code')
        if type(code) is not int or code not in DEFINITIONS or code in codes:
            raise ValueError('Invalid or duplicate native port')
        codes.add(code)
        definition = DEFINITIONS[code]
        required = sorted(k for k, v in definition['parameters'].items() if not v.get('optional'))
        schema = entry.get('parameter_schema')
        if (entry.get('category') != 'BODY_CAPABILITY'
                or schema != {'type': 'object', 'properties': definition['parameters'],
                              'required': required, 'additionalProperties': False}
                or entry.get('formal_enabled') != (definition.get('formal_enabled') is not False)
                or type(entry.get('currently_available')) is not bool
                or entry.get('environment_requirement_codes') != [CATALOG_DATA['requirement_codes'][r]
                    for r in definition['environment_requirements']]):
            raise ValueError('Observed capability declaration differs from native catalog')
        port = add({'type': 'NativePort', 'catalog_version': CATALOG_DATA['version'], 'code': code})
        for name, declared in definition['parameters'].items():
            domain = add({'type': 'ParameterDomain', 'schema': deepcopy(declared)})
            add({'type': 'ParameterSlot', 'port': port, 'name': name,
                 'domain': domain, 'required': name in required})
    for channel, value in source['numeric_channels'].items():
        if type(channel) is not str or type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Invalid observed scalar')
        add({'type': 'ObservedValue', 'value_type': 'integer' if type(value) is int else 'number',
             'value': value})
    for reference in source['references']:
        token = reference['token']
        if (reference['kind'] not in ('blocks', 'entities') or type(token) is not str
                or not token or len(token) > 128):
            raise ValueError('Invalid observed reference')
        add({'type': 'ObservedReference', 'kind': reference['kind'], 'token': token,
             'namespace': source['namespace'], 'body_epoch': source['body_epoch']})
    return nodes


def validate_native(internal):
    pool = internal.l0_state.get(KEY)
    if (not isinstance(pool, dict) or set(pool) != {'version', 'sources', 'incidence', 'evidence'}
            or pool['version'] != VERSION or any(not isinstance(pool[k], dict)
                for k in ('sources', 'incidence', 'evidence'))):
        raise ValueError('Invalid native operand mode/collection')
    if set(pool['sources']) != set(pool['incidence']) or set(pool['sources']) != set(pool['evidence']):
        raise ValueError('Native source coverage mismatch')
    admitted = {}
    for parent, source in pool['sources'].items():
        if parent not in internal.units or internal.units[parent].get('operand_kind') == 'NATIVE_SENSOR':
            raise ValueError('Missing observation Unit endpoint')
        expected = typed_inputs(source)
        if pool['incidence'][parent] != sorted(expected):
            raise ValueError('Invalid native operand incidence')
        for key, node in expected.items():
            unit = internal.units.get(key)
            if not unit or unit.get('unit_id') != key or unit.get('operand_kind') != 'NATIVE_SENSOR' or unit.get('pattern') != node:
                raise ValueError('Missing or invalid native operand reference')
        admitted.update(expected)
    actual = {k for k, v in internal.units.items() if v.get('operand_kind') == 'NATIVE_SENSOR'}
    if actual != set(admitted):
        raise ValueError('Unsupported native operand')
    validate_content(internal)  # All atoms remain ordinary typed UnitRefs.
    return pool


class NativeEngine(ContentEngine):
    def advance(self, current, frame, state_version, pending_actions):
        from individual.internal_state import InternalState
        working = InternalState.from_dict(current)
        pool = validate_native(working)
        previous = working.l0_state.get('previous_frame')
        before = ObservationFrame(**previous) if previous else None
        parent = pattern_id(detect_changes(before, frame).to_dict())
        # Register the entire first-observed source incidence, before interpretation.
        # Repeated pattern identity follows the frozen Unit's first-creation semantics.
        if parent not in pool['sources']:
            source = sensor_source(frame)
            atoms = typed_inputs(source)
            if len(working.units.keys() | atoms.keys() | {parent}) + len(validate_content(working)['nodes']) > self.caps.units:
                raise ContentCapacityError('Whole native input batch exceeds locked units capacity')
            for key, node in atoms.items():
                working.units.setdefault(key, {'unit_id': key, 'operand_kind': 'NATIVE_SENSOR',
                    'pattern': node, 'observations': 0, 'first_frame_id': frame.frame_id,
                    'last_sequence': frame.sequence_id})
            pool['sources'][parent] = source
            pool['incidence'][parent] = sorted(atoms)
            pool['evidence'][parent] = {'source': 'ENVIRONMENT_SENSOR_INTERFACE', 'frame_id': frame.frame_id}
        result = super().advance(working.to_dict(), frame, state_version, pending_actions)
        validate_native(result[0])
        return result

    def _read_operative_operands(self, internal, reference):
        # Same original traversal, followed by exact declared input incidence.
        result, read = TestOnlyFormalL0Engine._read_operative_operands(self, internal, reference)
        native = validate_native(internal)
        if not self._executing:
            return result, read
        reached = set(result['outcomes'])
        admitted = {key for parent in reached for key in native['incidence'].get(parent, [])}
        for key in admitted:
            result['outcomes'][key] = {'unit_id': key}
        # Constructor block follows frozen ContentEngine's exact Pair operation.
        # Only its admitted Unit set is extended; no action interpretation is added.
        pool = validate_content(internal)
        units = set(result['outcomes'])
        current = internal.l0_state['current_pattern']
        if current not in internal.units or not units <= internal.units.keys():
            raise ValueError('Constructor requires actual typed Unit operands')
        staged, atom_refs = deepcopy(pool['nodes']), set()
        for unit in units | {current}:
            node = {'type': 'UnitRef', 'unit': unit}
            ref = identity(node)
            staged[ref] = node
            if unit in units:
                atom_refs.add(ref)
        reusable = {ref for ref, node in pool['nodes'].items()
                    if node['type'] == 'Pair' and leaves(pool['nodes'], ref) <= units}
        right = identity({'type': 'UnitRef', 'unit': current})
        constructed = set()
        for left in atom_refs | reusable:
            node = {'type': 'Pair', 'left': left, 'right': right}
            ref = identity(node)
            staged[ref] = node
            constructed.add(ref)
        if len(staged) + len(internal.units) > self.caps.units:
            raise ContentCapacityError('Whole native construction batch exceeds locked units capacity')
        prior = set(pool['nodes'])
        pool['nodes'] = staged
        for ref in set(staged) - prior:
            pool['evidence'][ref] = {'source': 'ORDINARY_TYPED_CONSTRUCTION', 'current_unit': current,
                'read_relations': deepcopy(read['relations']), 'read_dependencies': deepcopy(read['dependencies'])}
        internal.l0_state['content_execution'] = {'input_atoms': sorted(atom_refs),
            'reused_content': sorted(reusable), 'constructed': sorted(constructed),
            'new_nodes': sorted(set(staged) - prior)}
        internal.l0_state['native_operand_execution'] = {'reached_units': sorted(reached),
            'admitted_native_units': sorted(admitted)}
        for ref in constructed:
            result['outcomes'][ref] = {'unit_id': ref, 'content_ref': ref}
        validate_native(internal)
        return result, read
