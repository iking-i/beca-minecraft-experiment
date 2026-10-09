"""Exact real request/receipt incidence, inside existing ordinary integration."""
from copy import deepcopy
from datetime import datetime

from individual.formal_l0 import digest
from individual.observation import FrameEncoder
from experimental.native_body_operands.engine import sensor_source, typed_inputs
from experimental.body_interface_references.engine import connection, compatible, value_ref
from experimental.body_interface_references.references import KEY as REF_KEY, body_ref
from experimental.operative_body_effects.engine import EffectEngine

VERSION = 'NATIVE-RECEIPT-EFFECT-CARRIER-TEST_ONLY-1'
MODE = 'real_receipt_effect_lifecycle'


def canonical_observation(raw):
    """JSON Schema required is a set; normalize wire ordering without loss."""
    result = deepcopy(raw)
    wire = deepcopy(result.get('actionSpace', []))
    changed = False
    for entry in result.get('actionSpace', []):
        schema = entry.get('parameter_schema', {})
        required = schema.get('required')
        if type(required) is not list or any(type(k) is not str for k in required) or len(required) != len(set(required)):
            raise ValueError('Invalid native required-field declaration')
        ordered = sorted(required)
        changed |= ordered != required
        schema['required'] = ordered
    if changed:
        result['nativeDeclarationWireSource'] = wire  # External audit; encoder ignores it.
    return result


class RealEncoder(FrameEncoder):
    def encode(self, raw, sequence, body_epoch=0):
        if raw.get('typedExecutionReceipts'):
            raise ValueError('Synthetic typed receipts forbidden in real carrier')
        frame = super().encode(raw, sequence, body_epoch)
        frame.nearby_data['native_execution_records'] = deepcopy(raw.get('nativeExecutionRecords', []))
        return frame


def assignments(internal, frame, record, experience):
    required = {'action_id', 'source', 'request', 'receipt', 'before_frame_id', 'individual_id'}
    if (set(record) != required or record['source'] not in
            ('NATIVE_BRIDGE_EXECUTION', 'OFFLINE_RECEIPT_ADAPTER_TEST')
            or record['individual_id'] != frame.frame_id.rsplit(':E', 1)[0]
            or record['before_frame_id'] != experience['frame_ids'][0]
            or frame.frame_id != experience['frame_ids'][1]
            or record['action_id'] not in experience['action_ids']):
        raise ValueError('Receipt is not owned by this live experience interval')
    index = experience['action_ids'].index(record['action_id'])
    request, receipt = record['request'], record['receipt']
    if (set(request) != {'code', 'parameters'} or type(request['code']) is not int
            or type(request['parameters']) is not dict or type(receipt) is not dict
            or type(receipt.get('code')) is not int or receipt['code'] != request['code']
            or digest(receipt.get('parameters')) != digest(request['parameters'])
            or experience['action_statuses'][index] != 'executed'
            or experience['action_parameters'][index] != request['parameters']
            or receipt.get('result') != {'input_sent': 1, 'effect_acknowledged': 0}
            or receipt.get('effect_attribution') != 'temporal_observation_only'
            or not isinstance(receipt.get('before'), dict) or not isinstance(receipt.get('after'), dict)):
        raise ValueError('Receipt/request/experience mismatch')
    start, end = (datetime.fromisoformat(receipt[k].replace('Z', '+00:00'))
                  for k in ('started_at', 'finished_at'))
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise ValueError('Invalid native execution interval')
    if datetime.fromisoformat(frame.timestamp.replace('Z', '+00:00')) < end:
        raise ValueError('Observation precedes completed execution')
    pool = internal.l0_state[REF_KEY]
    port = body_ref(pool['catalog'], 'port', request['code'])
    declaration = next(e for e in pool['catalog']['declarations'] if e['code'] == port['code'])
    schema = declaration['parameter_schema']
    if (not declaration['formal_enabled'] or set(request['parameters']) - set(schema['properties'])
            or set(schema['required']) - set(request['parameters'])):
        raise ValueError('Incomplete or foreign native request')
    available = typed_inputs(sensor_source(frame))
    result = []
    for name, value in request['parameters'].items():
        if type(value) in (int, float):
            operand = value_ref(value)
        elif type(value) is str:
            from experimental.body_interface_references.engine import unit_ref
            from experimental.native_body_operands.engine import unit_identity
            matches = [unit_identity(n) for n in available.values()
                       if n['type'] == 'ObservedReference' and n['token'] == value]
            if len(matches) != 1:
                raise ValueError('Missing or ambiguous current observed reference')
            operand = unit_ref(matches[0])
        else:
            raise ValueError('Unsupported observed receipt parameter type')
        if operand['unit'] not in available:
            raise ValueError('Receipt parameter is not current observed material')
        slot = body_ref(pool['catalog'], 'slot', port['code'], name)
        compatible(internal, slot, operand)
        result.append((slot, operand))
    return result


class RealEffectEngine(EffectEngine):
    def advance(self, current, frame, state_version, pending_actions):
        if frame.nearby_data.get('typed_execution_receipts'):
            raise ValueError('Synthetic receipt premise forbidden in real engine')
        if type(frame.nearby_data.get('native_execution_records', [])) is not list:
            raise ValueError('Invalid native execution record list')
        return super().advance(current, frame, state_version, pending_actions)

    def _form_operative_dependencies(self, internal, read, experience, partial,
                                    integration, state_version, failure):
        # Insert actual execution incidence at ordinary integration, BEFORE the
        # unchanged value composition / EffectRoute formation. No synthetic relabel.
        pool = internal.l0_state[REF_KEY]
        records = self._frame.nearby_data.get('native_execution_records', [])
        ids = [r['action_id'] for r in records]
        if len(ids) != len(set(ids)):
            raise ValueError('Repeated execution identity')
        for record in records:
            for slot, operand in assignments(internal, self._frame, record, experience):
                edge = connection(slot, operand)
                ref = digest(edge)
                if ref not in pool['edges']:
                    pool['edges'][ref] = edge
                    pool['evidence'][ref] = {'provenance': 'EXPERIENCE_INTEGRATED',
                        'state_version': state_version, 'experience_id': experience['experience_id'],
                        'integration_id': integration['integration_id'],
                        'supports': {'kind': 'RECORDED_NATIVE_EXECUTION_INCIDENCE',
                                     'record': deepcopy(record), 'after_frame_id': self._frame.frame_id}}
        super()._form_operative_dependencies(internal, read, experience, partial,
                                             integration, state_version, failure)
