"""Experimenter-only acceptance choreography, never imported by A's action policy.

Uses an explicitly selected lifetime with normal formal preflight and an independent
Supervisor. Every explicit input is TEST_ONLY; server consequences are re-observed.
New test A only with --new-test; no best-tool/recipe/retry/pathfinding, death injection or teleport.
"""
import argparse
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import queue
import sqlite3
import sys
import threading
import time
from uuid import uuid4

from individual.action_space import DEFINITIONS
from individual.bridge import MinecraftBridge, ROOT, parse_minecraft_port
from individual.core import ACore
from individual.formal_boundary import RESOURCE_CAP_KEYS, sensor_caps
from individual.formal_l0 import FormalLimits
from individual.lifetime import resolve_runtime_database
from individual.storage import create_lifetime
from supervisor.supervisor import Supervisor, load_limits


def emit(kind, **payload):
    print(json.dumps({'kind': kind, **payload}, ensure_ascii=False), flush=True)


def worker(args, database, limits):
    report_path = database.parent / 'reports' / f'world-entry-validation-{time.time_ns()}-{uuid4().hex[:8]}.json'
    bridge = MinecraftBridge(ROOT / 'minecraft/config.json', port=args.port,
                             log=lambda text: print(text, file=sys.stderr, flush=True))
    resource_caps = {k: limits[k] for k in RESOURCE_CAP_KEYS}
    resource_caps['body_observation_caps'] = sensor_caps(ROOT / 'minecraft/config.json')
    controls = queue.Queue()

    def read_controls():
        for line in sys.stdin:
            try: controls.put(json.loads(line))
            except ValueError: pass
        controls.put({'command': 'terminate'})

    threading.Thread(target=read_controls, daemon=True).start()
    core = None
    report = {'source': 'TEST_ONLY', 'autonomous_behavior_claimed': False, 'steps': []}
    before = None
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
            before = connection.execute('SELECT state_version,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
        report['prior_state_version'] = before[0]
        report['prior_snapshot_sha256'] = sha256(before[1].encode()).hexdigest()
        core = ACore(database, bridge, session_label='World-entry acceptance TEST_ONLY',
                     session_context={'source': 'TEST_ONLY', 'port_override': args.port},
                     physical_caps=FormalLimits.load(), resource_caps=resource_caps)
        identity = core.state.individual_id
        lock = deepcopy(core.state.internal_state['l0_state'])
        report['individual_id'] = identity
        emit('CORE_STARTED', individual_id=identity, state_version=core.state.state_version, session_id=core.state.session_id)
        core.start(); emit('BRIDGE_STARTED', pid=bridge.pid)

        def refresh(delay=0):
            deadline = time.monotonic() + delay
            while True:
                while not controls.empty():
                    message = controls.get_nowait()
                    if message['command'] == 'terminate': raise RuntimeError('Supervisor terminated acceptance')
                    if message['command'] == 'resource_sample': core.accept_resources(message['payload'])
                emit('HEARTBEAT', individual_id=identity, state_version=core.state.state_version,
                     session_id=core.state.session_id, bridge_pid=bridge.pid)
                if time.monotonic() >= deadline: break
                time.sleep(min(0.2, deadline-time.monotonic()))
            status = bridge.call('status'); core.accept_bridge_status(status)
            raw = bridge.call('observe'); core.accept_observation(raw)
            return raw

        deadline = time.monotonic() + 35
        while not bridge.call('status')['connected']:
            if time.monotonic() > deadline: raise RuntimeError('World spawn timeout')
            emit('HEARTBEAT', individual_id=identity, state_version=core.state.state_version,
                 session_id=core.state.session_id, bridge_pid=bridge.pid)
            time.sleep(0.2)
        raw = refresh(0.5)
        lock = deepcopy(core.state.internal_state['l0_state'])
        report['protocol_version'] = raw['encoding']['protocol_version']

        def run(name, parameters=None, delay=0.2):
            code = next(k for k,v in DEFINITIONS.items() if v['action_id'] == name)
            version = core.state.state_version
            success = core.execute_discrete_action(code, parameters or {})
            result = core.state.latest_action
            raw = refresh(delay)
            report['steps'].append({'action_code': code, 'parameters': parameters or {}, 'success': success,
                'reason_code': result.get('reason_code'), 'requested_after_version': version,
                'observation_version': core.state.state_version, 'position': raw['position'],
                'body_inputs': raw['bodyInputs'], 'control_modes': raw['controlModes'],
                'frame_id': core.state.observation_frame['frame_id'],
                'authorship': result['provenance']['decision_authorship']['aggregate_source']})
            return raw

        position_before = raw['position']
        run('CONTROL_INPUT', {'control':0,'pressed':1}, delay=0.15)
        raw = run('CONTROL_INPUT', {'control':0,'pressed':0})
        report['movement_changed_position'] = raw['position'] != position_before
        run('USE_START', {'hand':1}); raw = run('USE_RELEASE')
        run('SWAP_HANDS'); run('SWAP_HANDS')  # two explicitly recorded inputs, not automatic correction
        # Auditor chooses one already observed block; the carrier does not search/approach it.
        blocks = raw['nearbyBlocks']
        if blocks:
            run('LOOK_AT', {'object_ref':blocks[0]['block_ref']})
            raw = refresh(0.2)
            hit = raw.get('crosshair')
            if hit:
                run('DIG_START', {'block_ref':hit['target_ref']}, delay=0)
                raw = run('DIG_CANCEL')
                run('BLOCK_INPUT', {'block_ref':hit['target_ref'], 'hand':1, 'face':hit['face'],
                    'cursor_x':hit['cursor_x'],'cursor_y':hit['cursor_y'],'cursor_z':hit['cursor_z']})
            else: report['dig_validation'] = 'not live-validated: no bounded observed collision target after explicit look'
        # Honest invalid state tests; no forced death, mount, sleep or replacement target.
        run('DISMOUNT'); run('WAKE'); run('RESPAWN')
        run('BLOCK_INPUT', {'block_ref':'stale-reference-test','hand':0,'face':1,'cursor_x':0.5,'cursor_y':1,'cursor_z':0.5})
        report['conditional_positive_tests'] = 'not live-validated: death, mount, sleep, GUI require actual world conditions'
        report['individual_id_preserved'] = core.state.individual_id == identity
        report['boundary_preserved'] = all(core.state.internal_state['l0_state'][key] == lock[key]
            for key in ('locked_caps','locked_resource_caps','formal_condition_id','baseline_version','process_id'))
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as connection:
            old = connection.execute('SELECT snapshot FROM states WHERE state_version=?',(before[0],)).fetchone()[0]
        report['prior_snapshot_unchanged'] = old == before[1]
    except Exception as error:
        report['error'] = str(error)
        emit('CORE_ERROR', message=str(error))
    finally:
        if core:
            core.shutdown('world_entry_acceptance_TEST_ONLY')
            report['final_state_version'] = core.state.state_version
            emit('CORE_STOPPED', individual_id=core.state.individual_id, state_version=core.state.state_version)
        else: bridge.close()
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return int('error' in report)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=parse_minecraft_port,required=True)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--new-test',action='store_true',help='Explicit new independent test A; original selection/history are unchanged')
    parser.add_argument('--selection',default=str(ROOT/'individual/lifetime.json'))
    args=parser.parse_args()
    if args.new_test:
        if args.worker: raise ValueError('Only the external parent may register a test lifetime')
        args.selection=str(ROOT/'storage/world-entry-selection.local.json')
        result=create_lifetime(config=args.selection,label='World-entry acceptance independent TEST_ONLY',replace_missing_selection=True)
        print(f"Independent test individual: {result['individual_id']}",flush=True)
    database=resolve_runtime_database(config=args.selection)
    limits=load_limits(ROOT/'supervisor/limits.yaml')
    if args.worker: return worker(args,database,limits)
    supervisor=Supervisor(database,limits)
    supervisor.start(command=[sys.executable,'-u','-m','debug.world_entry_validation','--worker','--port',str(args.port),'--selection',args.selection])
    result=supervisor.run(duration=90)
    # The existing monitor can observe Bridge closure between CORE_STOPPED and
    # worker exit and report bridge_process_exited. Keep that audit record; the
    # acceptance worker's exit status/report distinguish normal close from failure.
    return 0 if supervisor.process.returncode == 0 else result


if __name__ == '__main__':
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'): stream.reconfigure(encoding='utf-8',errors='backslashreplace',line_buffering=True)
    raise SystemExit(main())
