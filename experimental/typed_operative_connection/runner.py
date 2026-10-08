"""Synthetic Core observations and real subprocess restart, no body output."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.native_body_operands.runner import observation
from experimental.operative_content.runner import capture
from .channel import ConnectionConfig, ConnectionCore
from .engine import KEY, connection


def create(database, history=True, origin=None, origin_edges=None):
    origin = origin or initial()[0]
    edges = origin_edges if origin_edges is not None else (
        connection('U-origin-0', 'U-origin-1'),)
    return ConnectionCore(database, FakeBridge(), initialize_lifetime=True,
        full_history_enabled=history,
        config=ConnectionConfig(str(database), origin, tuple(edges)))


def reopen(database, history=True):
    return ConnectionCore(database, FakeBridge(), full_history_enabled=history,
                          config=ConnectionConfig(str(database)))


def sample(sequence, value):
    return observation(sequence, value, codes=(16,))


def record(core, raw):
    before, journal = core.state.to_dict(), []
    transition = core._store.transition
    def commit(*args, **kwargs):
        result = transition(*args, **kwargs)
        journal.extend(deepcopy(list(args[4] if len(args) > 4 else kwargs.get('additional_events', ()))))
        return result
    with patch.object(core._store, 'transition', side_effect=commit):
        core.accept_observation(raw)
    return {'input': deepcopy(raw), 'before': before, 'after': core.state.to_dict(),
            'journal': journal}


def setup(core, values=(0, 1)):
    records = []
    for sequence, value in enumerate(values, 1):
        records.append(record(core, sample(sequence, value)))
    return records


def run(database, phase, history=True):
    core = create(database, history) if phase == 'create' else reopen(database, history)
    start = core.state.to_dict()
    records = []
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('binder')):
            values = ((1, 0), (2, 1), (3, 1)) if phase == 'create' else ((4, 1), (5, 1))
            for sequence, value in values:
                records.append(record(core, sample(sequence, value)))
    finally:
        core.shutdown('TEST_ONLY_typed_connection_normal_close')
    return {'pid': os.getpid(), 'start': start, 'records': records,
            'shutdown': core.state.to_dict(), 'lease_released': core._lease._file is None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database')
    parser.add_argument('--history-off', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(Path(args.database), args.phase, not args.history_off)))
