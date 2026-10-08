"""Offline subprocess and paired ordinary-Core measurement entry points."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from experimental.formall0_continuous.runner import FakeBridge, observation
from experimental.formall0_operative.validation import initial
from .channel import ContentConfig, ContentCore
from .engine import KEY


def create(database, history=True, names=('opaque:origin', 'opaque:operand')):
    return ContentCore(database, FakeBridge(), initialize_lifetime=True,
        full_history_enabled=history,
        config=ContentConfig(str(database), origin_state=initial(names=names)[0]))


def reopen(database, history=True):
    return ContentCore(database, FakeBridge(), full_history_enabled=history,
                       config=ContentConfig(str(database)))


class Captured(Exception):
    pass


def capture(core, raw, transform=lambda state: state):
    """Run real Core/engine; stop before commit. Canonical state never changes."""
    measured = {}
    advance = core._engine.advance
    def execute(state, frame, version, pending):
        measured['before'] = transform(deepcopy(state))
        return advance(measured['before'], frame, version, pending)
    def commit(raw, fields, sequence, internal, frame, journal):
        measured['after'] = internal.to_dict()
        measured['journal'] = deepcopy(journal)
        measured['partial'] = next(p for k, p in journal if k == 'RECURSIVE_PARTIAL_OUTPUT')
        raise Captured()
    with patch.object(core._engine, 'advance', side_effect=execute), \
            patch.object(core, '_commit_observation', side_effect=commit):
        try:
            core.accept_observation(raw)
        except Captured:
            return measured
    raise AssertionError('Measurement never reached ordinary commit boundary')


def run(database, phase, history=True):
    core = create(database, history) if phase == 'create' else reopen(database, history)
    start = core.state.to_dict()
    records = []
    transition = core._store.transition
    journal = []
    def committed(*args, **kwargs):
        transition(*args, **kwargs)
        journal[:] = deepcopy(list(args[4] if len(args) > 4 else kwargs.get('additional_events', ())))
    try:
        inputs = ((1, 0), (2, 1), (3, 2)) if phase == 'create' else ((4, 3), (5, 4))
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('No sampler')), \
                patch('individual.core.bind_parameters', side_effect=AssertionError('No binder')), \
                patch.object(core._store, 'transition', side_effect=committed):
            for sequence, value in inputs:
                before = core.state.to_dict()
                core.accept_observation(observation(sequence, value))
                records.append({'input': observation(sequence, value), 'before': before,
                    'after': core.state.to_dict(), 'journal': deepcopy(journal)})
    finally:
        core.shutdown('TEST_ONLY_content_normal_close')
    return {'pid': os.getpid(), 'phase': phase, 'start': start, 'records': records,
        'shutdown': core.state.to_dict(), 'lease_released': core._lease._file is None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database')
    parser.add_argument('--history-off', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(Path(args.database), args.phase, not args.history_off), allow_nan=False))
