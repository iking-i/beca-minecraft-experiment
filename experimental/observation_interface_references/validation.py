"""Offline process witness only; no Minecraft or selected lifetime access."""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch

from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from .real.channel import RealEffectCore
from .effects.channel import EffectConfig
from .effects.engine import KEY


class ReceiptBridge(FakeBridge):
    def __init__(self):
        self.calls = []
        self.core = None

    def call(self, method, args=None):
        assert method == 'perform'
        self.calls.append(deepcopy(args))
        start = self.core.state.observation_frame['timestamp']
        end = (datetime.fromisoformat(start) + timedelta(milliseconds=10)).isoformat()
        return {'code': args['code'], 'parameters': deepcopy(args['parameters']),
                'started_at': start, 'finished_at': end, 'before': {}, 'after': {},
                'result': {'input_sent': 1, 'effect_acknowledged': 0},
                'effect_attribution': 'temporal_observation_only'}


def run(path, phase):
    bridge = ReceiptBridge()
    c = RealEffectCore(path, bridge, initialize_lifetime=phase == 'create',
        config=EffectConfig(str(path), origin_state=initial()[0] if phase == 'create' else None))
    bridge.core = c
    restored = deepcopy(c.state.internal_state['l0_state'][KEY]['routes'])
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            for seq, value in (((1, 0), (2, 1), (3, 0))
                               if phase == 'create' else ((4, 1), (5, 1))):
                c.accept_observation(sample(seq, value))
                if phase == 'create' and seq == 1:
                    c.bootstrap_once()
        return {'pid': os.getpid(), 'individual_id': c.state.individual_id,
                'state_version': c.state.state_version,
                'routes': deepcopy(c.state.internal_state['l0_state'][KEY]['routes']),
                'restored_routes': restored, 'calls': bridge.calls,
                'authoritative': c._store.latest_state().to_dict() == c.state.to_dict(),
                'reused_content': c.state.internal_state['l0_state'].get('body_reference_execution', {}).get('reused_content', []),
                'minecraft_run': False, 'source': 'OFFLINE_RECEIPT_ADAPTER_TEST'}
    finally:
        c.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.database, args.phase), ensure_ascii=False))
