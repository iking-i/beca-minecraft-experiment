"""Read-only external measurements of the unchanged ordinary execution objects."""
from collections import Counter
from copy import deepcopy
import sys

from individual.formal_l0 import digest
from individual.internal_state import InternalState
from experimental.observation_interface_references.reference.references import KEY as REF
from experimental.observation_interface_references.effects.engine import KEY as FX
from experimental.operative_content.engine import ContentCapacityError


def inventory(state):
    internal = state['internal_state']
    local = internal['l0_state']
    pool, effects = local[REF], local[FX]
    packet = effects['current'] or {}
    counts = Counter(node['type'] for node in pool['nodes'].values())
    retained = len(internal['units']) + len(pool['nodes']) + len(effects['cells'])
    temporary = len(packet.get('effects', {})) + len(packet.get('operations', []))
    relations = (len(internal['relations']) + len(local['operative_test_only']['edges'])
                 + len(pool['edges']) + len(effects['routes']) + len(effects['cell_bindings']))
    return {
        'units': len(internal['units']), 'content_nodes': len(pool['nodes']),
        'content_types': dict(counts), 'pairs': counts['Pair'],
        'cells': len(effects['cells']), 'retained_unit_content_charge': retained,
        'current_effects': len(packet.get('effects', {})),
        'current_operations': len(packet.get('operations', [])),
        'current_packet_charge': temporary, 'total_unit_charge': retained + temporary,
        'unit_capacity': local['locked_caps']['units'],
        'unit_remaining': local['locked_caps']['units'] - retained - temporary,
        'relations': len(internal['relations']),
        'operative_edges': len(local['operative_test_only']['edges']),
        'typed_connections': len(pool['edges']), 'effect_routes': len(effects['routes']),
        'cell_bindings': len(effects['cell_bindings']), 'total_relation_charge': relations,
        'relation_capacity': local['locked_caps']['relations'],
        'relation_remaining': local['locked_caps']['relations'] - relations,
        'retained_observation_records': len(internal['observation_history_window']),
        'history_capacity': local['locked_caps']['history'],
        'saved_external_sources': len(pool['observations']),
        'transport_reservations_not_unit_charged': len(effects['attempts']),
        'internal_serialized_bytes': len(__import__('json').dumps(internal, ensure_ascii=False,
                                            separators=(',', ':')).encode('utf-8')),
    }


def delta(before, after, events):
    a, b = before['internal_state'], after['internal_state']
    old, new = a['l0_state'][REF], b['l0_state'][REF]
    old_pairs = {ref for ref, node in old['nodes'].items() if node['type'] == 'Pair'}
    execution = b['l0_state'].get('body_reference_execution', {})
    partials = [e['payload'] for e in events if e['event_type'] == 'RECURSIVE_PARTIAL_OUTPUT']
    expected = {ref for p in partials for ref in p['processing']['expected_outcomes']}
    dependencies = [p['processing'].get('operative_dependencies', {}) for p in partials]
    read_relations = {ref for read in dependencies for ref in read.get('relations', [])}
    read_units = {ref for relation in read_relations for ref in
                  a['relations'].get(relation, {}).get('outcomes', {}) if ref in a['units']}
    pair_operands = set(execution.get('reused_content', [])) if partials else set()
    recomputed = set(execution.get('constructed', [])) if partials else set()
    used_connections = execution.get('connections', []) if partials else []
    old_routes, new_routes = a['l0_state'][FX]['routes'], b['l0_state'][FX]['routes']
    packet = b['l0_state'][FX]['current'] or {}
    return {
        'new_units': {r: deepcopy(n) for r, n in b['units'].items() if r not in a['units']},
        'new_content': {r: {'node': deepcopy(n), 'support': deepcopy(new['node_evidence'][r])}
                        for r, n in new['nodes'].items() if r not in old['nodes']},
        'new_connections': {r: {'edge': deepcopy(n), 'support': deepcopy(new['evidence'][r])}
                            for r, n in new['edges'].items() if r not in old['edges']},
        'new_routes': {r: {'route': deepcopy(n), 'support': deepcopy(b['l0_state'][FX]['supports'][r])}
                       for r, n in new_routes.items() if r not in old_routes},
        'actual_relation_read': sorted(read_relations), 'actual_read_unit_operands': sorted(read_units),
        'actual_operative_dependencies': dependencies,
        'explicit_pair_operands_returned_by_ordinary_read': sorted(pair_operands),
        'old_pair_operands_used_to_form_wrappers': sorted(old_pairs & pair_operands),
        'existing_direct_pairs_recomputed_by_constructor': sorted(old_pairs & recomputed),
        'prior_pairs_in_expected_outcomes_not_proof_of_explicit_read': sorted(old_pairs & expected),
        'actual_typed_connections_used': deepcopy(used_connections),
        'current_constructed_pair_ids': sorted(recomputed),
        'retained_old_pair_ids': sorted(old_pairs & new['nodes'].keys()),
        'old_content_unchanged': all(new['nodes'].get(r) == n for r, n in old['nodes'].items()),
        'activated_route_ids': sorted({e['route_ref'] for e in packet.get('effects', {}).values()}),
        'current_operations': deepcopy(packet.get('operations', [])),
        'limit_events': [deepcopy(e) for e in events if e['event_type'] == 'CURRENT_LIMIT_ENCOUNTER'],
        'retention_by_need_or_purpose': 'NOT_IMPLEMENTED_IN_THIS_ENGINE',
        'runtime_questions': [deepcopy(p.get('question')) for p in b['active_processes'].values()],
    }


class CapacityTrace:
    """Observe rejected locals only; never substitute input/state/result or retry."""
    def __init__(self):
        self.records = []

    def __enter__(self):
        self.previous = sys.gettrace()
        if self.previous is not None:
            raise RuntimeError('Existing Python trace would be displaced; stop measurement')
        sys.settrace(self.trace)
        return self

    def __exit__(self, *args):
        sys.settrace(self.previous)

    def trace(self, frame, event, arg):
        if event == 'call':
            # No line-by-line tracing of JSON, SQLite or ordinary computations.
            # Only exception propagation within engines can contain staged charges.
            if frame.f_code.co_name not in {
                    'reject', 'advance', '_advance_operative', '_read_operative_operands',
                    '_form_operative_dependencies', 'validate', 'accept_observation', '_transition'}:
                return None
            frame.f_trace_lines = False
            frame.f_trace_opcodes = False
        if event == 'exception' and isinstance(arg[1], ContentCapacityError):
            values = frame.f_locals
            internal = values.get('internal', values.get('working'))
            record = {'file': frame.f_code.co_filename, 'function': frame.f_code.co_name,
                      'line': frame.f_lineno, 'message': str(arg[1])}
            if isinstance(internal, InternalState):
                record['uncommitted_internal_state'] = internal.to_dict()
                if REF in internal.l0_state and FX in internal.l0_state:
                    record['working_inventory'] = inventory({'internal_state': internal.to_dict()})
            for name in ('staged', 'products', 'used', 'reused', 'supports', 'proposals', 'snapshot'):
                if name in values:
                    record[name] = deepcopy(values[name])
                    if isinstance(record[name], set):
                        record[name] = sorted(record[name])
            if isinstance(internal, InternalState) and isinstance(values.get('staged'), dict):
                record['staged_unit_content_charge'] = len(internal.units) + len(values['staged'])
            if isinstance(internal, InternalState) and isinstance(values.get('proposals'), dict):
                pool = internal.l0_state[REF]
                record['proposed_reference_relation_charge'] = (
                    len(internal.relations) + len(internal.l0_state['operative_test_only']['edges'])
                    + len(pool['edges'].keys() | values['proposals'].keys()))
            self.records.append(record)
        return self.trace
