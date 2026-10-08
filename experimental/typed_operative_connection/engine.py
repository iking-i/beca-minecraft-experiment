"""Exact observed transitions form operand connections inside ordinary integration."""
from copy import deepcopy
import math

from individual.formal_l0 import digest
from experimental.formall0_operative.engine import TestOnlyFormalL0Engine
from experimental.native_body_operands.engine import (
    NativeEngine, KEY as NATIVE, validate_native, unit_identity,
)
from experimental.operative_content.engine import (
    KEY as CONTENT, identity, validate_content, ContentCapacityError,
)

KEY = 'typed_connection_test_only'
VERSION = 'TYPED-OPERATIVE-CONNECTION-TEST_ONLY-1'


def connection(source, target):
    return {'type': 'DirectedConnection', 'source': source, 'target': target}


def value_ref(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Observed transition requires a finite typed scalar')
    return unit_identity({'type': 'ObservedValue',
                          'value_type': 'integer' if type(value) is int else 'number',
                          'value': value})


def validate_connections(internal):
    graph = internal.l0_state.get(KEY)
    if (not isinstance(graph, dict) or set(graph) != {'version', 'edges', 'evidence'}
            or graph['version'] != VERSION
            or not isinstance(graph['edges'], dict) or not isinstance(graph['evidence'], dict)):
        raise ValueError('Invalid typed connection collection')
    for ref, edge in graph['edges'].items():
        if (not isinstance(edge, dict) or set(edge) != {'type', 'source', 'target'}
                or edge['type'] != 'DirectedConnection' or digest(edge) != ref
                or any(type(edge[p]) is not str or edge[p] not in internal.units
                       for p in ('source', 'target'))):
            raise ValueError('Invalid typed connection identity/endpoint')
    used = (len(internal.relations)
            + len(internal.l0_state['operative_test_only']['edges'])
            + len(graph['edges']))
    if used > internal.l0_state['locked_caps']['relations']:
        raise ContentCapacityError('Connections exceed shared locked relation capacity')
    return graph


class ConnectionEngine(NativeEngine):
    def advance(self, current, frame, state_version, pending_actions):
        from individual.internal_state import InternalState
        validate_connections(InternalState.from_dict(current))
        result = super().advance(current, frame, state_version, pending_actions)
        validate_connections(result[0])
        return result

    def _read_operative_operands(self, internal, reference):
        # Reuse actual interpreter traversal, not NativeEngine's fixed-right constructor.
        result, read = TestOnlyFormalL0Engine._read_operative_operands(self, internal, reference)
        native = validate_native(internal)
        graph = validate_connections(internal)
        if not self._executing:
            return result, read
        reached = set(result['outcomes'])
        admitted = {u for parent in reached for u in native['incidence'].get(parent, [])}
        for unit in admitted:
            result['outcomes'][unit] = {'unit_id': unit}
        units = set(result['outcomes'])
        pool = validate_content(internal)
        staged = deepcopy(pool['nodes'])
        products, used, inputs, product_supports = set(), [], set(), {}
        for ref, edge in sorted(graph['edges'].items()):
            if not {edge['source'], edge['target']} <= units:
                continue
            ends = []
            for endpoint in ('source', 'target'):
                node = {'type': 'UnitRef', 'unit': edge[endpoint]}
                atom = identity(node)
                staged[atom] = node
                ends.append(atom)
                inputs.add(atom)
            node = {'type': 'Pair', 'left': ends[0], 'right': ends[1]}
            product = identity(node)
            staged[product] = node
            products.add(product)
            product_supports[product] = {'connection_refs': [ref],
                                         'unit_refs': [edge['source'], edge['target']]}
            used.append(ref)
        if len(staged) + len(internal.units) > self.caps.units:
            raise ContentCapacityError('Whole connection construction exceeds locked units capacity')
        prior = set(pool['nodes'])
        pool['nodes'] = staged
        for ref in set(staged) - prior:
            pool['evidence'][ref] = {'source': 'ORDINARY_CONNECTION_CONSTRUCTION',
                'direct_supports': (product_supports[ref] if ref in product_supports
                                    else {'unit_refs': [staged[ref]['unit']]}),
                'read_dependencies': deepcopy(read['dependencies'])}
        internal.l0_state['content_execution'] = {
            'input_atoms': sorted(inputs), 'constructed': sorted(products),
            'reused_content': sorted(products & prior), 'new_nodes': sorted(set(staged) - prior)}
        internal.l0_state['typed_connection_execution'] = {'connections': used}
        internal.l0_state['native_operand_execution'] = {
            'reached_units': sorted(reached), 'admitted_native_units': sorted(admitted)}
        read['typed_connections'] = list(used)
        for ref in products:
            result['outcomes'][ref] = {'unit_id': ref, 'content_ref': ref}
        validate_content(internal)
        return result, read

    def _form_operative_dependencies(self, internal, read, experience, partial,
                                    integration, state_version, failure):
        # Formation is after current computation, on actual ordinary integration.
        graph = validate_connections(internal)
        proposals = {}
        if integration['experience_ids'] != [experience['experience_id']]:
            raise ValueError('Connection formation lacks actual integration')
        for fact in internal.detected_changes['changes']:
            before, after = fact['before'], fact['after']
            if before is None or after is None:
                continue  # No observed predecessor/successor, hence no relation to invent.
            source, target = value_ref(before), value_ref(after)
            if source not in internal.units or target not in internal.units:
                raise ValueError('Exact observed transition endpoint is not admitted')
            edge = connection(source, target)
            ref = digest(edge)
            proposal = proposals.setdefault(ref, {'edge': edge, 'facts': []})
            proposal['facts'].append(deepcopy(fact))
        existing = set(graph['edges'])
        # Reserve old and new relation edges together before either formation law publishes.
        old = internal.l0_state['operative_test_only']['edges']
        terminals = set(read['relations']) - {e['source'] for e in old}
        original_new = {(s, experience['root']) for s in terminals if s != experience['root']}
        original_new -= {(e['source'], e['target']) for e in old}
        used = len(internal.relations) + len(old) + len(existing)
        if used + len(original_new) + len(set(proposals) - existing) > self.caps.relations:
            raise ContentCapacityError('Whole formation exceeds shared relation capacity')
        super()._form_operative_dependencies(internal, read, experience, partial,
                                           integration, state_version, failure)
        # Canonical connections accumulate; repeated facts do not reconstruct endpoints.
        for ref, proposal in proposals.items():
            if ref in existing:
                continue
            graph['edges'][ref] = proposal['edge']
            graph['evidence'][ref] = {'provenance': 'EXPERIENCE_FORMED',
                'state_version': state_version, 'supports': {
                    'experience_id': experience['experience_id'],
                    'partial_id': partial['partial_id'], 'integration_id': integration['integration_id'],
                    'frame_ids': deepcopy(experience['frame_ids']),
                    'change_id': internal.detected_changes['change_id'],
                    'change_facts': proposal['facts']}}
        validate_connections(internal)
