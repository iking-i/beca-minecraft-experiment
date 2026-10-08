"""Synthetic declared carrier data, independent A/DB, real subprocess lifecycle."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from individual.action_space import DEFINITIONS, CATALOG_DATA
from experimental.formall0_continuous.runner import FakeBridge, observation as plain_observation
from experimental.formall0_operative.validation import initial
from experimental.operative_content.runner import capture
from .channel import NativeConfig, NativeCore


def observation(sequence, value, codes=(0, 16, 13), with_reference=True):
    raw = plain_observation(sequence, value)
    raw['actionSpace'] = []
    for code in codes:
        d = DEFINITIONS[code]
        raw['actionSpace'].append({'code': code, 'action_id': d['action_id'],
            'category': 'BODY_CAPABILITY',
            'parameter_schema': {'type': 'object', 'properties': deepcopy(d['parameters']),
                'required': sorted(k for k, v in d['parameters'].items() if not v.get('optional')),
                'additionalProperties': False},
            'environment_requirement_codes': [CATALOG_DATA['requirement_codes'][r]
                for r in d['environment_requirements']], 'currently_available': True,
            'formal_enabled': d.get('formal_enabled') is not False})
    raw.update(inventorySlots=[], inventoryScreen={'slot_state': [], 'cursor': {}}, selectedHotbarSlot=None)
    if with_reference:
        raw['nearbyEntities'] = [{'id': 73, 'type_id': 1,
            'position': {'x': value + 1, 'y': 64, 'z': 0}, 'entity_ref': 'opaque-observed-entity'}]
    return raw


def create(database, history=True, origin=None):
    return NativeCore(database, FakeBridge(), initialize_lifetime=True,
        full_history_enabled=history,
        config=NativeConfig(str(database), origin_state=origin or initial()[0]))


def reopen(database, history=True):
    return NativeCore(database, FakeBridge(), config=NativeConfig(str(database)),
                      full_history_enabled=history)


def run(database, phase, history=True):
    core = create(database, history) if phase == 'create' else reopen(database, history)
    start, records = core.state.to_dict(), []
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('No sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('No binder')):
            for sequence, value in (((1, 0), (2, 1), (3, 2)) if phase == 'create' else ((4, 3), (5, 4))):
                before = core.state.to_dict()
                core.accept_observation(observation(sequence, value))
                records.append({'before': before, 'after': core.state.to_dict()})
    finally:
        core.shutdown('TEST_ONLY_native_operands_normal_close')
    return {'pid': os.getpid(), 'phase': phase, 'start': start, 'records': records,
            'shutdown': core.state.to_dict(), 'lease_released': core._lease._file is None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database')
    parser.add_argument('--history-off', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(Path(args.database), args.phase, not args.history_off), allow_nan=False))
