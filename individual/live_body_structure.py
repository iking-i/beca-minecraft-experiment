"""BPC-LIVE-1 online facts/supports; no event reader, body call or action author.

Native ports are observed endpoints. Shared incidence records co-observation,
not a claim that a capability caused a change. Every matching port is retained.
"""
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import math

from .action_space import CATALOG_DATA, DEFINITIONS


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity(kind, data):
    return kind + ':' + sha256(canonical(data).encode()).hexdigest()


def source_identity():
    """External audit anchor for the same implementation across fresh instances."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / 'individual').glob('*.py')) + [root / 'minecraft/action-space.json']
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest() for p in paths}


@dataclass(frozen=True)
class LiveControls:
    """External preregistered measurement condition, never recursive input."""
    condition: str = 'CANONICAL'

    def __post_init__(self):
        if self.condition not in ('CANONICAL', 'NC1', 'NC2', 'NC3', 'NC4', 'NC5', 'NC6'):
            raise ValueError('Unknown frozen live control')


def observed_ports(entries):
    """Validate actual incoming catalog entries, then expose only native identity.

    The catalog validates identity; it cannot supply an unobserved endpoint.
    No action labels enter the graph and no code is chosen from this set.
    """
    ports = {}
    for entry in entries or ():
        code = entry.get('code')
        definition = DEFINITIONS.get(code) if type(code) is int else None
        if (not definition or entry.get('action_id') != definition['action_id']
                or entry.get('category') != 'BODY_CAPABILITY'
                or entry.get('parameter_schema') != {'type': 'object',
                    'properties': definition['parameters'],
                    'required': [k for k, v in definition['parameters'].items() if not v.get('optional')],
                    'additionalProperties': False}
                or entry.get('formal_enabled') != definition['formal_enabled']):
            raise ValueError('Invalid observed native capability')
        port = {'catalog_version': CATALOG_DATA['version'], 'code': code}
        ports[identity('BodyPort', port)] = port
    return [ports[key] for key in sorted(ports)]


def empty_structure(owner, caps):
    return {'version': 'BPC-LIVE-1', 'owner': list(owner), 'caps': deepcopy(caps),
            'facts': {}, 'supports': {}, 'connections': [], 'feedback': {},
            'last_sequence': 0, 'last_frame': None, 'last_state_version': None}


def exact_number(value):
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Non-numeric difference')
    numerator, denominator = value.as_integer_ratio()
    return [numerator, denominator]


def _put(graph, kind, data, rule, premises, version):
    key = identity(kind, data)
    graph['facts'].setdefault(key, {'kind': kind, 'data': deepcopy(data), 'formed_version': version})
    support = {'rule': rule, 'premises': sorted(premises)}
    proofs = graph['supports'].setdefault(key, [])
    if support not in proofs:
        proofs.append(support)
    return key


def _supported(graph, key, visiting=frozenset()):
    fact = graph['facts'].get(key)
    if not fact or key in visiting or identity(fact['kind'], fact['data']) != key:
        return False
    proofs = graph['supports'].get(key, ())
    for proof in proofs:
        rule, premises = proof['rule'], proof['premises']
        kind, data = fact['kind'], fact['data']
        if kind == 'Frame' and rule == 'LIVE_OBSERVATION' and not premises:
            if data['owner'] == graph['owner']:
                return True
            continue
        if not premises or not all(_supported(graph, p, visiting | {key}) for p in premises):
            continue
        inputs = [graph['facts'][p] for p in premises]
        if kind == 'BodyPort' and rule == 'OBSERVED_NATIVE_ENDPOINT':
            if any(f['kind'] == 'Frame' and data in f['data']['ports'] for f in inputs):
                return True
        elif kind == 'CurrentChange' and rule == 'EXACT_LIVE_DIFFERENCE':
            frames = {f['data']['frame_id']: f for f in inputs if f['kind'] == 'Frame'}
            before, after = (frames.get(x) for x in data['frame_ids'])
            if (before and after and before['data']['sequence'] + 1 == after['data']['sequence']
                    and (before['data']['namespace'], before['data']['epoch']) ==
                        (after['data']['namespace'], after['data']['epoch'])
                    and data['owner'] == graph['owner']):
                # Difference content is validated again without any event/history access.
                a, b = before['data']['channels'], after['data']['channels']
                expected = []
                for c in sorted(a.keys() | b.keys(), key=int):
                    if c in a and c in b and a[c] == b[c]:
                        continue
                    kind_value = ('appeared' if c not in a else
                                  'unobserved' if c not in b and after['data']['uncertain'] else
                                  'disappeared' if c not in b else
                                  'increased' if b[c] > a[c] else 'decreased')
                    expected.append([c, kind_value, exact_number(a.get(c)), exact_number(b.get(c)),
                                     exact_number(b[c] - a[c]) if c in a and c in b else None])
                if data['changes'] == expected and expected:
                    return True
        elif kind == 'Member' and rule == 'LIVE_RECORD_INCIDENCE':
            member = graph['facts'].get(data['object'])
            group = graph['facts'].get(data['group'])
            if (member in inputs and group in inputs and group['kind'] == 'Frame'
                    and ((member['kind'] == 'BodyPort' and member['data'] in group['data']['ports'])
                         or (member['kind'] == 'CurrentChange'
                             and member['data']['frame_ids'][1] == group['data']['frame_id']))):
                return True
        elif kind == 'Shared' and rule == 'SHARED_INCIDENCE':
            if (len(inputs) == 2 and all(f['kind'] == 'Member' for f in inputs)
                    and inputs[0]['data']['group'] == inputs[1]['data']['group']
                    and sorted(f['data']['object'] for f in inputs) == data['endpoints']):
                return True
    return False


def consume_saved(graph, previous_version, effect_screened=False):
    """Only saved facts/supports and an endogenous, saved feedback reference.

    No input-frame/history/producer arguments and no experimenter query root.
    """
    root = graph['feedback'].get('current_c')
    result = {'status': 'UNRESOLVED', 'query_source': deepcopy(graph['feedback']),
              'connection_ids': [], 'ports': [], 'root_witnesses': [],
              'read_from_committed_version': previous_version}
    if (not root or not _supported(graph, root)
            or graph['last_state_version'] is None or graph['last_state_version'] > previous_version
            or graph['feedback']['formed_version'] > previous_version):
        return result
    witnesses = set()
    def roots(key, visiting=frozenset()):
        if key in visiting:
            return
        if graph['facts'][key]['kind'] == 'Frame':
            witnesses.add(key)
        else:
            for proof in graph['supports'][key]:
                for p in proof['premises']:
                    if _supported(graph, p):
                        roots(p, visiting | {key})
    ports = {}
    for key in graph['connections']:
        f = graph['facts'].get(key)
        if (effect_screened or not f or f['kind'] != 'Shared' or root not in f['data']['endpoints']
                or f['formed_version'] >= previous_version + 1 or not _supported(graph, key)):
            continue
        others = [graph['facts'][p] for p in f['data']['endpoints'] if p != root]
        for other in others:
            if other['kind'] == 'BodyPort':
                p = other['data']
                ports[identity('BodyPort', p)] = deepcopy(p)
                result['connection_ids'].append(key)
                roots(key)
    result['ports'] = [ports[k] for k in sorted(ports)]
    result['connection_ids'] = sorted(set(result['connection_ids']))
    result['root_witnesses'] = sorted(witnesses)
    if ports:
        result['status'] = 'CONNECTED' if len(ports) == 1 else 'MULTIPLE_SUPPORTED_PORTS'
    return result


def advance_structure(prior, frame, ports, version, internal, caps, controls):
    """Incremental local online formation; previously formed edges are never rebuilt."""
    graph = deepcopy(prior)
    data = {'owner': graph['owner'], 'frame_id': frame.frame_id, 'sequence': frame.sequence_id,
            'namespace': frame.encoding_namespace, 'epoch': frame.body_epoch,
            'channels': deepcopy(frame.numeric_channels), 'ports': deepcopy(ports),
            'uncertain': frame.delta['missing_values_are_unobserved']}
    current_frame = _put(graph, 'Frame', data, 'LIVE_OBSERVATION', [], version)
    endpoint_ids = []
    if controls.condition != 'NC1':
        for port in ports:
            key = identity('BodyPort', port)
            if key not in graph['facts']:
                _put(graph, 'BodyPort', port, 'OBSERVED_NATIVE_ENDPOINT', [current_frame], version)
            endpoint_ids.append(key)
    c = None
    old_frame = prior['last_frame']
    if (old_frame and frame.delta['changes'] and not frame.delta['sample_gap']
            and controls.condition != 'NC2'):
        change = {'owner': graph['owner'], 'frame_ids': [frame.delta['previous_frame_id'], frame.frame_id],
                  'change_id': frame.delta['change_id'], 'changes': [
                      [x['channel_id'], x['kind'], exact_number(x['before']), exact_number(x['after']),
                       exact_number(x['delta'])] for x in frame.delta['changes']]}
        c = _put(graph, 'CurrentChange', change, 'EXACT_LIVE_DIFFERENCE', [old_frame, current_frame], version)
        cm = _put(graph, 'Member', {'group': current_frame, 'object': c},
                  'LIVE_RECORD_INCIDENCE', [current_frame, c], version)
        # All observed members of this online record participate, without ranking.
        for key in endpoint_ids:
            pm = _put(graph, 'Member', {'group': current_frame, 'object': key},
                      'LIVE_RECORD_INCIDENCE', [current_frame, key], version)
            edge = _put(graph, 'Shared', {'endpoints': sorted([c, key])},
                        'SHARED_INCIDENCE', [cm, pm], version)
            if edge not in graph['connections']:
                graph['connections'].append(edge)
        graph['feedback'] = {'current_c': c, 'formed_version': version,
                             'frame_id': frame.frame_id, 'source': 'LIVE_FORMATION_RESULT'}
    graph['last_sequence'] = frame.sequence_id
    graph['last_frame'] = current_frame
    graph['last_state_version'] = version
    counts = {'nodes': sum(f['kind'] in ('BodyPort', 'CurrentChange') for f in graph['facts'].values()),
              'connections': len(graph['connections']),
              'frames': sum(f['kind'] == 'Frame' for f in graph['facts'].values())}
    # Share the existing memory envelope, rather than silently adding new caps.
    limited = (counts['nodes'] + len(internal.units) > caps.units
               or counts['connections'] + len(internal.relations) > caps.relations
               or counts['frames'] > caps.history
               or any(len(p['premises']) > caps.evidence_window
                      for ps in graph['supports'].values() for p in ps))
    event = {'status': 'RESOURCE_LIMIT' if limited else 'COMPLETE_LOCAL_FORMATION',
             'state_version': version, 'frame_id': frame.frame_id, 'current_c': c,
             'observed_endpoint_ids': endpoint_ids, 'counts': counts,
             'new_connection_ids': sorted(set(graph['connections']) - set(prior['connections'])),
             'persisted': not limited and controls.condition != 'NC3',
             'association': 'shared_live_record_incidence_only'}
    if limited:
        # No partial graph, eviction, truncation or fallback publication.
        return deepcopy(prior), event
    if controls.condition == 'NC3':
        retained = deepcopy(prior)
        # Keep live sensor continuity, but never commit the formed connection/supports.
        retained['facts'][current_frame] = graph['facts'][current_frame]
        retained['supports'][current_frame] = graph['supports'][current_frame]
        retained.update(last_frame=current_frame, last_sequence=frame.sequence_id,
                        last_state_version=version, feedback=deepcopy(graph['feedback']))
        return retained, event
    return graph, event
