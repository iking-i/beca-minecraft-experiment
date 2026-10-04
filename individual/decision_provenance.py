"""Decision authorship is separate from capability ownership and data dependency."""

EXTERNAL = {'EXTERNAL_FIXED_POLICY', 'INITIAL_EXTERNAL_POLICY'}
INTERNAL = {'INTERNAL_VARIABLE_STRUCTURE', 'INTERNAL_VARIABLE_POLICY'}


def decision_authorship(selection):
    if selection.get('category') == 'TEST_ONLY':
        return {'initiator': 'capability_test', 'selection_source': 'TEST_ONLY',
                'parameter_binding_source': 'TEST_ONLY', 'aggregate_source': 'TEST_ONLY'}
    sources = {selection.get('source'), selection.get('category')}
    for key in ('sampling', 'selection', 'scoring'):
        ref = selection.get('policy_provenance', {}).get(key, {})
        if isinstance(ref, dict):
            sources.update((ref.get('source'), ref.get('category')))
    binder = selection.get('parameter_binding', {}).get('source', {})
    binding = binder.get('category', binder.get('source')) if isinstance(binder, dict) else binder
    if sources & EXTERNAL:
        author, aggregate = 'external_fixed_policy', 'EXTERNAL_FIXED_POLICY'
    elif sources & INTERNAL:
        author, aggregate = ('mixed_policy', 'MIXED_POLICY') if binding in EXTERNAL else ('internal_structure', 'INTERNAL_VARIABLE_STRUCTURE')
    else:
        author, aggregate = 'unattributed', 'UNATTRIBUTED'
    return {'initiator': author,
            'selection_source': 'EXTERNAL_FIXED_POLICY' if sources & EXTERNAL else
                                'INTERNAL_VARIABLE_STRUCTURE' if sources & INTERNAL else 'UNATTRIBUTED',
            'parameter_binding_source': binding, 'aggregate_source': aggregate}
