"""Typed construction inside the existing ordinary operative read hook."""
from copy import deepcopy

from experimental.formall0_operative.engine import TestOnlyFormalL0Engine
from individual.formal_l0 import digest

KEY = 'content_test_only'
VERSION = 'GENERIC-OPERATIVE-CONTENT-TEST_ONLY-1'


class ContentCapacityError(ValueError):
    pass


def identity(node):
    return 'T-' + digest(node)


def validate_content(internal):
    pool = internal.l0_state.get(KEY)
    if not isinstance(pool, dict) or set(pool) != {'version', 'nodes', 'evidence'} or pool['version'] != VERSION:
        raise ValueError('Invalid content version/collection')
    nodes = pool['nodes']
    if not isinstance(nodes, dict) or not isinstance(pool['evidence'], dict):
        raise ValueError('Invalid content containers')
    if set(pool['evidence']) != set(nodes):
        raise ValueError('Content evidence coverage mismatch')
    if len(nodes) + len(internal.units) > internal.l0_state['locked_caps']['units']:
        raise ContentCapacityError('Content plus Unit records exceeds locked units capacity')
    checked = set()
    def visit(ref, stack=frozenset()):
        if ref in stack or ref not in nodes:
            raise ValueError('Cyclic or missing content reference')
        if ref in checked:
            return
        node = nodes[ref]
        if not isinstance(node, dict) or identity(node) != ref:
            raise ValueError('Invalid canonical content identity')
        if node.get('type') == 'UnitRef' and set(node) == {'type', 'unit'}:
            if node['unit'] not in internal.units:
                raise ValueError('Missing content UnitRef')
        elif node.get('type') == 'Pair' and set(node) == {'type', 'left', 'right'}:
            visit(node['left'], stack | {ref})
            visit(node['right'], stack | {ref})
        else:
            raise ValueError('Illegal content type/shape')
        checked.add(ref)
    for ref in nodes:
        visit(ref)
    return pool


def leaves(nodes, ref):
    node = nodes[ref]
    if node['type'] == 'UnitRef':
        return {node['unit']}
    return leaves(nodes, node['left']) | leaves(nodes, node['right'])


def evaluate(internal, ref):
    """Mechanical value evaluation for tests/audit; never supplies engine answers."""
    nodes = validate_content(internal)['nodes']
    def value(key):
        node = nodes[key]
        if node['type'] == 'UnitRef':
            return {'type': 'UnitValue', 'pattern': deepcopy(internal.units[node['unit']]['pattern'])}
        return {'type': 'PairValue', 'left': value(node['left']), 'right': value(node['right'])}
    return value(ref)


class ContentEngine(TestOnlyFormalL0Engine):
    def __init__(self, caps=None, resource_caps=None):
        super().__init__(caps, resource_caps, test_only_operative_adoption=True)
        self._executing = False

    def advance(self, current, frame, state_version, pending_actions):
        if self._executing:
            raise RuntimeError('Reentrant content transition')
        self._executing = True
        try:
            # No after-advance attachment. Constructor runs before expected operands.
            return super().advance(current, frame, state_version, pending_actions)
        finally:
            self._executing = False

    def _read_operative_operands(self, internal, reference):
        result, read = super()._read_operative_operands(internal, reference)
        pool = validate_content(internal)
        if not self._executing:
            return result, read  # Admission must be pure and must not construct.
        units = set(result['outcomes'])
        current = internal.l0_state['current_pattern']
        if current not in internal.units or not units <= internal.units.keys():
            raise ValueError('Constructor requires actual typed Unit operands')
        staged = deepcopy(pool['nodes'])
        atom_refs = set()
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
            raise ContentCapacityError('Whole content construction batch exceeds locked units capacity')
        # Only full valid batches are published in the working transition state.
        prior = set(pool['nodes'])
        pool['nodes'] = staged
        for ref in set(staged) - prior:
            pool['evidence'][ref] = {'source': 'ORDINARY_TYPED_CONSTRUCTION',
                'current_unit': current, 'read_relations': deepcopy(read['relations']),
                'read_dependencies': deepcopy(read['dependencies'])}
        internal.l0_state['content_execution'] = {
            'input_atoms': sorted(atom_refs), 'reused_content': sorted(reusable),
            'constructed': sorted(constructed), 'new_nodes': sorted(set(staged) - prior)}
        # The normal interpreter now computes with these real constructed operands.
        for ref in constructed:
            result['outcomes'][ref] = {'unit_id': ref, 'content_ref': ref}
        validate_content(internal)
        return result, read
