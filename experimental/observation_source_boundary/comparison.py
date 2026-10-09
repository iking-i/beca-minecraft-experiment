"""Explicit offline saved-input comparison. Never opens the original DB writable.

Saved checkpoints are comparison fixtures, not a live A or reconstructed PASS.
UUID coupling below controls irrelevant fresh journal identities only in this
diagnostic; neither interpreter's execution/selection rules are mocked.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from unittest.mock import patch
from uuid import UUID

from individual.formal_l0 import FormalLimits
from individual.observation import ObservationFrame
from experimental.ordinary_pair_usage.engine import UsageRealEngine as FrozenEngine
from .engine import UsageRealEngine as BoundaryEngine
from .reference.references import KEY, VERSION
from .store import SourceStore, using

SAVED = Path('.test-tmp/continuous-capacity-live-58160-20261009-run2')


def compact(internal, store):
    result = deepcopy(internal)
    pool = result['l0_state'][KEY]
    pool['version'] = VERSION
    pool['sources'] = {parent: source['frame_id'] for parent, source in pool['sources'].items()}
    pool['observations'] = store.descriptor()
    del pool['observation_meta']
    return result


def expanded(internal, store):
    result = deepcopy(internal)
    pool = result['l0_state'][KEY]
    from experimental.observation_interface_references.reference.references import VERSION as OLD
    pool['version'] = OLD
    pool['sources'] = {parent: store.get(frame) for parent, frame in pool['sources'].items()}
    frames = [r[0] for r in store.db.execute('SELECT frame_id FROM os_sources ORDER BY ordinal')]
    if store.pending:
        frames.append(store.pending['source']['frame_id'])
    pool['observations'] = {frame: store.get(frame) for frame in frames}
    pool['observation_meta'] = {frame: store.meta(frame) for frame in frames}
    return result


def pending(record):
    for event in record['events']:
        if event['event_type'] == 'EXPERIENCE_FORMED':
            value = event['payload']
            latest = record['state_before']['latest_action']
            result = []
            for aid, parameters, status in zip(value['action_ids'], value['action_parameters'], value['action_statuses']):
                assert latest['action_id'] == aid
                result.append({'action_id':aid, 'action_code':latest['action_code'], 'parameters':parameters, 'status':status})
            return result
    return []


def fixture_store(db, iid):
    db.execute('CREATE TABLE experiment(singleton INTEGER PRIMARY KEY,individual_id TEXT)')
    db.execute('INSERT INTO experiment VALUES(1,?)', (iid,))
    db.commit()
    return SourceStore(db, install=True)


def uuids():
    for n in range(1, 10000):
        yield UUID(int=n)


def compare_saved(output_directory, saved=SAVED):
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=False)
    rows, preservation = [], {}
    db = sqlite3.connect(directory / 'sources.db')
    try:
        store = None
        for n in range(1, 33):
            path = saved / 'frames' / f'E{n:02d}.json'
            raw = path.read_bytes(); preservation[str(path)] = hashlib.sha256(raw).hexdigest()
            record = json.loads(raw)
            state = record['state_before']; before = state['internal_state']
            frame = ObservationFrame(**record['state_after']['observation_frame'])
            if store is None:
                store = fixture_store(db, state['individual_id'])
            # Each source came from the preceding paired transition, never from
            # the result under test. No historical loading inside advance.
            current = compact(before, store)
            l0 = before['l0_state']; caps = FormalLimits(**l0['locked_caps'])
            inputs = pending(record)
            start = time.perf_counter()
            with patch('individual.formal_l0.uuid4', side_effect=uuids()), patch('experimental.formall0_operative.engine.uuid4', side_effect=uuids()):
                old, of, oj = FrozenEngine(caps, l0['locked_resource_caps']).advance(deepcopy(before), deepcopy(frame), state['state_version'] + 1, inputs)
            old_seconds = time.perf_counter() - start
            store.reset_reads(); start = time.perf_counter()
            with using(store), patch('individual.formal_l0.uuid4', side_effect=uuids()), patch('experimental.formall0_operative.engine.uuid4', side_effect=uuids()):
                new, nf, nj = BoundaryEngine(caps, l0['locked_resource_caps']).advance(current, deepcopy(frame), state['state_version'] + 1, inputs)
            new_seconds = time.perf_counter() - start
            metrics = {'source_body_reads': store.reads, 'source_body_bytes': store.read_bytes, 'exact_index_reads': store.index_reads}
            same = expanded(new.to_dict(), store) == old.to_dict()
            if not same:
                (directory / f'mismatch-E{n}.json').write_text(json.dumps({'old':old.to_dict(), 'new_expanded':expanded(new.to_dict(), store)}, ensure_ascii=False, indent=2), encoding='utf-8')
            assert same and of == nf and oj == nj, f'Actual interpreter difference at E{n}'
            with db:
                db.execute('BEGIN IMMEDIATE')
                store.flush(new.l0_state[KEY]['observations'])
            store.published()
            old_size = len(json.dumps(record['state_after']['internal_state'], ensure_ascii=False, separators=(',', ':')).encode())
            compact_saved = compact(record['state_after']['internal_state'], store)
            new_size = len(json.dumps(compact_saved, ensure_ascii=False, separators=(',', ':')).encode())
            rows.append({'frame':n, 'recursive_state_equal_after_expansion':same,
                'journal_equal':oj == nj, 'frame_equal':of == nf,
                'old_actual_snapshot_bytes':old_size, 'new_equivalent_snapshot_bytes':new_size,
                'old_seconds':old_seconds, 'new_seconds':new_seconds, **metrics,
                'source_count':store.header['count'], 'units':len(new.units),
                'pairs':sum(x['type']=='Pair' for x in new.l0_state[KEY]['nodes'].values()),
                'channels':len(frame.numeric_channels), 'objects':len(new.l0_state[KEY]['current_source']['references']),
                'capabilities':len(new.l0_state[KEY]['current_source']['declarations'])})
        audit = store.audit()
        for path, expected in preservation.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
        result = {'scope':'OFFLINE_SAVED_REAL_DATA_NOT_NEW_LIVE', 'classification':'PASS',
            'rows':rows, 'source_audit':audit, 'input_hashes':preservation,
            'original_database_opened':False, 'validation_detection_semantics_identical':False}
        (directory / 'COMPARISON.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return result
    finally:
        db.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('output')
    args = parser.parse_args()
    result = compare_saved(args.output)
    print(json.dumps({'classification': result['classification'], 'frames':len(result['rows']), 'first':result['rows'][0], 'last':result['rows'][-1]}))
