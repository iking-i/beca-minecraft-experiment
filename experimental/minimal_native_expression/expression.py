"""Decode actual ordinary Pair operands; ambiguity never authorizes transport."""
from copy import deepcopy
import json
import math
from pathlib import Path
from uuid import uuid4

from individual.action_space import CATALOG_DATA, DEFINITIONS
from individual.internal_state import InternalState
from individual.formal_l0 import digest
from experimental.native_body_operands.engine import validate_native, unit_identity
from experimental.native_parameter_binding_extension.channel import BindingCore
from experimental.native_parameter_binding_extension.engine import validate_bindings
from experimental.operative_content.engine import validate_content


def scalar(node, schema, frame):
    if node.get('type') == 'ObservedValue':
        value = node['value']
        if (schema.get('type') not in ('integer', 'number') or type(value) not in (int, float)
                or not math.isfinite(value) or (schema['type'] == 'integer' and type(value) is not int)
                or (schema['type'] == 'integer' and abs(value) > 2**53 - 1)
                or value < schema.get('minimum', -math.inf) or value > schema.get('maximum', math.inf)):
            raise ValueError('Invalid exact numeric parameter')
        return value
    if node.get('type') == 'ObservedReference' and schema.get('type') == 'string':
        tokens = {r.get('target_ref') for family in ('blocks', 'entities')
                  for r in frame['nearby_data'].get(family, [])}
        if (node['token'] not in tokens or node['namespace'] != frame['encoding_namespace']
                or node['body_epoch'] != frame['body_epoch']):
            raise ValueError('Stale reference')
        return node['token']
    raise ValueError('Missing typed parameter source')


def read_expression(state, port):
    """External measurement names the port; actual Pair endpoints supply values."""
    if (set(port) != {'catalog_version', 'code'} or type(port['code']) is not int
            or type(port['catalog_version']) is not int):
        raise ValueError('Invalid measurement identity')
    if port['catalog_version'] != CATALOG_DATA['version'] or port['code'] not in DEFINITIONS:
        raise ValueError('Catalog mismatch')
    internal = InternalState.from_dict(state['internal_state'])
    validate_native(internal)
    graph = validate_bindings(internal)
    pool = validate_content(internal)
    frame = state['observation_frame']
    definition = DEFINITIONS[port['code']]
    schema = definition['parameters']
    declaration, = [d for d in frame['nearby_data']['body']['action_space'] if d['code'] == port['code']]
    required = {k for k, v in schema.items() if not v.get('optional')}
    if (not declaration['formal_enabled'] or not declaration['currently_available']
            or declaration['parameter_schema'] != {'type': 'object', 'properties': schema,
                'required': sorted(required), 'additionalProperties': False}):
        raise ValueError('Current declaration incompatible/unavailable')
    native_port = unit_identity({'type': 'NativePort', **port})
    admitted = set(internal.l0_state.get('native_operand_execution', {}).get('admitted_native_units', []))
    if native_port not in admitted:
        return {'status': 'MISSING_PORT', 'candidates': [], 'bindings': {}}
    bindings = {k: {} for k in schema}
    used = set(internal.l0_state.get('typed_connection_execution', {}).get('connections', []))
    # Only products of actual last ordinary execution, not arbitrary saved Pairs.
    for ref in internal.l0_state.get('content_execution', {}).get('constructed', []):
        node = pool['nodes'][ref]
        if node['type'] != 'Pair':
            continue
        left, right = pool['nodes'][node['left']], pool['nodes'][node['right']]
        if left['type'] != 'UnitRef' or right['type'] != 'UnitRef':
            continue
        slot = internal.units[left['unit']]['pattern']
        if not isinstance(slot, dict) or slot.get('type') != 'ParameterSlot' or slot['port'] != native_port:
            continue
        name = slot['name']  # Declared protocol label, never a value lookup rule.
        if name not in schema or left['unit'] not in admitted or right['unit'] not in admitted:
            raise ValueError('Invalid or inaccessible slot endpoint')
        edge = {'type': 'DirectedConnection', 'source': left['unit'], 'target': right['unit']}
        edge_ref = digest(edge)
        support = pool['evidence'][ref].get('direct_supports', {})
        if (edge_ref not in used or graph['edges'].get(edge_ref) != edge
                or support != {'connection_refs': [edge_ref], 'unit_refs': [left['unit'], right['unit']]}):
            raise ValueError('Pair lacks actual executed connection support')
        value = scalar(internal.units[right['unit']]['pattern'], schema[name], frame)
        key = json.dumps(value, sort_keys=True, allow_nan=False)
        bindings[name][key] = {'value': value, 'pair_ref': ref, 'connection_ref': edge_ref,
            'slot_ref': left['unit'], 'operand_ref': right['unit'],
            'audit': deepcopy(graph['evidence'].get(edge_ref, {}))}
    if any(not bindings[name] for name in required):
        return {'status': 'MISSING_BINDING', 'candidates': [], 'bindings': bindings}
    # Multiple-slot ambiguity is refused; never enumerate compatible combinations.
    ambiguous = [name for name, values in bindings.items() if len(values) > 1]
    if ambiguous and len(schema) != 1:
        return {'status': 'AMBIGUOUS', 'candidates': [], 'bindings': bindings}
    if len(schema) == 1:
        name, = schema
        candidates = [{'code': port['code'], 'parameters': {name: row['value']}}
                      for row in bindings[name].values()]
        if not candidates and name not in required:
            candidates = [{'code': port['code'], 'parameters': {}}]
    else:
        parameters = {}
        for name, values in bindings.items():
            if values:
                row, = values.values()
                parameters[name] = row['value']
        candidates = [{'code': port['code'], 'parameters': parameters}]
    return {'status': 'UNIQUE' if len(candidates) == 1 else 'AMBIGUOUS',
        'candidates': candidates, 'bindings': bindings, 'port': deepcopy(port),
        'action_code_author': 'EXPERIMENTER_MEASUREMENT_PORT',
        'adoption_authority': 'NOT_ESTABLISHED'}


class OneAttempt:
    """Mechanical TEST_ONLY tail. Ledger reservation forbids uncertainty retries."""
    def __init__(self, ledger):
        self.ledger = Path(ledger)

    def execute(self, core, port):
        if not isinstance(core, BindingCore):
            raise ValueError('Only isolated BindingCore is admitted')
        if (core._closed or core._paused or not core._session_active or core._computation is not None
                or core._await_fresh_observation):
            raise ValueError('Core unavailable for this attempt')
        before = core.state.to_dict()
        read = read_expression(before, port)
        report = {'read': read, 'perform_attempts': 0, 'before': before,
                  'classification': 'NOT_READY', 'retry': False}
        if read['status'] != 'UNIQUE':
            report['reason'] = read['status']
            return report
        expression, = read['candidates']
        # Atomic reservation before transport; survives process replacement.
        with self.ledger.open('x', encoding='utf-8') as f:
            json.dump({'before': before, 'read': read, 'expression': expression}, f, allow_nan=False)
        report.update(perform_attempts=1, expression=expression, classification='NOT_TESTABLE')
        action_id = str(uuid4())
        request = {'action_id': action_id, 'action_code': expression['code'],
                   'status': 'requested', 'method': 'perform', 'args': deepcopy(expression),
                   'initiator': 'TEST_ONLY_MECHANICAL_EXPRESSION_PROJECTION',
                   'provenance': {'source_state_version': before['state_version'], 'read': deepcopy(read)}}
        core._transition('ACTION_REQUESTED', request, latest_action=request)
        try:
            receipt = core._bridge.call('perform', deepcopy(expression))
            report['receipt'] = deepcopy(receipt)
            if (receipt.get('code') != expression['code'] or receipt.get('parameters') != expression['parameters']
                    or not receipt.get('started_at') or not receipt.get('finished_at')
                    or receipt.get('result') != {'input_sent': 1, 'effect_acknowledged': 0}
                    or receipt.get('effect_attribution') != 'temporal_observation_only'):
                report['classification'] = 'FAIL'
                raise ValueError('Execution receipt mismatch')
            final = {**request, 'status': 'executed', 'result': deepcopy(receipt)}
            core._transition('ACTION_EXECUTED', final, latest_action=final)
            core._pending_actions.append({'action_id': action_id, 'action_code': expression['code'],
                'parameters': deepcopy(expression['parameters']), 'status': 'executed'})
            renewed = core._bridge.call('observe')
            report['renewed_observation'] = deepcopy(renewed)
            core.accept_observation(renewed)
            report['after'] = core.state.to_dict()
            report['classification'] = 'TRANSPORT_AND_REENTRY_COMPLETED'
        except Exception as error:
            report['error'] = {'type': type(error).__name__, 'message': str(error)}
            # An observation error after execution must not rewrite execution as failure.
            if 'after' not in report and core.state.latest_action['status'] == 'requested':
                core._transition('ACTION_FAILED', {**request, 'status': 'failed', 'error': report['error']},
                    latest_action={**request, 'status': 'failed', 'error': report['error']})
        with self.ledger.with_suffix(self.ledger.suffix + '.result.json').open('x', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, allow_nan=False, indent=2)
        return report
