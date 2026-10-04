"""Body capability catalog and numeric parameter bindings, separate from learned structure.

The binding sampler is explicitly an INITIAL_EXTERNAL_POLICY, not a learned policy.
It chooses among numeric/ref domains, never among Minecraft semantic names.
"""
from copy import deepcopy
import json
from pathlib import Path

from .policies import CATALOG, PolicyRegistry

CATALOG_DATA = json.loads((Path(__file__).resolve().parents[1] / 'minecraft/action-space.json').read_text(encoding='utf-8'))
DEFINITIONS = {entry['code']: entry for entry in CATALOG_DATA['actions']}
BODY_CAPABILITY = 'BODY_CAPABILITY'
ENVIRONMENT_CONSTRAINT = 'ENVIRONMENT_CONSTRAINT'
LEARNED_STRUCTURE = 'LEARNED_STRUCTURE'


def provision(internal, entries, version, journal):
    """Append a carrier provisioning record; never rewrite earlier lifetime states."""
    if not entries:
        return
    definitions = []
    for entry in entries:
        definition = DEFINITIONS.get(entry['code'])
        if not definition or entry['action_id'] != definition['action_id'] or entry['category'] != BODY_CAPABILITY:
            raise ValueError('Bridge supplied an unregistered body action')
        definitions.append({key: deepcopy(entry[key]) for key in ('code', 'action_id', 'category', 'parameter_schema', 'environment_requirements')})
    record = {'version': CATALOG_DATA['version'], 'category': BODY_CAPABILITY, 'actions': definitions,
        'layer_boundaries': {'capabilities': BODY_CAPABILITY, 'availability': ENVIRONMENT_CONSTRAINT,
                            'experience_data': LEARNED_STRUCTURE},
        'learned_policy_formation_claimed': False}
    if internal.body_capabilities == record:
        return
    before = deepcopy(internal.body_capabilities)
    internal.body_capabilities = record
    registry = PolicyRegistry(internal)
    codes = [entry['code'] for entry in definitions]
    # Capability installation changes available codecs, not the action selection policy.
    for owner, parameter in [('body.actions', 'action_codes'), ('environment.action_interface', 'available_codes')]:
        previous = deepcopy(registry.parameters(owner)[parameter])
        if previous == codes:
            continue
        entry = internal.policy_registry[owner]
        entry['parameters'][parameter] = deepcopy(codes)
        entry['revision'] += 1
        path = f'{owner}.{parameter}'
        metadata = internal.parameter_sources.get(path, registry._metadata(owner, previous, f'A{version}'))
        metadata = {**metadata, 'value': deepcopy(codes), 'modified_by': 'external_carrier_provisioning',
            'modification_count': metadata['modification_count'] + 1, 'value_origin': 'BODY_CAPABILITY',
            'provenance': {'state_version': version, 'action_space_version': record['version'], 'learned': False}}
        internal.parameter_sources[path] = metadata
        status = internal.policy_migration_status[owner]
        status['modification_count'] += 1
        status['last_reason'] = 'external_carrier_provisioning'
        status['provenance'] = deepcopy(metadata['provenance'])
        journal.append(('BODY_INTERFACE_PARAMETER_UPDATED', {'parameter': path, 'before': previous,
            'after': deepcopy(codes), 'metadata': deepcopy(metadata)}))
    owner = 'action.parameter_binding'
    if owner not in internal.policy_registry:
        category, parameters, location = CATALOG[owner]
        internal.policy_registry[owner] = {'policy_id': owner, 'category': category, 'parameters': deepcopy(parameters),
            'created_at': f'A{version}', 'implementation': location, 'revision': 0}
        internal.policy_migration_status[owner] = {'current_source': category, 'modification_count': 0,
            'migration_count': 0, 'last_reason': 'body_capability_extension', 'provenance': {'state_version': version},
            'status': 'initialized', 'historical_origin_verified': True}
        registry = PolicyRegistry(internal)
        for key, value in parameters.items():
            internal.parameter_sources[f'{owner}.{key}'] = registry._metadata(owner, value, f'A{version}')
    journal.append(('BODY_CAPABILITIES_PROVISIONED', {'before': before, 'after': deepcopy(record),
        'source': BODY_CAPABILITY, 'external_provisioning': True, 'learned': False, 'state_version': version,
        'parameter_binding_policy': PolicyRegistry(internal).reference(owner)}))


def bind_parameters(code, frame, internal, selection):
    """Mechanical sampling for the existing fixed selector, not a use/recipe policy."""
    name = DEFINITIONS[code]['action_id']
    body = frame['nearby_data']['body']
    registry = PolicyRegistry(internal)
    policy = registry.parameters('action.parameter_binding')
    if policy['method'] != 'numeric_domain_lcg':
        raise ValueError('Unsupported explicit parameter binding policy')
    lcg = registry.parameters('formal.action_sampling' if selection.get('policy_id') == 'formal.action_sampling' else 'action.selection')
    choices = []

    def choose(label, values):
        if not values:
            raise ValueError(f'No numeric domain for {label}')
        seed = internal.exploration_state['random_state']
        state = (lcg['multiplier'] * seed + lcg['increment']) % lcg['modulus']
        internal.exploration_state['random_state'] = state
        value = values[state % len(values)]
        choices.append({'parameter': label, 'domain': deepcopy(values), 'seed_before': seed,
                        'seed_after': state, 'value': value})
        return value

    blocks = [b['target_ref'] for b in frame['nearby_data']['blocks'] if b.get('target_ref')]
    entities = [e['target_ref'] for e in frame['nearby_data']['entities'] if e.get('target_ref')]
    inventory = body['inventory_slots']
    win = body.get('container') or body['inventory_screen']
    slots = win['slot_state']
    occupied = lambda rows: [s['slot'] for s in rows if s['count'] > 0]
    empty = lambda rows: [s['slot'] for s in rows if s['count'] == 0]
    p = {}
    if name == 'LOOK_DELTA':
        p = {key: choose(key, policy['look_deltas']) for key in ('yaw_delta', 'pitch_delta')}
    elif name == 'LOOK_AT': p = {'object_ref': choose('object_ref', blocks + entities)}
    elif name in ('DIG', 'INTERACT_BLOCK'): p = {'block_ref': choose('block_ref', blocks)}
    elif name in ('INTERACT_ENTITY', 'ATTACK_ENTITY'): p = {'entity_ref': choose('entity_ref', entities)}
    elif name == 'PLACE_BLOCK':
        p = {'inventory_slot': choose('inventory_slot', occupied(inventory)), 'reference_block': choose('reference_block', blocks),
             'face': choose('face', list(range(6)))}
    elif name == 'SELECT_HOTBAR_SLOT': p = {'slot': choose('slot', list(range(9)))}
    elif name == 'USE_HELD_ITEM': p = {'duration_ms': choose('duration_ms', policy['use_durations_ms'])}
    elif name in ('DROP_ITEM', 'MOVE_INVENTORY_ITEM', 'EQUIP_FROM_SLOT'):
        source = choose('source_slot', occupied(inventory))
        p = {'slot' if name == 'DROP_ITEM' else 'source_slot': source}
        if name == 'EQUIP_FROM_SLOT': p['equipment_slot'] = choose('equipment_slot', list(range(6)))
        else:
            count = inventory[source]['count']
            p['amount'] = choose('amount', list(range(1, min(count, policy['amount_cap']) + 1)))
            if name == 'MOVE_INVENTORY_ITEM': p['target_slot'] = choose('target_slot', [s['slot'] for s in inventory if s['slot'] != source])
    elif name in ('MOVE_CONTAINER_ITEM', 'TAKE_CONTAINER_ITEM', 'PUT_CONTAINER_ITEM', 'MOVE_ITEM_TO_CRAFT_SLOT'):
        start, end = win['inventory_start'], win['inventory_end']
        sources = occupied(slots)
        targets = [s['slot'] for s in slots]
        if name == 'TAKE_CONTAINER_ITEM': sources = [s for s in sources if s < start]; targets = list(range(start, end))
        elif name == 'PUT_CONTAINER_ITEM': sources = [s for s in sources if start <= s < end]; targets = list(range(start))
        elif name == 'MOVE_ITEM_TO_CRAFT_SLOT': targets = body['crafting']['input_slots']
        source = choose('source_slot', sources)
        p = {'source_slot': source, 'target_slot': choose('target_slot', [s for s in targets if s != source]),
             'amount': choose('amount', list(range(1, min(slots[source]['count'], policy['amount_cap']) + 1)))}
        if name != 'MOVE_ITEM_TO_CRAFT_SLOT': p['container_id'] = win['container_id']
    elif name == 'CLOSE_CONTAINER': p = {'container_id': win['container_id']}
    elif name == 'TAKE_CRAFT_RESULT': p = {'target_slot': choose('target_slot', list(range(win['inventory_start'], win['inventory_end'])))}
    elif name == 'CLICK_SLOT':
        p = {'container_id': win['container_id'], 'slot': choose('slot', [s['slot'] for s in slots]),
             'mouse_button': choose('mouse_button', [0, 1])}
    selection['parameter_binding'] = {'source': registry.reference('action.parameter_binding'),
        'parameters': registry.parameter_references('action.parameter_binding'), 'choices': choices,
        'frame_id': frame['frame_id'], 'item_semantics_used': False, 'learned': False}
    return p


def formal_command(code, parameters):
    return {'method': 'perform', 'args': {'action_id': DEFINITIONS[code]['action_id'], 'parameters': deepcopy(parameters)}}
