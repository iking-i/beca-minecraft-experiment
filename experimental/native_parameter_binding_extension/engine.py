"""Ordinary integration of typed experience incidence; no output selector."""
from copy import deepcopy
import math

from individual.formal_l0 import digest
from individual.internal_state import InternalState
from experimental.native_body_operands.engine import unit_identity
from experimental.typed_operative_connection.engine import (
    ConnectionEngine, KEY as GRAPH, connection, validate_connections,
)
from experimental.operative_content.engine import ContentCapacityError

VERSION = 'NATIVE-PARAMETER-CONNECTION-TEST_ONLY-1'
REGISTER = 'typed_receipt_input_test_only'


def compatible(internal, slot_ref, value_ref):
    """Check supplied exact endpoints; never find or fill a compatible endpoint."""
    slot = internal.units[slot_ref]['pattern']
    value = internal.units[value_ref]['pattern']
    if slot.get('type') != 'ParameterSlot':
        raise ValueError('Receipt endpoint is not a declared slot')
    domain = internal.units.get(slot['domain'], {}).get('pattern', {})
    schema = domain.get('schema', {})
    if value.get('type') == 'ObservedValue':
        v = value['value']
        if (schema.get('type') not in ('integer', 'number') or type(v) not in (int, float)
                or not math.isfinite(v) or (schema['type'] == 'integer' and type(v) is not int)
                or v < schema.get('minimum', -math.inf) or v > schema.get('maximum', math.inf)):
            raise ValueError('Supplied binding value violates declared domain')
    elif value.get('type') == 'ObservedReference':
        if schema.get('type') != 'string':
            raise ValueError('Reference supplied for non-reference slot')
    else:
        raise ValueError('Unsupported binding operand')


def validate_bindings(internal):
    graph = validate_connections(internal)
    for edge in graph['edges'].values():
        source = internal.units[edge['source']]['pattern']
        if isinstance(source, dict) and source.get('type') == 'ParameterSlot':
            compatible(internal, edge['source'], edge['target'])
    return graph


def validate_receipts(internal, frame, receipts):
    if not isinstance(receipts, list):
        raise ValueError('Receipt input must be a list')
    ids = set()
    for r in receipts:
        if (not isinstance(r, dict) or set(r) != {'execution_id', 'catalog_version', 'code', 'status', 'assignments', 'source'}
                or type(r['execution_id']) is not str or not r['execution_id'] or r['execution_id'] in ids
                or r['source'] != 'EXTERNAL_SYNTHETIC_TYPED_RECEIPT'
                or r['status'] != 'executed' or not isinstance(r['assignments'], list)):
            raise ValueError('Invalid synthetic execution receipt')
        ids.add(r['execution_id'])
        slots = set()
        port = unit_identity({'type': 'NativePort', 'catalog_version': r['catalog_version'], 'code': r['code']})
        if type(r['code']) is not int or type(r['catalog_version']) is not int or port not in internal.units:
            raise ValueError('Receipt native port not admitted')
        for a in r['assignments']:
            if (not isinstance(a, dict) or set(a) != {'slot_ref', 'operand_ref'}
                    or any(type(a[k]) is not str or a[k] not in internal.units for k in a)
                    or a['slot_ref'] in slots):
                raise ValueError('Invalid or duplicate receipt incidence')
            slots.add(a['slot_ref'])
            slot = internal.units[a['slot_ref']]['pattern']
            if not isinstance(slot, dict) or slot.get('port') != port:
                raise ValueError('Receipt slot belongs to another port')
            compatible(internal, a['slot_ref'], a['operand_ref'])
            value = internal.units[a['operand_ref']]['pattern']
            if value['type'] == 'ObservedReference':
                current = {x.get('target_ref') for family in ('blocks', 'entities')
                           for x in frame.nearby_data.get(family, [])}
                if (value['token'] not in current or value['namespace'] != frame.encoding_namespace
                        or value['body_epoch'] != frame.body_epoch):
                    raise ValueError('Receipt reference is stale or unobserved')


class BindingEngine(ConnectionEngine):
    def advance(self, current, frame, state_version, pending_actions):
        working = InternalState.from_dict(current)
        validate_bindings(working)
        # Supplemental typed incidence is a current input, not an operative answer.
        receipts = deepcopy(frame.nearby_data.get('typed_execution_receipts', []))
        # NativeEngine admits declared input before the ordinary integration hook.
        working.l0_state[REGISTER] = receipts
        result = super().advance(working.to_dict(), frame, state_version, pending_actions)
        validate_receipts(result[0], frame, receipts)
        validate_bindings(result[0])
        return result

    def _form_operative_dependencies(self, internal, read, experience, partial,
                                    integration, state_version, failure):
        receipts = internal.l0_state[REGISTER]
        # The formation hook runs only inside the original experience/integration.
        # frame is the actual current input; caller does not supply an output edge.
        frame = self._receipt_frame
        validate_receipts(internal, frame, receipts)
        super()._form_operative_dependencies(internal, read, experience, partial,
                                             integration, state_version, failure)
        graph = validate_bindings(internal)
        proposals = {}
        for receipt in receipts:
            for incidence in receipt['assignments']:
                edge = connection(incidence['slot_ref'], incidence['operand_ref'])
                proposals[digest(edge)] = (edge, {'kind': 'RECORDED_EXTERNAL_INCIDENCE',
                    'receipt': deepcopy(receipt), 'frame_id': frame.frame_id,
                    'experience_id': experience['experience_id'], 'integration_id': integration['integration_id']})
        snapshot = {**graph['edges'], **{r: e for r, (e, _) in proposals.items()}}
        by_source = {}
        for ref, edge in snapshot.items():
            by_source.setdefault(edge['source'], []).append((ref, edge))
        for left_ref, left in snapshot.items():
            a = internal.units[left['source']]['pattern']
            b = internal.units[left['target']]['pattern']
            if not isinstance(a, dict) or a.get('type') != 'ParameterSlot' or not isinstance(b, dict) or b.get('type') != 'ObservedValue':
                continue
            for right_ref, right in by_source.get(left['target'], []):
                c = internal.units[right['target']]['pattern']
                if not isinstance(c, dict) or c.get('type') != 'ObservedValue':
                    continue
                compatible(internal, left['source'], right['target'])
                edge = connection(left['source'], right['target'])
                ref = digest(edge)
                if ref not in snapshot:
                    support = proposals.setdefault(ref, (edge, {'kind': 'EXACT_ENDPOINT_COMPOSITION',
                        'direct_connections': [], 'experience_id': experience['experience_id'],
                        'integration_id': integration['integration_id']}))[1]
                    support['direct_connections'].append([left_ref, right_ref])
        used = len(internal.relations) + len(internal.l0_state['operative_test_only']['edges']) + len(graph['edges'])
        if used + len(set(proposals) - set(graph['edges'])) > self.caps.relations:
            raise ContentCapacityError('Binding batch exceeds shared relation capacity')
        for ref, (edge, support) in proposals.items():
            if ref not in graph['edges']:
                graph['edges'][ref] = edge
                graph['evidence'][ref] = {'provenance': 'EXPERIENCE_INTEGRATED',
                    'state_version': state_version, 'supports': support}
        validate_bindings(internal)

    def _advance_operative(self, current, frame, state_version, pending_actions):
        self._receipt_frame = frame
        try:
            return super()._advance_operative(current, frame, state_version, pending_actions)
        finally:
            self._receipt_frame = None
