"""Physical action codecs. The structural engine sees only integer action codes."""

from .policies import PolicyRegistry, positive_number

ACTION_CODES = (0, 1, 2)
DEBUG_ACTION_NAMES = {0: 'NO_OP', 1: 'MOVE_FORWARD_SHORT', 2: 'JUMP'}


def body_command(code, duration_ms=120):
    if code == 0:
        return None
    if code == 1:
        return {'method': 'move', 'args': {'direction': 'forward', 'durationMs': duration_ms}}
    if code == 2:
        return {'method': 'move', 'args': {'direction': 'jump', 'durationMs': duration_ms}}
    raise ValueError('Unknown discrete action code')


def select_action(internal, pattern_id, available_codes=None):
    """Explore untested/ambiguous temporal associations, without a reward function."""
    attempts = internal.exploration_state['attempts']
    registry = PolicyRegistry(internal)
    codes = tuple(ACTION_CODES if available_codes is None else available_codes)
    if not codes:
        raise ValueError('No currently available body capability')
    scoring = registry.parameters('action.scoring')
    selection = registry.parameters('action.selection')
    base = positive_number(scoring['base_score'], 'base_score', allow_zero=True)
    weight = positive_number(scoring['unresolved_weight'], 'unresolved_weight', allow_zero=True)
    offset = positive_number(scoring['attempt_offset'], 'attempt_offset')
    exponent = positive_number(scoring['attempt_exponent'], 'attempt_exponent', allow_zero=True)
    temporary = positive_number(scoring['temporary_score'], 'temporary_score', allow_zero=True)
    if selection['method'] != 'max_score_lcg_tie':
        raise ValueError('Unsupported selection method')
    scores, components = {}, {}
    for code in codes:
        key = f'{pattern_id}:{code}'
        relation = internal.relations.get(key, {})
        count = attempts.get(key, 0)
        denominator = (offset + count) ** exponent
        unresolved = int(relation.get('unresolved', False))
        scores[code] = (base + weight * unresolved + temporary) / denominator
        components[str(code)] = {
            'environment_constraint': {'eligible': code in codes,
                                       'source': registry.reference('environment.action_interface'),
                                       'mechanism': registry.reference('body.actions'),
                                       'meaning': 'available_codec_only; not a prediction of safety'},
            'initial_policy_component': {'value': base / denominator,
                'source': registry.reference('action.scoring'), 'attempt_count': count},
            'internal_structure_component': {'value': weight * unresolved / denominator,
                'source': 'INTERNAL_VARIABLE_STRUCTURE', 'data_category': 'LEARNED_STRUCTURE', 'relation_id': key,
                'relation_present': bool(relation), 'unresolved': bool(unresolved),
                'attempt_count': count, 'evaluation_policy': registry.reference('action.scoring')},
            'temporary_evaluation_component': {'value': temporary / denominator,
                'active': temporary != 0, 'source': registry.reference('action.scoring')},
            'denominator': denominator, 'final_score': scores[code]}
    best = max(scores.values())
    candidates = [code for code in codes if scores[code] == best]
    seed_before = internal.exploration_state['random_state']
    state = (selection['multiplier'] * seed_before + selection['increment']) % selection['modulus']
    internal.exploration_state['random_state'] = state
    code = candidates[state % len(candidates)]
    key = f'{pattern_id}:{code}'
    attempts[key] = attempts.get(key, 0) + 1
    # Only a working window: full action history remains in append-only events.
    if len(attempts) > selection['attempt_capacity']:
        del attempts[next(iter(attempts))]
    references = registry.parameter_references('action.scoring')
    return code, {'scores': {str(k): v for k, v in scores.items()}, 'tie_state': state,
                  'seed_before': seed_before, 'pattern_id': pattern_id,
                  'criterion': 'temporal_evidence_gap', 'reward': None, 'score_components': components,
                  'policy_provenance': {'scoring': registry.reference('action.scoring'),
                      'selection': registry.reference('action.selection'), 'parameters': references,
                      'selection_parameters': registry.parameter_references('action.selection'),
                      'data_source': 'INTERNAL_VARIABLE_STRUCTURE',
                      'data_dependencies': ['relations', 'exploration_state.attempts', 'exploration_state.random_state']}}

