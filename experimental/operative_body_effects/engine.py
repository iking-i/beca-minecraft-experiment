"""Candidate exact-occurrence propagation in the ordinary ReferenceEngine hooks."""
from copy import deepcopy
import math

from individual.formal_l0 import digest
from experimental.body_interface_references.engine import (
    ReferenceEngine, validate as validate_references, value_ref, connection)
from experimental.body_interface_references.references import KEY as REF_KEY, resolve
from experimental.operative_content.engine import ContentCapacityError

KEY = 'operative_effects_test_only'
VERSION = 'OCCURRENCE-EFFECTS-TEST_ONLY-1'


def empty_pool():
    return {'version': VERSION, 'routes': {}, 'supports': {}, 'cells': {},
            'cell_bindings': [], 'current': None, 'attempts': {}}


def trigger(internal, fact):
    source = internal.l0_state[REF_KEY]['current_source']
    if (type(fact.get('before')) not in (int, float)
            or type(fact.get('after')) not in (int, float)
            or not math.isfinite(fact['before']) or not math.isfinite(fact['after'])
            or fact['before'] == fact['after']):
        return None
    return {'namespace': source['namespace'], 'channel_id': fact['channel_id'],
            'kind': fact['kind'], 'before': value_ref(fact['before']),
            'after': value_ref(fact['after'])}


def receiver(internal, ref):
    if type(ref) is dict and set(ref) == {'type', 'cell'} and ref['type'] == 'CellRef':
        cells = internal.l0_state[KEY]['cells']
        if type(ref['cell']) is not str or ref['cell'] not in cells:
            raise ValueError('Unknown cell receiver')
        return {'type': 'Cell', **cells[ref['cell']]}
    result = resolve(internal, ref)
    if not isinstance(result, dict) or result.get('type') != 'ParameterSlot':
        raise ValueError('Effect receiver is not a declared slot/cell')
    return result


def validate(internal):
    base = validate_references(internal)
    pool = internal.l0_state.get(KEY)
    if (type(pool) is not dict or set(pool) != set(empty_pool())
            or pool['version'] != VERSION
            or any(type(pool[k]) is not dict for k in ('routes', 'supports', 'cells', 'attempts'))
            or type(pool['cell_bindings']) is not list):
        raise ValueError('Invalid effect state/version')
    if len(pool['attempts']) > 1:
        raise ValueError('Only current transport reservation belongs in runtime state')
    if set(pool['routes']) != set(pool['supports']):
        raise ValueError('Effect support coverage mismatch')
    for cell in pool['cells'].values():
        if (set(cell) != {'value', 'value_type'} or cell['value_type'] not in ('integer', 'number')
                or type(cell['value']) not in (int, float) or not math.isfinite(cell['value'])
                or cell['value_type'] == 'integer' and type(cell['value']) is not int):
            raise ValueError('Invalid typed cell')
    for binding in pool['cell_bindings']:
        if set(binding) != {'receiver', 'operand'}:
            raise ValueError('Invalid cell binding')
        receiver(internal, binding['receiver']); resolve(internal, binding['operand'])
    for ref, route in pool['routes'].items():
        if (set(route) != {'type', 'trigger', 'receiver'} or route['type'] != 'EffectRoute'
                or digest(route) != ref):
            raise ValueError('Invalid effect route')
        t = route['trigger']
        if (set(t) != {'namespace', 'channel_id', 'kind', 'before', 'after'}
                or t['namespace'] != base['catalog']['namespace']
                or type(t['channel_id']) is not str or not t['channel_id']):
            raise ValueError('Invalid occurrence trigger')
        for endpoint in (t['before'], t['after']):
            if resolve(internal, endpoint).get('type') != 'ObservedValue':
                raise ValueError('Effect trigger is not an observed numeric endpoint')
        receiver(internal, route['receiver'])
        support = pool['supports'][ref]
        if set(support) != {'binding', 'transition', 'formation'}:
            raise ValueError('Missing direct effect supports')
        binding = support['binding']
        if route['receiver']['type'] == 'CellRef':
            if {'receiver': route['receiver'], 'operand': t['before']} not in pool['cell_bindings']:
                raise ValueError('Missing cell binding support')
        elif base['edges'].get(binding) != connection(route['receiver'], t['before']):
            raise ValueError('Missing receiver binding support')
        if base['edges'].get(support['transition']) != connection(t['before'], t['after']):
            raise ValueError('Missing observed transition support')
        if trigger(internal, support['formation'].get('change_fact', {})) != t:
            raise ValueError('Effect trigger differs from actually integrated change')
    packet = pool['current']
    if packet is not None:
        if (set(packet) != {'frame_id', 'state_version', 'effects', 'read_dependencies', 'body_status', 'operations'}
                or type(packet['effects']) is not dict or type(packet['operations']) is not list):
            raise ValueError('Invalid current effect packet')
        executed = set(internal.l0_state['body_reference_execution']['connections'])
        for ref, effect in packet['effects'].items():
            if (set(effect) != {'type', 'receiver', 'operand', 'route_ref', 'occurrence'}
                    or effect['type'] != 'ReceiverEffect' or digest(effect) != ref):
                raise ValueError('Invalid current effect identity')
            route = pool['routes'].get(effect['route_ref'])
            support = pool['supports'].get(effect['route_ref'])
            if (not route or not support or effect['receiver'] != route['receiver']
                    or effect['operand'] != route['trigger']['after']
                    or trigger(internal, effect['occurrence']) != route['trigger']
                    or effect['occurrence'] not in internal.detected_changes['changes']
                    or support['transition'] not in executed
                    or effect['receiver']['type'] != 'CellRef' and support['binding'] not in executed):
                raise ValueError('Effect lacks actual executed route support')
    packet_count = (len(pool['current']['effects']) + len(pool['current'].get('operations', []))) if pool['current'] else 0
    if len(internal.units) + len(base['nodes']) + len(pool['cells']) + packet_count > internal.l0_state['locked_caps']['units']:
        raise ContentCapacityError('Shared Unit/content/effect capacity exceeded')
    if (len(internal.relations) + len(internal.l0_state['operative_test_only']['edges'])
            + len(base['edges']) + len(pool['routes']) + len(pool['cell_bindings'])
            > internal.l0_state['locked_caps']['relations']):
        raise ContentCapacityError('Shared relation/effect route capacity exceeded')
    return pool


class EffectEngine(ReferenceEngine):
    def advance(self, current, frame, state_version, pending_actions):
        from individual.internal_state import InternalState
        working = InternalState.from_dict(current)
        validate(working)
        working.l0_state[KEY]['current'] = None
        self._effect_version = state_version
        result = super().advance(working.to_dict(), frame, state_version, pending_actions)
        validate(result[0])
        return result

    def _read_operative_operands(self, internal, reference):
        result, read = super()._read_operative_operands(internal, reference)
        if not self._executing:
            return result, read
        pool = validate(internal)
        base = internal.l0_state[REF_KEY]
        used = set(internal.l0_state['body_reference_execution']['connections'])
        occurrences = {digest(t): (t, fact) for fact in internal.detected_changes['changes']
                       if (t := trigger(internal, fact)) is not None}
        effects = {}
        for route_ref, route in pool['routes'].items():
            matched = occurrences.get(digest(route['trigger']))
            if matched is None:
                continue
            support = pool['supports'][route_ref]
            if support['transition'] not in used:
                continue
            if route['receiver']['type'] != 'CellRef' and support['binding'] not in used:
                continue
            t, fact = matched
            target = receiver(internal, route['receiver'])
            value = resolve(internal, t['after'])
            if target['type'] == 'Cell':
                if target['value_type'] == 'integer' and value['value_type'] != 'integer':
                    raise ValueError('Cell effect type mismatch')
                pool['cells'][route['receiver']['cell']]['value'] = value['value']
            effect = {'type': 'ReceiverEffect', 'receiver': deepcopy(route['receiver']),
                      'operand': deepcopy(t['after']), 'route_ref': route_ref,
                      'occurrence': deepcopy(fact)}
            effect_ref = digest(effect)
            effects[effect_ref] = effect
            result['outcomes'][effect_ref] = {'unit_id': effect_ref, 'effect_ref': effect_ref}
        pool['current'] = {'frame_id': self._frame.frame_id,
                           'state_version': self._effect_version,
                           'effects': effects, 'read_dependencies': deepcopy(read),
                           'body_status': 'UNPROJECTED'}
        from .native import project
        status, operations = project(internal, self._frame, effects)
        pool['current'].update(body_status=status, operations=operations)
        for operation in operations:
            ref = digest(operation)
            result['outcomes'][ref] = {'unit_id': ref, 'operation_ref': ref}
        validate(internal)
        return result, read

    def _form_operative_dependencies(self, internal, read, experience, partial,
                                    integration, state_version, failure):
        # Existing ordinary integration forms binding/value connections first.
        super()._form_operative_dependencies(internal, read, experience, partial,
                                             integration, state_version, failure)
        pool = internal.l0_state[KEY]
        base = internal.l0_state[REF_KEY]
        # A creator-supplied typed cell is another native receiver. Its current
        # value identifies the binding operand exactly; no value search/ranking.
        for name, cell in pool['cells'].items():
            operand = value_ref(cell['value'])
            if operand['unit'] in internal.units:
                binding = {'receiver': {'type': 'CellRef', 'cell': name}, 'operand': operand}
                if binding not in pool['cell_bindings']:
                    pool['cell_bindings'].append(binding)
        bindings = [(ref, e['source'], e['target']) for ref, e in base['edges'].items()
                    if e['source'].get('type') == 'BodyRef' and e['source'].get('kind') == 'slot']
        bindings += [(digest(b), b['receiver'], b['operand']) for b in pool['cell_bindings']]
        for fact in internal.detected_changes['changes']:
            t = trigger(internal, fact)
            if t is None:
                continue
            transition = digest(connection(t['before'], t['after']))
            if transition not in base['edges']:
                continue
            for binding_ref, target, operand in bindings:
                if operand != t['before']:
                    continue
                route = {'type': 'EffectRoute', 'trigger': deepcopy(t), 'receiver': deepcopy(target)}
                ref = digest(route)
                if ref not in pool['routes']:
                    pool['routes'][ref] = route
                    pool['supports'][ref] = {'binding': binding_ref, 'transition': transition,
                        'formation': {'experience_id': experience['experience_id'],
                                      'integration_id': integration['integration_id'],
                                      'change_fact': deepcopy(fact),
                                      'state_version': state_version}}
        validate(internal)
