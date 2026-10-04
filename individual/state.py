from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import math


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


@dataclass(frozen=True)
class AState:
    individual_id: str
    state_version: int
    started_at: str
    last_update_at: str
    latest_observation: dict | None = None
    latest_action: dict | None = None
    health: float | None = None
    hunger: float | None = None
    position: dict | None = None
    inventory_summary: list = field(default_factory=list)
    environment_sequence: int = 0
    status: str = 'starting'
    continuity_required: bool = True
    observation_frame: dict | None = None
    internal_state: dict = field(default_factory=dict)
    session_id: str | None = None
    carrier_epoch: int = 0

    def to_dict(self):
        return asdict(self)

    def detached(self):
        return AState(**self.to_dict())


def observation_fields(observation):
    if not isinstance(observation, dict):
        raise ValueError('Observation must be an object')
    obs = deepcopy(observation)
    if not isinstance(obs.get('timestamp'), str) or not obs['timestamp']:
        raise ValueError('Observation needs a timestamp')
    position = obs.get('position')
    if not isinstance(position, dict):
        raise ValueError('Observation needs a position')
    for axis in ('x', 'y', 'z'):
        value = position.get(axis)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Position must contain finite numeric x/y/z')
    for key in ('health', 'hunger'):
        if key not in obs:
            raise ValueError(f'Observation needs {key}')
        value = obs[key]
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            raise ValueError(f'Invalid {key}')
    inventory = obs.get('inventory')
    if not isinstance(inventory, list):
        raise ValueError('Observation needs an inventory list')
    counts = {}
    for item in inventory:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str):
            raise ValueError('Invalid inventory item')
        count = item.get('count')
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('Invalid inventory count')
        counts[item['name']] = counts.get(item['name'], 0) + count
    return dict(latest_observation=obs, health=obs['health'], hunger=obs['hunger'],
                position=deepcopy(position),
                inventory_summary=[{'name': name, 'count': count} for name, count in sorted(counts.items())])

