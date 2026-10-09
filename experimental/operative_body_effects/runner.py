"""Synthetic history and offline receipt; never connects Minecraft."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample, supplied_receipt
from .channel import EffectCore, EffectConfig


class OfflineBridge(FakeBridge):
    def __init__(self):
        super().__init__()
        self.calls = []

    def call(self, method, args=None):
        if method != 'perform':
            raise AssertionError('Only mechanical mock perform is available')
        self.calls.append(deepcopy(args))
        return {'code': args['code'], 'parameters': deepcopy(args['parameters']),
                'started_at': 'offline:start', 'finished_at': 'offline:end',
                'result': {'input_sent': 1, 'effect_acknowledged': 0},
                'effect_attribution': 'temporal_observation_only'}


def run(database, phase):
    bridge = OfflineBridge()
    config = EffectConfig(str(database), origin_state=initial()[0] if phase == 'create' else None)
    core = EffectCore(database, bridge, config=config, initialize_lifetime=phase == 'create')
    start = core.state.to_dict()
    records = []
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            for sequence, value in (((1, 0), (2, 1), (3, 0), (4, 1), (5, 1))
                                    if phase == 'create' else ((6, 1), (7, 1))):
                raw = sample(sequence, value)
                if phase == 'create' and sequence == 2:
                    raw['typedExecutionReceipts'] = [supplied_receipt(core, raw)]
                before = core.state.to_dict()
                core.accept_observation(raw)
                records.append({'input': raw, 'before': before, 'after': core.state.to_dict()})
            end = core.state.to_dict()
    finally:
        core.shutdown('TEST_ONLY_operative_effect_close')
    return {'pid': os.getpid(), 'start': start, 'end': end, 'records': records,
            'calls': bridge.calls, 'minecraft_run': False, 'receipt_kind': 'OFFLINE_MOCK'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database')
    args = parser.parse_args()
    print(json.dumps(run(Path(args.database), args.phase), ensure_ascii=False, allow_nan=False))
