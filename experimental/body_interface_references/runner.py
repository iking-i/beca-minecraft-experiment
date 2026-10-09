"""New TEST_ONLY DB, synthetic input, real Core transitions and process restart."""
import argparse
import json
import os
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch

from individual.action_space import DEFINITIONS
from individual.internal_state import InternalState
from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.native_body_operands.runner import observation
from .channel import ReferenceCore, ReferenceConfig
from .references import KEY, body_ref, observed_catalog
from .engine import value_ref


def create(database):
    return ReferenceCore(database, FakeBridge(), config=ReferenceConfig(str(database), origin_state=initial()[0]),
                         initialize_lifetime=True)


def reopen(database):
    return ReferenceCore(database, FakeBridge(), config=ReferenceConfig(str(database)))


def sample(sequence, value):
    raw = observation(sequence, value, codes=tuple(DEFINITIONS))
    raw.update(health=1, hunger=2)
    return raw


def supplied_receipt(core, raw, code=16, name='slot', value=0):
    frame = core._encoder.encode(raw, core.state.environment_sequence + 1, core._body_epoch)
    catalog = observed_catalog(frame)
    saved = core.state.internal_state['l0_state'][KEY]['catalog']
    if saved is not None:
        catalog['body_epoch'] = saved['body_epoch']
    return {'execution_id': 'synthetic-reference-premise', 'catalog_version': 2,
            'code': code, 'status': 'executed', 'source': 'EXTERNAL_SYNTHETIC_TYPED_RECEIPT',
            'assignments': [{'slot_ref': body_ref(catalog, 'slot', code, name),
                             'operand_ref': value_ref(value)}]}


def setup(core):
    rows = []
    for seq, value in ((1, 0), (2, 1), (3, 1)):
        raw = sample(seq, value)
        if seq == 2:
            raw['typedExecutionReceipts'] = [supplied_receipt(core, raw)]
        before = core.state.to_dict()
        core.accept_observation(raw)
        rows.append({'input': raw, 'before': before, 'after': core.state.to_dict()})
    return rows


def binding_values(internal, executed_only=False):
    """Audit only: reports formed slot endpoints; never supplies engine answers."""
    from .references import resolve
    pool = internal.l0_state[KEY]
    used = internal.l0_state.get('body_reference_execution', {}).get('connections', [])
    return sorted({resolve(internal, e['target'])['value'] for ref, e in pool['edges'].items()
                   if not executed_only or ref in used
                   if e['source'].get('kind') == 'slot'})


def run(database, phase):
    core = create(database) if phase == 'create' else reopen(database)
    start = core.state.to_dict()
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler forbidden')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder forbidden')):
            if phase == 'create':
                rows = setup(core)
            else:
                rows = []
                # The frozen Core starts a new sampling epoch on restart. Its
                # first observation establishes that epoch; the next ordinary
                # observation executes recursion, without bridging the gap.
                for seq in (4, 5):
                    core.accept_observation(sample(seq, 1))
                    rows.append({'after': core.state.to_dict()})
            end = core.state.to_dict()
    finally:
        core.shutdown('TEST_ONLY_body_reference_close')
    return {'phase': phase, 'pid': os.getpid(), 'start': start, 'records': rows, 'end': end,
            'shutdown': core.state.to_dict(), 'body_execution': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['create', 'resume'])
    parser.add_argument('database')
    args = parser.parse_args()
    print(json.dumps(run(Path(args.database), args.phase), ensure_ascii=False))
