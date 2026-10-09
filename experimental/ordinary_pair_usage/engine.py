"""Isolated ordinary read correction; original ReferenceEngine remains unchanged.

Construction hook copied from observation_interface_references/reference/engine.py.
Only the historical Pair reuse predicate changes. Same base traversal, direct
connection construction, identity, capacity and pre-publication semantics.
"""
from copy import deepcopy
from individual.formal_l0 import digest
from experimental.formall0_operative.engine import TestOnlyFormalL0Engine
from experimental.native_body_operands.engine import typed_inputs
from experimental.operative_content.engine import identity, ContentCapacityError
from experimental.observation_interface_references.reference.engine import ReferenceEngine, validate, unit_ref
from experimental.observation_interface_references.reference.references import resolve
from experimental.observation_interface_references.real.adapter import RealEffectEngine

VERSION = 'ORDINARY-PAIR-USAGE-TEST_ONLY-1'
MODE = 'ordinary_pair_usage_test_only'

class UsageReferenceEngine(ReferenceEngine):
    def _read_operative_operands(self, internal, reference):
        result, read = TestOnlyFormalL0Engine._read_operative_operands(self, internal, reference)
        pool = validate(internal)
        if not self._executing:
            return result, read
        reached = set(result['outcomes'])
        sources = [s for parent, s in pool['sources'].items() if parent in reached]
        accessible_values = {r for s in sources for r, n in typed_inputs(s).items()
                             if n['type'] in ('ObservedValue', 'ObservedReference')}
        def accessible(ref):
            resolve(internal, ref)
            if ref['type'] == 'UnitRef':
                return ref['unit'] in reached
            if ref['type'] == 'ObservationRef':
                return ref['node'] in accessible_values
            if ref['type'] == 'ObservationFactRef':
                return any(s['frame_id'] == ref['frame_id'] for s in sources)
            # Exact declared membership, not eager enumeration/construction.
            return any(s['namespace'] == ref['namespace']
                       and ref['code'] in {e['code'] for e in s['declarations']} for s in sources)
        staged = deepcopy(pool['nodes'])
        products, used, supports = set(), [], {}
        def pair(a, b, support):
            refs = []
            for node in (a, b):
                ref = identity(node); staged[ref] = deepcopy(node); refs.append(ref)
                supports.setdefault(ref, {'operand': deepcopy(node)})
            node = {'type': 'Pair', 'left': refs[0], 'right': refs[1]}
            ref = identity(node); staged[ref] = node; products.add(ref)
            supports.setdefault(ref, support)
        for ref, edge in pool['edges'].items():
            a, b = edge['source'], edge['target']
            if not accessible(a) or not accessible(b):
                continue
            pair(a, b, {'connection_ref': ref})
            used.append(ref)
            operand = resolve(internal, a)
            if isinstance(operand, dict) and operand.get('type') == 'ParameterSlot':
                # Declared structural incidence, not a candidate value generator.
                for role in ('port', 'domain'):
                    pair(a, operand[role], {'declared_incidence': role,
                                           'catalog_id': pool['catalog']['id']})
        # Explicit executed operands, not historical reachability or audit labels.
        reused = set()
        for key, record in result['outcomes'].items():
            if 'content_ref' not in record:
                continue
            ref = record['content_ref']
            if key != ref or record.get('unit_id') != ref or ref not in pool['nodes']:
                raise ValueError('Missing or inconsistent executed content operand')
            if pool['nodes'][ref]['type'] != 'Pair':
                raise ValueError('Executed content constructor requires a Pair operand')
            reused.add(ref)
        current = unit_ref(internal.l0_state['current_pattern'])
        current_ref = identity(current)
        if reused:
            staged[current_ref] = current
            supports[current_ref] = {'operand': current}
        for left in reused:
            node = {'type': 'Pair', 'left': left, 'right': current_ref}
            ref = identity(node); staged[ref] = node; products.add(ref)
            supports[ref] = {'content_operand': left, 'current_unit': current['unit']}
        if len(staged) + len(internal.units) > self.caps.units:
            raise ContentCapacityError('Whole reference Pair batch exceeds locked capacity')
        prior = set(pool['nodes'])
        pool['nodes'] = staged
        for ref in set(staged) - prior:
            pool['node_evidence'][ref] = {'source': 'ORDINARY_REFERENCE_CONSTRUCTION',
                'direct_supports': supports[ref], 'read_dependencies': deepcopy(read['dependencies'])}
        internal.l0_state['body_reference_execution'] = {
            'connections': used, 'constructed': sorted(products),
            'reused_content': sorted(reused), 'new_nodes': sorted(set(staged) - prior),
            'pair_usage_rule': VERSION}
        read['typed_connections'] = list(used)
        for ref in products:
            result['outcomes'][ref] = {'unit_id': ref, 'content_ref': ref}
        validate(internal)
        return result, read


class UsageRealEngine(RealEffectEngine, UsageReferenceEngine):
    def advance(self, current, frame, state_version, pending_actions):
        if (current or {}).get('l0_state', {}).get(MODE) != {'version': VERSION}:
            raise ValueError('Explicit ordinary Pair usage version required')
        return super().advance(current, frame, state_version, pending_actions)
