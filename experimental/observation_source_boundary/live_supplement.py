"""External bounded live recorder; delegates all state/formation to BoundaryCore.

Two separate worker processes share one fresh database. No bootstrap, replay,
respawn, sampler, binder, or source reconstruction. Logs are external evidence.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from unittest.mock import patch
from uuid import uuid4

import psutil
from individual.bridge import MinecraftBridge
from individual.formal_l0 import digest
from individual.internal_state import InternalState
from experimental.formall0_operative.validation import initial
from experimental.continuous_capacity.recorder import inventory, delta
from .effects.channel import EffectConfig
from .lifecycle import BoundaryCore
from .reference.references import KEY, fact_ref, resolve
from .store import SourceStore, using

ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


class ObservedCore(BoundaryCore):
    """Read-only post-commit event observer, including when audit history is OFF."""
    def __init__(self, *args, record, **kwargs):
        self.record = record
        self.observed_events = []
        super().__init__(*args, **kwargs)

    def _transition(self, event_type, payload, additional_events=(), **changes):
        state = super()._transition(event_type, payload, additional_events, **changes)
        for kind, body in [(event_type, payload), *additional_events]:
            event = {'event_type': kind, 'payload': deepcopy(body),
                     'state_version': state.state_version, 'timestamp': now(),
                     'individual_id': state.individual_id, 'session_id': state.session_id,
                     'evidence_source': 'EXTERNAL_OBSERVER_OF_SUCCESSFUL_TRANSITION'}
            self.observed_events.append(event)
            self.record.write(json.dumps(event, ensure_ascii=False) + '\n')
            self.record.flush()
        return state


def worker(directory, phase, port):
    directory = Path(directory).resolve()
    out = directory / "ON_SUPPLEMENT"
    out.mkdir(exist_ok=False)
    database = directory / 'individual.db'
    report = {'phase': phase, 'full_history': phase == 'ON', 'pid': os.getpid(),
              'started_at': now(), 'budget': 8, 'records': [], 'classification': 'NOT_TESTABLE',
              'bootstrap': False, 'replay': False, 'sampler_calls': 0, 'binder_calls': 0}
    core = None
    process = psutil.Process()
    stop = threading.Event()
    peak = [process.memory_info().rss]
    report['rss_initial'] = peak[0]
    with (out / 'rss.jsonl').open('x', encoding='utf-8') as rss, \
         (out / 'transitions.jsonl').open('x', encoding='utf-8') as events, \
         (out / 'transport.jsonl').open('x', encoding='utf-8') as transport, \
         (out / 'body.log').open('x', encoding='utf-8') as body_log:
        def sample():
            while not stop.is_set():
                value = process.memory_info().rss
                peak[0] = max(peak[0], value)
                rss.write(json.dumps({'timestamp': now(), 'rss': value}) + '\n')
                rss.flush()
                stop.wait(.05)
        thread = threading.Thread(target=sample, daemon=True)
        thread.start()
        bridge = MinecraftBridge(directory / 'body-config.json', port=port,
            log=lambda line: (body_log.write(line + '\n'), body_log.flush()))
        original_call = bridge.call
        def call(method, args=None, timeout=None):
            transport.write(json.dumps({'timestamp': now(), 'request': method, 'args': args}) + '\n')
            transport.flush()
            result = original_call(method, args, timeout)
            transport.write(json.dumps({'timestamp': now(), 'response': method, 'result': result}, ensure_ascii=False) + '\n')
            transport.flush()
            return result
        bridge.call = call
        def forbidden(name):
            def reject(*args, **kwargs):
                report[name + '_calls'] += 1
                raise AssertionError(name + ' forbidden in source storage validation')
            return reject
        try:
            core = ObservedCore(database, bridge, record=events,
                config=EffectConfig(str(database), origin_state=initial()[0] if phase == 'OFF' else None),
                initialize_lifetime=phase == 'OFF', full_history_enabled=phase == 'ON')
            report['restored_state'] = core.state.to_dict()
            report.update(individual_id=core.state.individual_id, session_id=core.state.session_id,
                          restored_source_count=core._source_store.header['count'])
            store = core._source_store
            original_get = store.get
            accesses = []
            def get(frame):
                source = original_get(frame)
                accesses.append({'frame_id': frame, 'digest': digest(source)})
                return source
            store.get = get
            with patch('individual.core.select_uniform_action', side_effect=forbidden('sampler')), \
                 patch('individual.core.bind_parameters', side_effect=forbidden('binder')):
                core.start()
                deadline = time.monotonic() + 30
                def drain():
                    for event in bridge.drain_events():
                        if event['kind'] == 'lifecycle':
                            core.accept_bridge_status(event['status'], source=event)
                            if event['status'].get('state') == 'dead':
                                raise RuntimeError('Real body death; preserve event, no respawn')
                        elif event['kind'] in ('exited', 'transport_error'):
                            raise RuntimeError('Carrier interrupted; no reconnect')
                while True:
                    status = bridge.call('status', timeout=5)
                    drain()
                    if status.get('connected'):
                        break
                    if status.get('lastError') or time.monotonic() >= deadline:
                        raise RuntimeError('Body unavailable: ' + str(status))
                    time.sleep(.2)
                report['bridge_pid'] = bridge.pid
                for index in range(1, 9):
                    if index > 1:
                        time.sleep(2)
                    drain()
                    before = core.state.to_dict()
                    raw = bridge.call('observe', timeout=10)
                    frame_path = out / ('frame-%02d.json' % index)
                    record = {'raw_observation': raw, 'state_before': before}
                    write(frame_path, record)
                    first_event = len(core.observed_events)
                    accesses.clear()
                    started = time.perf_counter()
                    core.accept_observation(raw)
                    elapsed = time.perf_counter() - started
                    after = core.state.to_dict()
                    runtime_accesses = deepcopy(accesses)
                    counters = {'body_reads': store.reads, 'body_bytes_read': store.read_bytes,
                                'index_reads': store.index_reads,
                                'source_accesses': runtime_accesses}
                    frame_events = deepcopy(core.observed_events[first_event:])
                    inv = inventory(after)
                    inv['saved_external_sources'] = store.header['count']
                    source = after['internal_state']['l0_state'][KEY]['current_source']
                    row = store.db.execute('SELECT count(*),sum(length(CAST(body AS BLOB))) FROM os_sources').fetchone()
                    matches = core._store.latest_state().to_dict() == after
                    if not matches:
                        raise RuntimeError('Authoritative Current State mismatch')
                    historical = []
                    for item in runtime_accesses:
                        if item['frame_id'] != source['frame_id'] and item not in historical:
                            historical.append(item)
                    # Separate external exact-reference probe, not A's recursive input.
                    probe = None
                    first_source = store.db.execute('SELECT frame_id FROM os_sources ORDER BY ordinal LIMIT 1').fetchone()[0]
                    with using(store):
                        old = store.get(first_source)
                        channel = next(iter(old['numeric_channels']))
                        internal = InternalState.from_dict(after['internal_state'])
                        address = fact_ref(internal, first_source, channel)
                        probe = {'address': address, 'resolved': resolve(internal, address),
                                 'scope': 'EXTERNAL_READ_ONLY_REFERENCE_PROBE_NOT_RECURSIVE_INPUT'}
                    summary = {'index': index, 'frame_id': source['frame_id'],
                        'individual_id': after['individual_id'], 'session_id': after['session_id'],
                        'state_version': after['state_version'], 'body_epoch': source['body_epoch'],
                        'inventory': inv, 'source_count': row[0], 'source_body_bytes': row[1],
                        'current_state_json_bytes': len(json.dumps(after, ensure_ascii=False, separators=(',', ':')).encode()),
                        'channels': len(source['numeric_channels']), 'objects': len(source['references']),
                        'capabilities': len(source['declarations']), 'runtime_source_reads': counters,
                        'historical_sources_accessed_by_runtime': historical,
                        'reference_probe': probe, 'authoritative_matches': matches,
                        'processing_seconds': elapsed, 'rss': process.memory_info().rss,
                        'event_counts': dict(Counter(e['event_type'] for e in frame_events)),
                        'delta': delta(before, after, frame_events)}
                    record.update(state_after=after, events=frame_events, measurement=summary)
                    write(frame_path, record)
                    report['records'].append(summary)
                    write(out / 'REPORT.json', report)
                    print(json.dumps({'phase': phase, 'frame': source['frame_id'],
                        'version': after['state_version'], 'capacity': inv['total_unit_charge'],
                        'reads': counters['body_reads']}), flush=True)
                    if any(e['event_type'] in ('ACTION_FAILED',) for e in frame_events):
                        raise RuntimeError('Real temporal/action interruption; preserve without repair')
                report['classification'] = 'BUDGET_COMPLETED'
        except Exception as error:
            report['error'] = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
            report['classification'] = 'RESOURCE_LIMIT' if type(error).__name__ == 'ContentCapacityError' else ('NOT_TESTABLE' if not report['records'] else 'PARTIAL')
        finally:
            if core is not None:
                try:
                    report['final_before_shutdown'] = core.state.to_dict()
                    with using(core._source_store):
                        report['explicit_source_audit'] = core._source_store.audit()
                    core.shutdown('EXTERNAL_SOURCE_STORAGE_8_FRAME_BUDGET_OR_BLOCKER')
                    report['shutdown_state'] = core.state.to_dict()
                    report['shutdown_completed'] = True
                except Exception:
                    report['shutdown_error'] = traceback.format_exc()
                    bridge.close()
            else:
                bridge.close()
            stop.set()
            thread.join()
            report.update(ended_at=now(), rss_peak_sampled_50ms=peak[0],
                          rss_final=process.memory_info().rss,
                          event_counts=dict(Counter(e['event_type'] for e in core.observed_events)) if core else {})
            write(out / 'REPORT.json', report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    result = worker(args.directory, "ON", args.port)
    print(json.dumps({"classification": result["classification"]}), flush=True)
