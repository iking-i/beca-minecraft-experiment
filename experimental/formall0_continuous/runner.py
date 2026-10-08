"""Offline subprocess witness. Does not open Minecraft or the selected lifetime."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from individual.core import ACore
from experimental.formall0_operative.validation import initial
from .channel import TestOnlyOperativeConfig


class FakeBridge:
    pid = None
    alive = False

    def close(self):
        pass

    def call(self, *args, **kwargs):
        raise AssertionError('No body execution in Core adoption experiment')


def observation(sequence, value):
    return {'timestamp': f'2026-10-08T00:00:{sequence:02d}+00:00',
            'position': {'x': value, 'y': 64, 'z': 0},
            'health': 20, 'hunger': 20, 'inventory': [],
            'encoding': {'protocol_version': 'FORMAL-CONTINUOUS-TEST_ONLY'}}


def run(database, phase, full_history=True):
    config = TestOnlyOperativeConfig(str(Path(database).resolve()),
        origin_state=initial()[0] if phase == 'create' else None)
    core = ACore(database, FakeBridge(), initialize_lifetime=phase == 'create',
                 test_only_operative=config, full_history_enabled=full_history)
    start = core.state.to_dict()
    records = []
    journal = []
    transition = core._store.transition

    def record_commit(previous, current, event_type, payload, additional_events=()):
        transition(previous, current, event_type, payload, additional_events)
        journal[:] = deepcopy(list(additional_events))
    try:
        sequences = ((1, 0), (2, 1)) if phase == 'create' else ((3, 2), (4, 3), (5, 4))
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('No sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('No binder')), \
                patch.object(core._store, 'transition', side_effect=record_commit):
            for sequence, value in sequences:
                before = core.state.to_dict()
                core.accept_observation(observation(sequence, value))
                records.append({'input': observation(sequence, value), 'before': before,
                                'after': core.state.to_dict(), 'journal': deepcopy(journal)})
        committed = core.state.to_dict()
    finally:
        core.shutdown('TEST_ONLY_normal_process_end')
    return {'pid': os.getpid(), 'phase': phase, 'database': str(Path(database).resolve()),
            'start': start, 'records': records, 'committed': committed,
            'shutdown': core.state.to_dict(), 'closed': core._closed,
            'lease_released': core._lease._file is None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database')
    parser.add_argument('--history-off', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.database, args.phase, not args.history_off), allow_nan=False))


if __name__ == '__main__':
    main()
