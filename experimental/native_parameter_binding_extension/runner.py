"""Synthetic typed receipt premises; no past/future command or body call."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.native_body_operands.runner import observation
from experimental.native_body_operands.engine import unit_identity
from experimental.typed_operative_connection.engine import value_ref, KEY as GRAPH
from experimental.typed_operative_connection.runner import record
from .channel import BindingCore, BindingConfig


def create(db, history=True, origin=None, origin_edges=None):
    return BindingCore(db, FakeBridge(), config=BindingConfig(str(db)),
        initialize_lifetime=True, origin=origin or initial()[0], origin_edges=origin_edges,
        full_history_enabled=history)


def reopen(db, history=True):
    return BindingCore(db, FakeBridge(), config=BindingConfig(str(db)), full_history_enabled=history)


def sample(seq, value):
    raw = observation(seq, value, codes=(8,))
    # Unchanged sensor materials make values 0/1/2 available in both histories.
    raw.update(health=1, hunger=2)
    return raw


def slot_ref(raw, name='yaw_delta'):
    # Fixture identifies an external factual premise; engine never reads names.
    declaration = raw['actionSpace'][0]
    domain = unit_identity({'type': 'ParameterDomain', 'schema': declaration['parameter_schema']['properties'][name]})
    return unit_identity({'type': 'ParameterSlot',
        'port': unit_identity({'type': 'NativePort', 'catalog_version': 2, 'code': declaration['code']}),
        'name': name, 'domain': domain, 'required': True})


def receipt(raw, value=0, name='yaw_delta', execution_id='synthetic-execution-1'):
    return {'execution_id': execution_id, 'catalog_version': 2, 'code': raw['actionSpace'][0]['code'],
            'status': 'executed', 'source': 'EXTERNAL_SYNTHETIC_TYPED_RECEIPT',
            'assignments': [{'slot_ref': slot_ref(raw, name), 'operand_ref': value_ref(value)}]}


def setup(core, successor=1):
    first = sample(1, 0)
    second = sample(2, successor)
    second['typedExecutionReceipts'] = [receipt(second)]
    return [record(core, first), record(core, second)]


def run(db, phase, history=True):
    core = create(db, history) if phase == 'create' else reopen(db, history)
    start = core.state.to_dict()
    try:
        rows = setup(core) + [record(core, sample(3, 1))] if phase == 'create' else [record(core, sample(4, 1)), record(core, sample(5, 1))]
    finally:
        core.shutdown('TEST_ONLY_binding_extension_close')
    return {'pid': os.getpid(), 'start': start, 'records': rows,
            'shutdown': core.state.to_dict(), 'lease_released': core._lease._file is None}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['create', 'resume']); p.add_argument('database')
    p.add_argument('--history-off', action='store_true')
    args = p.parse_args()
    print(json.dumps(run(Path(args.database), args.phase, not args.history_off)))
