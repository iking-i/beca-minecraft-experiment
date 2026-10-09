"""External host-command synchronization only; unchanged live Core and engine."""
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
from individual.observation import stable_id
from experimental.observation_interface_references.reference.references import resolve
from individual.internal_state import InternalState


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
    settings['username'] = 'BECA_H_' + uuid4().hex[:8]
    settings['port'] = port
    settings['reconnect']['enabled'] = False
    configuration = directory / 'body-config.json'
    configuration.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    report = {'classification': 'NOT_TESTABLE', 'port': port, 'database': str(database),
        'bootstrap_expression': deepcopy(BOOTSTRAP), 'bootstrap_authorship': 'EXPERIMENTER',
        'records': [], 'bootstrap': None, 'minecraft_connected': False,
        'world_interventions': [], 'body_username': settings['username'],
        'controlled_channel': str(stable_id('26.1:player_slots:44:count')),
        'operator_authorship': 'EXPERIMENTER_WORLD_COMMAND',
        'protocol': 'quantity 0->1; only after matching route, 1->0->1; two renewed frames',
        'synthetic_training': False, 'imported_history': False,
        'sampler_used': False, 'binder_used': False, 'retry': False,
        'window': {'observations': 6, 'host_phase_wait_seconds': 600, 'command_settle_seconds': 2, 'manual_host_commands': True}}
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
                def observe(label):
                    raw = bridge.call('observe', timeout=10)
                    record = {'label': label, 'raw_observation': deepcopy(raw),
                              'state_before': core.state.to_dict()}
                    report['records'].append(record)
                    try:
                        core.accept_observation(raw)
                    except Exception as error:
                        record['admission_error'] = {'type': type(error).__name__, 'message': str(error)}
                        raise
                    record['state_after'] = core.state.to_dict()
                    source = core.state.internal_state['l0_state'][REF_KEY]['current_source']
                    quantity = source['numeric_channels'].get(report['controlled_channel'])
                    record['controlled_quantity'] = quantity
                    print(json.dumps({'observation': label, 'quantity': quantity,
                        'version': core.state.state_version,
                        'routes': len(core.state.internal_state['l0_state'][KEY]['routes'])}), flush=True)
                    return quantity

                def intervene(item, expected, label):
                    command = '/item replace entity ' + settings['username'] + ' hotbar.8 with ' + item
                    entry = {'source': 'EXPERIMENTER_WORLD_COMMAND', 'command': command,
                             'channel_id': report['controlled_channel'],
                             'state_before': core.state.state_version, 'monotonic': time.monotonic()}
                    report['world_interventions'].append(entry)
                    stage_file = directory / (label + '.READY.json')
                    ack_file = directory / (label + '.HOST_ACK.json')
                    instruction = {'phase': label, 'command': command,
                        'body_username': settings['username'],
                        'individual_id': core.state.individual_id,
                        'session_id': core.state.session_id,
                        'committed_state_before': core.state.state_version,
                        'channel_id': report['controlled_channel'],
                        'expected_after': expected, 'ack_file': str(ack_file)}
                    stage_file.write_text(json.dumps(instruction, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(json.dumps({'host_command_ready': instruction}, ensure_ascii=False), flush=True)
                    deadline = time.monotonic() + 600
                    while not ack_file.exists():
                        if time.monotonic() >= deadline:
                            raise RuntimeError('Host command acknowledgement timed out; no retry')
                        time.sleep(.5)
                    acknowledgement = json.loads(ack_file.read_text(encoding='utf-8'))
                    if (acknowledgement.get('command') != command
                            or acknowledgement.get('source') != 'WORLD_OWNER_REPORT'
                            or acknowledgement.get('completed') is not True):
                        raise RuntimeError('Host command not confirmed successful; stop without retry')
                    entry['host_report'] = acknowledgement
                    # Host report is not proof of a world change; require the next actual observation.
                    time.sleep(2)
                    actual = observe(label)
                    entry['observed_quantity'] = actual
                    entry['state_after'] = core.state.state_version
                    if type(actual) is not int or actual != expected:
                        raise RuntimeError('Actual world quantity differs from preregistered boundary; no retry')

                if observe('E1_baseline') != 0:
                    raise RuntimeError('Fresh body hotbar.8 not empty; do not alter initial condition')
                report['bootstrap'] = core.bootstrap_once()
                intervene('minecraft:stone 1', 1, 'E2_external_0_to_1')
                internal = InternalState.from_dict(core.state.internal_state)
                report['matching_route_ids'] = [ref for ref, route in internal.l0_state[KEY]['routes'].items()
                    if route['trigger']['channel_id'] == report['controlled_channel']
                    and resolve(internal, route['trigger']['before'])['value'] == 0
                    and resolve(internal, route['trigger']['after'])['value'] == 1]
                if not report['matching_route_ids']:
                    raise RuntimeError('No route from actual controlled transition; stop without further intervention')
                intervene('minecraft:air', 0, 'E3_external_1_to_0')
                intervene('minecraft:stone 1', 1, 'E4_external_0_to_1')
                for label in ('E5_renewed_world', 'E6_continued_recursion'):
                    time.sleep(2)
                    observe(label)
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
