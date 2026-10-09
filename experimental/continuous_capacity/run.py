"""Bounded real observations through frozen UsageRealCore, with external records."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from individual.bridge import MinecraftBridge
from individual.formal_l0 import digest
from experimental.formall0_operative.validation import initial
from experimental.observation_interface_references.effects.channel import EffectConfig
from experimental.observation_interface_references.real.channel import BOOTSTRAP
from experimental.operative_content.engine import ContentCapacityError
from experimental.ordinary_pair_usage.channel import UsageRealCore
from experimental.ordinary_pair_usage.engine import VERSION
from .recorder import CapacityTrace, inventory, delta

ROOT = Path(__file__).resolve().parents[2]
BASE = '43ef0ef97797992bf788d52c348b79be294407c0'
THEORY_SUPPLIED = '78c5bfa0af87ac4a55493d46c91bcc653e554f0e'


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')


def events_after(store, sequence):
    cursor = store.connection.execute(
        'SELECT event_sequence,event_type,state_version,timestamp,payload '
        'FROM events WHERE event_sequence>? ORDER BY event_sequence', (sequence,))
    names = [column[0] for column in cursor.description]
    result = [dict(zip(names, row)) for row in cursor]
    for event in result:
        event['payload'] = json.loads(event['payload'])
    return result


def outcome(committed, budget, error):
    if error:
        if error['type'] == 'ContentCapacityError':
            return 'RESOURCE_LIMIT'
        return 'FAILURE' if committed else 'NOT_TESTABLE'
    return 'BUDGET_COMPLETED' if committed == budget else 'PARTIAL'


def observation_carrier_available(status):
    # Existing body.observable() and EffectCore.tick() permit dead observation.
    # This grants no respawn/perform authority and does not change body semantics.
    return not status.get('lastError') and (status.get('connected') or status.get('state') == 'dead')


def run(directory, port, config=ROOT / 'minecraft/config.json'):
    directory = Path(directory).resolve()
    if not directory.is_relative_to(ROOT / '.test-tmp'):
        raise ValueError('Fresh run data must be isolated under workspace .test-tmp')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != BASE:
        raise ValueError('Frozen implementation baseline does not match')
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'frames').mkdir()
    database = directory / 'individual.db'
    settings = json.loads(Path(config).read_text(encoding='utf-8'))
    settings.update(username='BECA_C_' + uuid4().hex[:8], port=port)
    settings['reconnect']['enabled'] = False
    configuration = directory / 'body-config.json'
    write_json(configuration, settings)
    budget = 32
    report = {
        'classification': 'NOT_TESTABLE', 'started_at': now(), 'baseline': head,
        'engine_version': VERSION, 'theory_latest_supplied': THEORY_SUPPLIED,
        'repository_theory_reference_changed': False, 'observation_budget': budget,
        'interval_after_processing_seconds': 2, 'port': port,
        'database': str(database), 'body_username': settings['username'],
        'fresh_database': True, 'fresh_individual': True, 'runtime_interrupted': False,
        'world_interventions': [], 'bootstrap': None,
        'bootstrap_expression': deepcopy(BOOTSTRAP), 'bootstrap_author': 'EXPERIMENTER',
        'records': [], 'committed_frames': 0, 'acquired_frames': 0,
        'sampler_calls': 0, 'binder_calls': 0, 'synthetic_receipts': False,
        'historical_replay': False, 'offline_reconstruction': False,
        'retry': False, 'capacity_changed': False, 'purpose_need_mechanism_added': False,
    }
    core = None
    sequence = 0
    counts = Counter()
    executed, integrated = {}, set()
    report_path = directory / 'REPORT.json'
    write_json(report_path, report)
    with (directory / 'bridge-stderr.log').open('x', encoding='utf-8') as errors, \
         (directory / 'transport.jsonl').open('x', encoding='utf-8') as transport, \
         (directory / 'events.jsonl').open('x', encoding='utf-8') as event_log:
        bridge = MinecraftBridge(configuration, port=port,
            log=lambda line: (errors.write(line + '\n'), errors.flush()))
        original = bridge.call

        def call(method, args=None, timeout=None):
            transport.write(json.dumps({'phase': 'request', 'timestamp': now(),
                'monotonic': time.monotonic(), 'method': method, 'args': args}) + '\n')
            transport.flush()
            try:
                result = original(method, args, timeout)
            except Exception as error:
                transport.write(json.dumps({'phase': 'error', 'method': method,
                    'timestamp': now(), 'type': type(error).__name__, 'message': str(error)}) + '\n')
                transport.flush()
                raise
            transport.write(json.dumps({'phase': 'response', 'method': method,
                'timestamp': now(), 'result': result}, ensure_ascii=False) + '\n')
            transport.flush()
            return result

        bridge.call = call

        def drain(store=None):
            nonlocal sequence
            events = events_after(store or core._store, sequence)
            for event in events:
                event_log.write(json.dumps(event, ensure_ascii=False) + '\n')
                sequence = event['event_sequence']
                counts[event['event_type']] += 1
                if event['event_type'] == 'ACTION_EXECUTED':
                    executed[event['payload']['action_id']] = deepcopy(event)
                if event['event_type'] == 'EXPERIENCE_FORMED':
                    integrated.update(event['payload']['action_ids'])
            event_log.flush()
            return events

        def reject_sampler(*args, **kw):
            report['sampler_calls'] += 1
            raise AssertionError('Sampler forbidden in continuous capacity measurement')

        def reject_binder(*args, **kw):
            report['binder_calls'] += 1
            raise AssertionError('Binder forbidden in continuous capacity measurement')

        try:
            core = UsageRealCore(database, bridge, initialize_lifetime=True,
                config=EffectConfig(str(database), origin_state=initial()[0]))
            report.update(individual_id=core.state.individual_id, session_id=core.state.session_id,
                          origin_inventory=inventory(core.state.to_dict()))
            write_json(directory / 'origin.json', core.state.to_dict())
            with patch('individual.core.select_uniform_action', side_effect=reject_sampler), \
                 patch('individual.core.bind_parameters', side_effect=reject_binder):
                core.start()
                deadline = time.monotonic() + 30
                while True:
                    status = bridge.call('status', timeout=5)
                    for event in bridge.drain_events():
                        if event['kind'] == 'lifecycle':
                            core.accept_bridge_status(event['status'], source=event)
                        elif event['kind'] in ('exited', 'transport_error'):
                            report['runtime_interrupted'] = True
                            raise RuntimeError('Carrier interrupted; no reconnect')
                    if status.get('connected'):
                        break
                    if status.get('lastError') or time.monotonic() >= deadline:
                        raise RuntimeError(f'Body unavailable: {status}')
                    time.sleep(.2)
                report.update(connected=True, core_pid=__import__('os').getpid(), bridge_pid=bridge.pid)
                drain()
                for index in range(1, budget + 1):
                    if index > 1:
                        time.sleep(2)
                    for event in bridge.drain_events():
                        if event['kind'] == 'lifecycle':
                            core.accept_bridge_status(event['status'], source=event)
                            if not observation_carrier_available(event['status']):
                                report['runtime_interrupted'] = True
                                raise RuntimeError('Native carrier disconnected; stop without reconnect')
                        elif event['kind'] in ('exited', 'transport_error'):
                            report['runtime_interrupted'] = True
                            raise RuntimeError('Native carrier exited; stop without reconnect')
                    drain()
                    before = core.state.to_dict()
                    raw = bridge.call('observe', timeout=10)
                    report['acquired_frames'] += 1
                    frame_file = directory / 'frames' / f'E{index:02d}.json'
                    frame_record = {'attempt': index, 'raw_observation': raw, 'state_before': before}
                    write_json(frame_file, frame_record)  # Save actual input before processing can fail.
                    trace = CapacityTrace()
                    try:
                        with trace:
                            core.accept_observation(raw)
                    except Exception as error:
                        after = core.state.to_dict()
                        frame_record.update(state_after_failure=after, error={
                            'type': type(error).__name__, 'message': str(error)},
                            capacity_trace=trace.records, events=drain(),
                            unchanged_committed_state=(after == before),
                            authoritative_matches=core._store.latest_state().to_dict() == after)
                        write_json(frame_file, frame_record)
                        report['failed_frame_file'] = str(frame_file)
                        raise
                    after = core.state.to_dict()
                    events = drain()
                    if (after['individual_id'] != report['individual_id']
                            or after['session_id'] != report['session_id']
                            or after['state_version'] <= before['state_version']
                            or after['environment_sequence'] != index):
                        raise RuntimeError('Continuous identity/version/session boundary changed')
                    if core._store.latest_state().to_dict() != after:
                        raise RuntimeError('Authoritative state differs from committed live state')
                    summary = {
                        'frame': index, 'frame_id': after['observation_frame']['frame_id'],
                        'state_version': after['state_version'], 'event_sequence': sequence,
                        'individual_id': after['individual_id'], 'session_id': after['session_id'],
                        'timestamp': after['observation_frame']['timestamp'],
                        'inventory': inventory(after), 'delta': delta(before, after, events),
                        'event_counts': dict(Counter(e['event_type'] for e in events)),
                        'authoritative_matches': True,
                    }
                    frame_record.update(state_after=after, measurement=summary, events=events)
                    write_json(frame_file, frame_record)
                    report['records'].append(summary)
                    report['committed_frames'] += 1
                    write_json(report_path, report)
                    print(json.dumps({'frame': index, 'version': after['state_version'],
                        'capacity': summary['inventory']['total_unit_charge'],
                        'pairs': summary['inventory']['pairs'],
                        'routes': summary['inventory']['effect_routes']}, ensure_ascii=False), flush=True)
                    if any(e['event_type'] == 'ACTION_FAILED' for e in events):
                        raise RuntimeError('Native recursive action failed; no retry')
                    if index == 1:
                        report['bootstrap'] = core.bootstrap_once()
                        drain()
                        write_json(report_path, report)
        except Exception as error:
            report['error'] = {'type': type(error).__name__, 'message': str(error),
                               'timestamp': now(), 'traceback': traceback.format_exc()}
        finally:
            if core is not None:
                drain()
                report['final_before_shutdown'] = core.state.to_dict()
                report['final_inventory'] = inventory(core.state.to_dict())
                report['authoritative_matches_before_shutdown'] = (
                    core._store.latest_state().to_dict() == core.state.to_dict())
                try:
                    core.shutdown('EXTERNAL_32_FRAME_BUDGET_OR_LIMIT_STOP')
                    report['shutdown_state'] = core.state.to_dict()
                    report['shutdown_completed'] = True
                    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
                        drain(SimpleNamespace(connection=db))
                except Exception as error:
                    report['shutdown_error'] = traceback.format_exc()
            else:
                bridge.close()
            report.update(event_counts=dict(counts), final_event_sequence=sequence,
                executions=list(executed.values()),
                integrated_receipt_ids=sorted(integrated & executed.keys()),
                classification=outcome(report['committed_frames'], budget, report.get('error')),
                ended_at=now())
            write_json(report_path, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--port', required=True, type=int)
    args = parser.parse_args()
    result = run(args.directory, args.port)
    print(json.dumps({key: result.get(key) for key in ('classification', 'individual_id',
        'session_id', 'committed_frames', 'acquired_frames', 'final_inventory', 'error')}, ensure_ascii=False))
