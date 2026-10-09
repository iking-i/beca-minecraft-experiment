"""Separate-process RSS/read/time observation; explicitly offline only."""
import gc
import json
from pathlib import Path
import sqlite3
import threading
import time
import psutil

from copy import deepcopy
from individual.formal_l0 import FormalLimits
from individual.observation import ObservationFrame
from .comparison import SAVED, fixture_store, compact, pending
from .store import using


def measure(mode, directory):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    if mode == 'old':
        from experimental.ordinary_pair_usage.engine import UsageRealEngine as Engine
    elif mode == 'new':
        from .engine import UsageRealEngine as Engine
    else:
        raise ValueError('Unknown measurement mode')
    process = psutil.Process(); peak = [process.memory_info().rss]
    stopped = threading.Event()
    def sample():
        while not stopped.wait(.01):
            peak[0] = max(peak[0], process.memory_info().rss)
    thread = threading.Thread(target=sample, daemon=True); thread.start()
    db = sqlite3.connect(directory / 'sources.db') if mode=='new' else None
    rows, store = [], None
    try:
        initial_rss = process.memory_info().rss
        for n in range(1, 33):
            record = json.loads((SAVED / 'frames' / f'E{n:02d}.json').read_text(encoding='utf-8'))
            current = record['state_before']['internal_state']
            version = record['state_before']['state_version'] + 1
            frame = ObservationFrame(**record['state_after']['observation_frame'])
            inputs = pending(record)
            if mode=='new':
                if store is None:
                    store = fixture_store(db, record['state_before']['individual_id'])
                current = compact(current, store); store.reset_reads()
            del record
            gc.collect()
            engine = Engine(FormalLimits(**current['l0_state']['locked_caps']), current['l0_state']['locked_resource_caps'])
            before = process.memory_info().rss; start = time.perf_counter()
            if mode=='new':
                with using(store):
                    result = engine.advance(current, frame, version, inputs)
                with db:
                    db.execute('BEGIN IMMEDIATE'); store.flush(result[0].l0_state['observation_interface_references_test_only']['observations'])
                store.published()
            else:
                result = engine.advance(current, frame, version, inputs)
            rows.append({'frame':n, 'seconds':time.perf_counter()-start,
                'rss_before':before, 'rss_after':process.memory_info().rss,
                'source_body_reads':store.reads if store else None,
                'source_body_bytes':store.read_bytes if store else None,
                'decoded_source_cache_count':len(store.cache) if store else None})
            del result, engine, current, frame, inputs
            gc.collect()
        final = process.memory_info().rss
    finally:
        stopped.set(); thread.join()
        if db: db.close()
    result = {'mode':mode, 'scope':'OFFLINE_SAVED_CHECKPOINTS_SEPARATE_PROCESS_NOT_LIVE',
        'pid':process.pid, 'rss_initial':initial_rss, 'rss_peak_sampled_10ms':peak[0],
        'rss_final':final, 'total_advance_and_commit_seconds':sum(r['seconds'] for r in rows),
        'rows':rows, 'full_history_scanning_in_fixture_loader_not_runtime':True,
        'unlimited_running_or_memory_bound_proven':False}
    (directory / 'MEASUREMENT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    import sys
    measure(*sys.argv[1:])
