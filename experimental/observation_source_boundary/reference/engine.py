"""Versioned endpoint adaptation inside the ordinary FormalL0 hooks.

No frozen engine is edited. Pair construction and exact observed transition /
endpoint composition follow TC/Binding semantics; addresses replace eager body
Units. Declared slot owner/domain incidence has external interface provenance.
"""
from copy import deepcopy
from ..store import repository
import math

from individual.internal_state import InternalState
from individual.observation import ObservationFrame
from individual.change_detection import detect_changes
from individual.structure import pattern_id
from individual.formal_l0 import digest
from experimental.formall0_operative.engine import TestOnlyFormalL0Engine
from experimental.native_body_operands.engine import sensor_source, typed_inputs, unit_identity
from experimental.operative_content.engine import identity, ContentCapacityError
from .references import KEY, VERSION, observed_catalog, validate_catalog, resolve, body_ref, observation_ref


def unit_ref(unit):
    return {'type': 'UnitRef', 'unit': unit}


def value_ref(value, internal):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Nonfinite observed endpoint')
    return observation_ref(internal, unit_identity({'type': 'ObservedValue',
        'value_type': 'integer' if type(value) is int else 'number', 'value': value}))


def connection(source, target):
    return {'type': 'DirectedConnection', 'source': deepcopy(source), 'target': deepcopy(target)}


def compatible(internal, source, target):
    a, b = resolve(internal, source), resolve(internal, target)
    if not isinstance(a, dict) or a.get('type') != 'ParameterSlot':
        return
    schema = resolve(internal, a['domain'])['schema']
    if isinstance(b, dict) and b.get('type') == 'ObservedValue':
        v = b['value']
        if (schema.get('type') not in ('integer', 'number') or type(v) not in (int, float)
                or not math.isfinite(v) or schema['type'] == 'integer' and type(v) is not int
                or not schema.get('minimum', -math.inf) <= v <= schema.get('maximum', math.inf)):
            raise ValueError('Binding violates exact declared slot domain')
    elif isinstance(b, dict) and b.get('type') == 'ObservedReference':
        if schema.get('type') != 'string':
            raise ValueError('Reference binding violates slot type')
    else:
        raise ValueError('Binding target is not an observed value/reference')


def validate(internal):
    pool = internal.l0_state.get(KEY)
    if (not isinstance(pool, dict) or set(pool) != {'version', 'catalog', 'current_source', 'sources', 'observations', 'edges', 'evidence', 'nodes', 'node_evidence'}
            or pool['version'] != VERSION
            or any(not isinstance(pool[k], dict) for k in ('sources', 'edges', 'evidence', 'nodes', 'node_evidence'))):
        raise ValueError('Invalid body-reference collection/version')
    validate_catalog(pool['catalog'])
    if (pool['catalog'] is None) != (pool['current_source'] is None):
        raise ValueError('Missing current interface provenance')
    if pool['current_source'] is not None:
        source = pool['current_source']
        typed_inputs(source)
        check_frame = ObservationFrame(source['frame_id'], 0, 'audit', source['namespace'], source['body_epoch'],
            {}, {}, {'body': {'action_space': source['declarations']}}, source['numeric_channels'], {})
        observed = observed_catalog(check_frame)
        # Catalog reference generation survives a new transport sampling epoch.
        # Native identities are catalog/code identities, not frame-local tokens.
        observed['body_epoch'] = pool['catalog']['body_epoch']
        if observed != pool['catalog']:
            raise ValueError('Interface declaration provenance mismatch')
    if set(pool['nodes']) != set(pool['node_evidence']):
        raise ValueError('Content support coverage mismatch')
    if len(internal.units) + len(pool['nodes']) > internal.l0_state['locked_caps']['units']:
        raise ContentCapacityError('Actual Unit/content structures exceed locked capacity')
    if (len(internal.relations) + len(internal.l0_state['operative_test_only']['edges'])
            + len(pool['edges']) > internal.l0_state['locked_caps']['relations']):
        raise ContentCapacityError('Actual operative connections exceed relation capacity')
    repository().boundary(pool['observations'])
    if pool['current_source'] is not None and repository().get(pool['current_source']['frame_id']) != pool['current_source']:
        raise ValueError('Current observation is not registered')
    for parent, frame_id in pool['sources'].items():
        if parent not in internal.units:
            raise ValueError('Missing ordinary observation incidence endpoint')
        source = repository().get(frame_id)
        if source['namespace'] != pool['catalog']['namespace']:
            raise ValueError('Missing observation incidence provenance')
    if any(u.get('operand_kind') == 'REFERENCE_SENSOR' for u in internal.units.values()):
        raise ValueError('External observation facts must not masquerade as Units')
    if set(pool['edges']) != set(pool['evidence']):
        raise ValueError('Connection support coverage mismatch')
    for ref, edge in pool['edges'].items():
        if (not isinstance(edge, dict) or set(edge) != {'type', 'source', 'target'}
                or edge['type'] != 'DirectedConnection' or ref != digest(edge)):
            raise ValueError('Invalid canonical connection')
        compatible(internal, edge['source'], edge['target'])
        resolve(internal, edge['source']); resolve(internal, edge['target'])
    checked = set()
    def visit(ref, stack=frozenset()):
        if ref in stack or ref not in pool['nodes']:
            raise ValueError('Cyclic or missing content reference')
        if ref in checked:
            return
        node = pool['nodes'][ref]
        if identity(node) != ref:
            raise ValueError('Content identity mismatch')
        if node.get('type') == 'Pair' and set(node) == {'type', 'left', 'right'}:
            visit(node['left'], stack | {ref}); visit(node['right'], stack | {ref})
        else:
            resolve(internal, node)
        checked.add(ref)
    for ref in pool['nodes']:
        visit(ref)
    return pool


def evaluate(internal, ref):
    pool = validate(internal)
    def value(key):
        node = pool['nodes'][key]
        if node['type'] == 'Pair':
            return {'type': 'PairValue', 'left': value(node['left']), 'right': value(node['right'])}
        return {'type': 'OperandValue', 'pattern': resolve(internal, node)}
    return value(ref)


def receipt_assignments(internal, frame):
    """Validate exact supplied incidence even when this tick has no integration."""
    pool = internal.l0_state[KEY]
    receipts = frame.nearby_data.get('typed_execution_receipts', [])
    if not isinstance(receipts, list):
        raise ValueError('Invalid receipt list')
    current_values = typed_inputs(sensor_source(frame))
    ids, result = set(), []
    for receipt in receipts:
        if (not isinstance(receipt, dict) or set(receipt) != {'execution_id', 'catalog_version', 'code', 'status', 'assignments', 'source'}
                or type(receipt['execution_id']) is not str or not receipt['execution_id']
                or receipt['execution_id'] in ids or receipt['source'] != 'EXTERNAL_SYNTHETIC_TYPED_RECEIPT'
                or receipt['status'] != 'executed' or type(receipt['code']) is not int
                or type(receipt['catalog_version']) is not int or receipt['catalog_version'] != pool['catalog']['version']
                or not isinstance(receipt['assignments'], list)):
            raise ValueError('Invalid external receipt premise')
        ids.add(receipt['execution_id'])
        slots = set()
        body_ref(pool['catalog'], 'port', receipt['code'])
        for assignment in receipt['assignments']:
            if not isinstance(assignment, dict) or set(assignment) != {'slot_ref', 'operand_ref'}:
                raise ValueError('Invalid receipt incidence')
            a, b = assignment['slot_ref'], assignment['operand_ref']
            resolve(internal, a); resolve(internal, b)
            if (a.get('type') != 'BodyRef' or a.get('kind') != 'slot'
                    or a['code'] != receipt['code'] or digest(a) in slots):
                raise ValueError('Receipt slot/port mismatch')
            slots.add(digest(a))
            if b.get('type') != 'ObservationRef' or b.get('node') not in current_values:
                raise ValueError('Receipt operand is not current observed material')
            compatible(internal, a, b)
            result.append((a, b, deepcopy(receipt)))
    return result


class ReferenceEngine(TestOnlyFormalL0Engine):
    def __init__(self, caps=None, resource_caps=None):
        super().__init__(caps, resource_caps, test_only_operative_adoption=True)
        self._executing = False

    def advance(self, current, frame, state_version, pending_actions):
        if self._executing:
            raise RuntimeError('Reentrant reference transition')
        working = InternalState.from_dict(current)
        pool = validate(working)
        # Replacing the current interface register does not create a Unit.
        catalog = observed_catalog(frame)
        if pool['catalog'] is not None:
            catalog['body_epoch'] = pool['catalog']['body_epoch']
        pool['catalog'] = catalog
        previous = working.l0_state.get('previous_frame')
        before = ObservationFrame(**previous) if previous else None
        parent = pattern_id(detect_changes(before, frame).to_dict())
        source = sensor_source(frame)
        pool['current_source'] = source
        repository().stage(source, {'timestamp': frame.timestamp,
            'sequence_id': frame.sequence_id, 'source_digest': digest(source)})
        pool['observations'] = repository().descriptor()
        if parent not in pool['sources']:
            typed_inputs(source)  # Validate all facts; instantiate no sensor Units.
            if len(working.units.keys() | {parent}) + len(pool['nodes']) > self.caps.units:
                raise ContentCapacityError('Actual observation Unit/content exceeds locked capacity')
            pool['sources'][parent] = source['frame_id']
        # All existing body addresses must also be legal in this current scope.
        for edge in pool['edges'].values():
            resolve(working, edge['source']); resolve(working, edge['target'])
        receipt_assignments(working, frame)
        self._executing = True
        self._frame = frame
        try:
            result = super().advance(working.to_dict(), frame, state_version, pending_actions)
            validate(result[0])
            return result
        finally:
            self._executing = False
            self._frame = None

    def _read_operative_operands(self, internal, reference):
        result, read = super()._read_operative_operands(internal, reference)
        pool = validate(internal)
        if not self._executing:
            return result, read
        reached = set(result['outcomes'])
        sources = [repository().get(f) for parent, f in pool['sources'].items() if parent in reached]
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
        # The same ordinary Pair(existing content, current UnitRef) operation as
        # ContentEngine: saved structure is a real later construction operand.
        def leaf_addresses(ref):
            node = pool['nodes'][ref]
            if node['type'] != 'Pair':
                return [node]
            return leaf_addresses(node['left']) + leaf_addresses(node['right'])
        def structurally_supported(ref):
            if ref in products:
                return True  # Exact Pair of a currently executed connection/incidence.
            node = pool['nodes'][ref]
            return (node['type'] == 'Pair' and structurally_supported(node['left'])
                    and pool['nodes'][node['right']]['type'] == 'UnitRef'
                    and accessible(pool['nodes'][node['right']]))
        reused = {ref for ref, node in pool['nodes'].items()
                  if node['type'] == 'Pair' and structurally_supported(ref)
                  and all(accessible(a) for a in leaf_addresses(ref))}
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
            'reused_content': sorted(reused), 'new_nodes': sorted(set(staged) - prior)}
        read['typed_connections'] = list(used)
        for ref in products:
            result['outcomes'][ref] = {'unit_id': ref, 'content_ref': ref}
        validate(internal)
        return result, read

    def _form_operative_dependencies(self, internal, read, experience, partial,
                                    integration, state_version, failure):
        pool = validate(internal)
        if integration['experience_ids'] != [experience['experience_id']]:
            raise ValueError('Missing actual integration')
        proposals = {}
        def propose(a, b, support):
            resolve(internal, a); resolve(internal, b); compatible(internal, a, b)
            edge = connection(a, b)
            proposals.setdefault(digest(edge), (edge, support))
        for fact in internal.detected_changes['changes']:
            if fact['before'] is not None and fact['after'] is not None:
                propose(value_ref(fact['before'], internal), value_ref(fact['after'], internal),
                        {'kind': 'EXACT_OBSERVED_TRANSITION', 'change_fact': deepcopy(fact),
                         'frame_ids': deepcopy(experience['frame_ids'])})
        for a, b, receipt in receipt_assignments(internal, self._frame):
            propose(a, b, {'kind': 'RECORDED_EXTERNAL_INCIDENCE', 'receipt': receipt})
        snapshot = {**pool['edges'], **{r: e for r, (e, _) in proposals.items()}}
        by_source = {}
        for ref, edge in snapshot.items():
            by_source.setdefault(digest(edge['source']), []).append((ref, edge))
        # Same exact endpoint composition; all results retained, never selected.
        for left_ref, left in snapshot.items():
            a, b = resolve(internal, left['source']), resolve(internal, left['target'])
            if not isinstance(a, dict) or a.get('type') != 'ParameterSlot' or b.get('type') != 'ObservedValue':
                continue
            for right_ref, right in by_source.get(digest(left['target']), []):
                if left['target'] == right['source'] and resolve(internal, right['target']).get('type') == 'ObservedValue':
                    propose(left['source'], right['target'], {'kind': 'EXACT_ENDPOINT_COMPOSITION',
                                                           'direct_connections': [left_ref, right_ref]})
        super()._form_operative_dependencies(internal, read, experience, partial,
                                             integration, state_version, failure)
        used = len(internal.relations) + len(internal.l0_state['operative_test_only']['edges'])
        if used + len(pool['edges'].keys() | proposals.keys()) > self.caps.relations:
            raise ContentCapacityError('Whole reference formation exceeds relation capacity')
        for ref, (edge, support) in proposals.items():
            if ref not in pool['edges']:
                pool['edges'][ref] = edge
                pool['evidence'][ref] = {'provenance': 'EXPERIENCE_INTEGRATED',
                    'state_version': state_version, 'experience_id': experience['experience_id'],
                    'integration_id': integration['integration_id'], 'supports': support}
        validate(internal)
