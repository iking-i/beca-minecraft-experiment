"""Numeric encoding boundary. Human labels exist only in separate debug mappings."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import math


def stable_id(value):
    return int.from_bytes(hashlib.sha256(value.encode('utf-8')).digest()[:7], 'big')


@dataclass
class ObservationFrame:
    frame_id: str
    sequence_id: int
    timestamp: str
    encoding_namespace: str
    body_epoch: int
    self_channels: dict
    spatial_data: dict
    nearby_data: dict
    numeric_channels: dict
    coverage: dict
    delta: dict = field(default_factory=dict)
    internal_observations: list = field(default_factory=list)

    def to_dict(self):
        return deepcopy(asdict(self))


class FrameEncoder:
    # This is a sensor layout, not concepts/values supplied to the individual.
    SELF_FIELDS = ('health', 'hunger')

    def __init__(self, individual_id):
        self.individual_id = individual_id
        self.debug_mapping = {'channels': {}, 'object_types': {}}

    def encode(self, raw, sequence, body_epoch=0):
        # Full per-frame mappings are journaled outside the individual's structure.
        self.debug_mapping = {'channels': {}, 'object_types': {}}
        channels = {}
        own = {}
        position = raw['position']
        namespace = str(raw.get('encoding', {}).get('protocol_version') or 'unreported')

        def add(descriptor, value, debug_label):
            if value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                return None
            channel_id = str(stable_id(f'{namespace}:{descriptor}'))
            known = self.debug_mapping['channels'].get(channel_id)
            if known is not None and known != debug_label:
                raise ValueError('Sensor channel encoding collision')
            self.debug_mapping['channels'][channel_id] = debug_label
            channels[channel_id] = value
            return channel_id

        for index, name in enumerate(self.SELF_FIELDS):
            channel = add(f's:{index}', raw.get(name), name)
            if channel:
                own[channel] = raw[name]
        for index, axis in enumerate(('x', 'y', 'z'), start=2):
            add(f's:{index}', position[axis], f'position.{axis}')
        for index, name in enumerate(('yaw', 'pitch'), start=5):
            add(f's:{index}', raw.get('orientation', {}).get(name), f'orientation.{name}')
        add('s:7', raw.get('time', {}).get('timeOfDay'), 'time.timeOfDay')
        add('s:8', raw.get('time', {}).get('day'), 'time.day')

        nearby = {'blocks': [], 'entities': [], 'inventory': []}
        for family, source in (('blocks', raw.get('nearbyBlocks', [])), ('entities', raw.get('nearbyEntities', []))):
            for item in source:
                numeric_type = item.get('type_id', item.get('type'))
                if isinstance(numeric_type, bool) or not isinstance(numeric_type, int):
                    # Stable fallback encoding stays on this boundary, never in recursion.
                    numeric_type = stable_id(f'{namespace}:{family}:{item.get("name", item.get("type", "?"))}')
                type_key = f'{namespace}:{family}:{numeric_type}'
                self.debug_mapping['object_types'][type_key] = item.get('name')
                p = item['position']
                object_key = (f'b:{p["x"]}:{p["y"]}:{p["z"]}' if family == 'blocks' else f'e:{item["id"]}')
                object_id = stable_id(f'{namespace}:{object_key}')
                relative = [p[axis] - position[axis] for axis in ('x', 'y', 'z')]
                nearby[family].append({'object_id': object_id, 'type_id': numeric_type, 'relative_position': relative,
                    'target_ref': item.get('block_ref' if family == 'blocks' else 'entity_ref')})
                add(f'{object_key}:0', numeric_type, f'{object_key}.type_id')
                for index, value in enumerate(relative, start=1):
                    add(f'{object_key}:{index}', round(value, 5), f'{object_key}.relative_{index}')
        inventory_counts = {}
        for item in raw.get('inventory', []):
            numeric_type = item.get('type')
            if isinstance(numeric_type, bool) or not isinstance(numeric_type, int):
                numeric_type = stable_id(f'{namespace}:inventory:{item["name"]}')
            inventory_counts[numeric_type] = inventory_counts.get(numeric_type, 0) + item['count']
            self.debug_mapping['object_types'][f'{namespace}:inventory:{numeric_type}'] = item.get('name')
        for numeric_type, count in sorted(inventory_counts.items()):
            nearby['inventory'].append({'type_id': numeric_type, 'count': count})
            add(f'i:{numeric_type}', count, f'inventory:{numeric_type}.count')
        if raw.get('actionSpace'):
            # Slot positions and references are carrier encoding, never item-use knowledge.
            body = { 'inventory_slots': deepcopy(raw['inventorySlots']),
                     'selected_hotbar_slot': raw.get('selectedHotbarSlot'),
                     'held_item': deepcopy(raw.get('heldItem')),
                     'inventory_screen': deepcopy(raw['inventoryScreen']),
                     'container': deepcopy(raw.get('container')), 'crafting': deepcopy(raw.get('crafting')),
                     'action_space': deepcopy(raw['actionSpace']), 'control_modes': deepcopy(raw.get('controlModes', {})) }
            nearby['body'] = body
            add('s:9', body['selected_hotbar_slot'], 'selected_hotbar_slot')
            for label, value in body['control_modes'].items():
                add(f'control:{label}', int(value), f'control:{label}')
            for family, slots in [('player_slots', body['inventory_slots']),
                                  ('window_slots', (body['container'] or {}).get('slot_state', []))]:
                for slot in slots:
                    for field in ('item_type_id', 'count', 'metadata', 'durability'):
                        add(f'{family}:{slot["slot"]}:{field}', slot.get(field), f'{family}:{slot["slot"]}:{field}')
            for label in ('container', 'crafting'):
                window = body[label]
                add(f'ui:{label}:open', int(window is not None), f'ui:{label}:open')
                if window:
                    add(f'ui:{label}:id', stable_id(window['container_id']), f'ui:{label}:id')
                    for field in ('item_type_id', 'count', 'metadata', 'durability'):
                        add(f'ui:{label}:cursor:{field}', window['cursor'].get(field), f'ui:{label}:cursor:{field}')
            for slot in body['inventory_screen']['slot_state']:
                for field in ('item_type_id', 'count', 'metadata', 'durability'):
                    add(f'player_screen:{slot["slot"]}:{field}', slot.get(field), f'player_screen:{slot["slot"]}:{field}')
            for field in ('item_type_id', 'count'):
                add(f'player_cursor:{field}', body['inventory_screen']['cursor'].get(field), f'player_cursor:{field}')
        coverage = deepcopy(raw.get('coverage', {}))
        return ObservationFrame(f'{self.individual_id}:E{sequence}', sequence, raw['timestamp'], namespace,
                                body_epoch, own, {'position': [position[a] for a in ('x', 'y', 'z')],
                                'orientation': [raw.get('orientation', {}).get(k) for k in ('yaw', 'pitch')]},
                                nearby, channels, coverage)

