"""Bounded genuine body carrier; one labeled bootstrap, no planned later actions."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time
from unittest.mock import patch
from uuid import uuid4

from individual.bridge import MinecraftBridge
from experimental.formall0_operative.validation import initial
from experimental.observation_interface_references.effects.channel import EffectConfig
from experimental.observation_interface_references.effects.engine import KEY
from experimental.observation_interface_references.reference.references import KEY as REF_KEY
from experimental.operative_content.engine import ContentCapacityError
from .channel import RealEffectCore, BOOTSTRAP


def read_events(store):
    cursor = store.connection.execute(
        'SELECT event_sequence,event_type,state_version,timestamp,payload FROM events ORDER BY event_sequence')
    names = [column[0] for column in cursor.description]
    events = [dict(zip(names, row)) for row in cursor]
    for event in events:
        event['payload'] = json.loads(event['payload'])
    return events


def run(directory, port, config='minecraft/config.json'):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    database = directory / 'individual.db'
    settings = json.loads(Path(config).read_text(encoding='utf-8'))
    settings['username'] = 'BECA_E_' + uuid4().hex[:8]
    settings['port'] = port
    settings['reconnect']['enabled'] = False
    configuration = directory / 'body-config.json'
    configuration.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    report = {'classification': 'NOT_TESTABLE', 'port': port, 'database': str(database),
        'bootstrap_expression': deepcopy(BOOTSTRAP), 'bootstrap_authorship': 'EXPERIMENTER',
        'records': [], 'bootstrap': None, 'minecraft_connected': False,
        'synthetic_training': False, 'imported_history': False,
        'sampler_used': False, 'binder_used': False, 'retry': False,
        'window': {'observations': 8, 'seconds_after_connected': 30}}
    with (directory / 'bridge-stderr.log').open('x', encoding='utf-8') as errors, \
         (directory / 'transport.jsonl').open('x', encoding='utf-8') as transport:
        bridge = MinecraftBridge(configuration, port=port,
            log=lambda line: (errors.write(line + '\n'), errors.flush()))
        original_call = bridge.call
        def call(method, args=None, timeout=None):
            transport.write(json.dumps({'phase': 'request', 'method': method, 'args': args,
                                        'monotonic': time.monotonic()}, ensure_ascii=False) + '\n')
            transport.flush()
            try:
                result = original_call(method, args, timeout)
            except Exception as error:
                transport.write(json.dumps({'phase': 'error', 'method': method,
                    'type': type(error).__name__, 'message': str(error)}) + '\n')
                transport.flush()
                raise
            transport.write(json.dumps({'phase': 'response', 'method': method, 'result': result},
                                       ensure_ascii=False) + '\n')
            transport.flush()
            return result
        bridge.call = call
        core = None
        try:
            core = RealEffectCore(database, bridge, initialize_lifetime=True,
                config=EffectConfig(str(database), origin_state=initial()[0]))
            report['individual_id'] = core.state.individual_id
            report['session_id'] = core.state.session_id
            with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler forbidden')), \
                 patch('individual.core.bind_parameters', side_effect=AssertionError('binder forbidden')):
                core.start()
                startup_deadline = time.monotonic() + 30
                while True:
                    status = bridge.call('status', timeout=5)
                    for event in bridge.drain_events():
                        if event['kind'] == 'lifecycle':
                            core.accept_bridge_status(event['status'], source=event)
                        elif event['kind'] in ('exited', 'transport_error'):
                            raise RuntimeError('Carrier stopped; do not reconnect')
                    if status.get('connected'):
                        report['minecraft_connected'] = True
                        break
                    if status.get('lastError') or time.monotonic() >= startup_deadline:
                        raise RuntimeError(f'Body not available: {status}')
                    time.sleep(.2)
                deadline = time.monotonic() + 30
                for sequence in range(8):
                    if time.monotonic() >= deadline:
                        break
                    raw = bridge.call('observe', timeout=min(10, max(.1, deadline-time.monotonic())))
                    record = {'raw_observation': deepcopy(raw), 'state_before': core.state.to_dict()}
                    report['records'].append(record)
                    try:
                        core.accept_observation(raw)
                    except Exception as error:
                        record['admission_error'] = {'type': type(error).__name__, 'message': str(error)}
                        raise
                    record['state_after'] = core.state.to_dict()
                    if sequence == 0:
                        report['bootstrap'] = core.bootstrap_once()
                    time.sleep(.5)
                report['classification'] = 'PARTIAL' if report['bootstrap'] else 'NOT_READY'
        except Exception as error:
            report['error'] = {'type': type(error).__name__, 'message': str(error)}
            report['classification'] = ('RESOURCE_LIMIT' if isinstance(error, ContentCapacityError)
                else 'PARTIAL' if report['bootstrap'] else 'NOT_READY'
                if report['minecraft_connected'] else 'NOT_TESTABLE')
        finally:
            if core is not None:
                report['final_committed_state'] = core.state.to_dict()
                report['authoritative_current_state'] = core._store.latest_state().to_dict()
                report['events'] = read_events(core._store)
                actions = [e for e in report['events'] if e['event_type'] == 'ACTION_EXECUTED']
                report['external_executions'] = [e for e in actions if
                    e['payload']['initiator'] == 'EXPERIMENTER_SUPPLIED_REAL_BOOTSTRAP']
                report['recursive_executions'] = [e for e in actions if
                    e['payload']['initiator'] == 'TEST_ONLY_ORDINARY_OCCURRENCE_EFFECT']
                experiences = [e for e in report['events'] if e['event_type'] == 'EXPERIENCE_FORMED']
                integrated = {i for e in experiences for i in e['payload']['action_ids']}
                report['recursive_receipts_in_renewed_experience'] = [e['payload']['action_id']
                    for e in report['recursive_executions'] if e['payload']['action_id'] in integrated]
                local = core.state.internal_state['l0_state']
                report['formed_route_count'] = len(local[KEY]['routes'])
                report['formed_connection_count'] = len(local[REF_KEY]['edges'])
                if (not report.get('error') and report['recursive_receipts_in_renewed_experience']
                        and len(experiences) >= 3):
                    report['classification'] = 'PASS'
                try:
                    core.shutdown('TEST_ONLY_real_effect_bounded_close')
                    report['shutdown_state'] = core.state.to_dict()
                except Exception as error:
                    report['shutdown_error'] = str(error)
            else:
                bridge.close()
    (directory / 'REPORT.json').write_text(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    report = run(args.directory, args.port)
    print(json.dumps({k: report.get(k) for k in ('classification', 'individual_id', 'session_id',
        'formed_route_count', 'formed_connection_count', 'recursive_receipts_in_renewed_experience', 'error')}, ensure_ascii=False))
