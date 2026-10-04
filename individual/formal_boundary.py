"""External, persistent V0-A/V0-B conditions; no capacity-change or unlock API."""

from contextlib import closing
from copy import deepcopy
from dataclasses import asdict
import json
import math
from pathlib import Path
import sqlite3
from uuid import uuid4

BASELINE_VERSION = 'formal_l0_v0_ab_2'
RESOURCE_CAP_KEYS = ('max_core_ram_mb', 'max_bridge_ram_mb',
                     'max_total_cpu_percent', 'max_lifetime_storage_mb')
SENSOR_BOUNDS = {'blockRadius': (4, 8), 'entityRadius': (16, 64),
                 'maxBlocks': (64, 512), 'maxEntities': (64, 512)}


def sensor_caps(config_path):
    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    supplied = config.get('observation', {})
    if not isinstance(supplied, dict):
        raise ValueError('Invalid body observation configuration')
    result = {key: supplied.get(key, default) for key, (default, maximum) in SENSOR_BOUNDS.items()}
    for key, value in result.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= SENSOR_BOUNDS[key][1]:
            raise ValueError(f'Invalid body sensor capacity: {key}')
    return result


def normalize_resource_caps(value=None):
    value = {} if value is None else value
    if not isinstance(value, dict) or (value and set(value) not in (set(RESOURCE_CAP_KEYS), set(RESOURCE_CAP_KEYS) | {'body_observation_caps'})):
        raise ValueError('Resource ceilings must be empty for an unmonitored fixture or contain all four Supervisor capacities')
    for key in RESOURCE_CAP_KEYS:
        if key not in value: continue
        number = value[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number <= 0:
            raise ValueError('Invalid Supervisor resource capacity')
    result = {key: value[key] for key in RESOURCE_CAP_KEYS if key in value}
    if 'body_observation_caps' in value:
        sensor = value['body_observation_caps']
        if not isinstance(sensor, dict) or set(sensor) != set(SENSOR_BOUNDS):
            raise ValueError('Invalid body sensor capacities')
        for key, number in sensor.items():
            if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= SENSOR_BOUNDS[key][1]:
                raise ValueError('Invalid body sensor capacity')
        result['body_observation_caps'] = {key: sensor[key] for key in SENSOR_BOUNDS}
    return result


def validate_boundary(internal, caps, resource_caps=None):
    local = (internal or {}).get('l0_state', {})
    locked = local.get('locked_caps')
    if locked is None:
        if local.get('profile') == 'formal_l0':
            raise ValueError('Unsealed historical formal_l0 baseline: automatic migration is forbidden; preserve it and explicitly select separate experimental conditions')
        return None
    if local.get('baseline_version') != BASELINE_VERSION:
        raise ValueError('Incompatible formal_l0 baseline; automatic migration is forbidden')
    if locked != asdict(caps) or local.get('locked_resource_caps', {}) != (resource_caps or {}):
        raise ValueError('Configured capacities differ from locked_caps; refusing formal_l0 continuation without modifying A. Restore the locked conditions or explicitly start a separate experiment')
    return {key: deepcopy(local[key]) for key in (
        'locked_caps', 'locked_resource_caps', 'baseline_version', 'formal_condition_id')}


def boundary_for(internal, caps, resource_caps=None):
    return validate_boundary(internal, caps, resource_caps) or {
        'locked_caps': asdict(caps), 'locked_resource_caps': deepcopy(resource_caps or {}),
        'baseline_version': BASELINE_VERSION, 'formal_condition_id': f'C-{uuid4()}'}


def preflight(database, caps, resource_caps=None):
    """Before lease, EventStore/schema, interruption recovery, Session or Supervisor writes."""
    path = Path(database).resolve()
    if not path.is_file():
        return
    wal = Path(str(path) + '-wal')
    # A checkpointed file can be read without even creating WAL/SHM sidecars.
    # A live/uncheckpointed WAL must be honored: immutable mode would ignore it.
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(path.as_uri() + flags, uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='states'").fetchone():
            return
        row = db.execute('SELECT snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
        if row:
            internal = json.loads(row[0]).get('internal_state') or {}
            if caps is None:
                if internal.get('l0_state', {}).get('locked_caps') or internal.get('l0_state', {}).get('profile') == 'formal_l0':
                    raise ValueError('Formal lifetime cannot resume through legacy adaptation; use an independent debug fixture')
            else:
                validate_boundary(internal, caps, resource_caps)
