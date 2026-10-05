"""Entirely synthetic legal-source fixtures; not existing-A empirical evidence."""
from copy import deepcopy
from .codec import record_from_events, shape_id


def events(index, context, code, consequence, parameters=None):
    base = index * 10
    def frame(suffix, channel, sequence):
        return {'frame_id': f'F-{index}-{suffix}', 'sequence_id': sequence,
                'encoding_namespace': 'TEST_ONLY-fixture', 'body_epoch': 0,
                'numeric_channels': {str(channel): index},
                'delta': {'changes': [{'channel_id': channel, 'kind': 'changed'}]}}
    a, b = frame('a', context, base), frame('b', consequence, base + 1)
    p = {} if parameters is None else deepcopy(parameters)
    action = {'action_id': f'A-{index}', 'action_code': code, 'method': 'perform',
              'args': {'code': code, 'parameters': p}, 'status': 'requested'}
    experience = {'experience_id': f'E-{index}', 'antecedent': shape_id(a['delta']),
                  'outcome': shape_id(b['delta']), 'action_code': code,
                  'root': f"{shape_id(a['delta'])}:{code}", 'frame_ids': [a['frame_id'], b['frame_id']],
                  'action_ids': [action['action_id']], 'action_statuses': ['executed'],
                  'action_parameters': [deepcopy(p)], 'causality': 'temporal_association_only'}
    def event(kind, payload, offset):
        return {'event_id': f'EV-{index}-{offset}', 'individual_id': 'TEST_ONLY-CEC0',
                'event_sequence': base + offset, 'state_version': base + offset,
                'event_type': kind, 'payload': payload, 'category': 'TEST_ONLY_FIXTURE'}
    return (event('EXPERIENCE_FORMED', experience, 3), event('ACTION_REQUESTED', action, 1),
            event('ACTION_EXECUTED', {**deepcopy(action), 'status': 'executed'}, 2),
            event('OBSERVATION_FRAME', a, 0), event('OBSERVATION_FRAME', b, 4))


def fixture():
    # Both positive incidence examples plus a disconnected negative pair.
    return tuple(record_from_events(*events(i, u, c, y), 2)
                 for i, u, c, y in ((1, 0, 3, 1), (2, 5, 3, 7), (3, 8, 9, 1), (4, 10, 12, 15)))
