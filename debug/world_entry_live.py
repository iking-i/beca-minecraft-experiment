"""TEST_ONLY live causal acceptance; never imported by formal A policy.

Independent identity, selection, configuration and Supervisor. Explicit fixture
commands and choreography are experimenter decisions, never learned behavior.
Protocol evidence is passive and is not supplied to the recursive interpreter.
"""
import argparse
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import queue
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from uuid import uuid4

from debug.live_evidence import at, matching_blocks, server_slot, verdict, freeze_decision
from debug.world_entry_validation import emit
from individual.bridge import MinecraftBridge, ROOT, parse_minecraft_port
from individual.core import ACore
from individual.formal_boundary import RESOURCE_CAP_KEYS, sensor_caps
from individual.formal_l0 import FormalLimits
from individual.storage import create_lifetime, write_json
from supervisor.supervisor import Supervisor, load_limits

CANONICAL = 'A-9ea5abde-7fa2-4313-a102-254d4664fd49'
_CANONICAL_AUDIT_CACHE = {}


def canonical_fingerprint(root=ROOT):
    """Read only, no lease, schema, checkpoint, session or original report writes."""
    root = Path(root)
    selection = root / 'individual/lifetime.json'
    pin = json.loads(selection.read_text(encoding='utf-8'))
    database = (root / pin['database']).resolve()
    files = {p.relative_to(root).as_posix(): {'sha256': sha256(p.read_bytes()).hexdigest()}
             for p in [selection, root / 'minecraft/config.json', root / 'individual/experiment.json', root / 'supervisor/limits.yaml']}
    sidecars = [database, *[Path(str(database) + suffix) for suffix in ('-wal', '-shm', '.lock')]]
    sidecars += [database.with_name('individual.supervisor.db')]
    files.update({str(p): {'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns,
                         **({'sha256':sha256(p.read_bytes()).hexdigest()} if p.stat().st_size<10_000_000 else {})}
                  for p in sidecars if p.exists()})
    cached = _CANONICAL_AUDIT_CACHE.get(str(database))
    if cached and cached['files']==files:
        return deepcopy(cached)
    # A readonly SQLite connection may still write SHM read marks. When WAL
    # exists, query a temporary full file copy, never the original connection.
    scratch = None
    try:
        wal = Path(str(database)+'-wal')
        query_path = database
        flags = '?mode=ro&immutable=1'
        if wal.exists() and wal.stat().st_size:
            scratch = (root/'.test-tmp'/('canonical-read-audit-'+uuid4().hex)).resolve()
            assert scratch.is_relative_to((root/'.test-tmp').resolve())
            scratch.mkdir(parents=True,exist_ok=False)
            query_path=scratch/'individual.db'
            print('Read-only canonical WAL audit: copying temporary audit image; original files untouched',flush=True)
            shutil.copyfile(database,query_path);shutil.copyfile(wal,Path(str(query_path)+'-wal'))
            flags='?mode=ro'
        with closing(sqlite3.connect(query_path.as_uri()+flags,uri=True)) as db:
            version,snapshot=db.execute('SELECT state_version,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
            identity=db.execute('SELECT individual_id FROM experiment').fetchone()[0]
            last_event=db.execute('SELECT MAX(event_sequence) FROM events').fetchone()[0]
            sessions=db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
        for p in sidecars:
            if str(p) in files:
                assert p.stat().st_size==files[str(p)]['bytes'] and p.stat().st_mtime_ns==files[str(p)]['mtime_ns'], 'Canonical changed during read audit'
    finally:
        if scratch:
            # Verified own workspace directory; only unlink direct audit files.
            assert scratch.is_relative_to((root/'.test-tmp').resolve())
            for p in scratch.iterdir():
                assert p.parent==scratch and p.is_file()
                p.unlink()
            scratch.rmdir()
    result = {'files': files, 'individual_id': identity, 'selection': pin,
            'state_version': version, 'last_event_sequence': last_event, 'sessions': sessions,
            'latest_snapshot_sha256': sha256(snapshot.encode()).hexdigest(),
            'formal_boundary': json.loads(snapshot).get('internal_state', {}).get('l0_state', {}).get('locked_caps')}
    _CANONICAL_AUDIT_CACHE[str(database)]=deepcopy(result)
    return result


def read_wire(path):
    if not Path(path).exists():
        return []
    result = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        try: result.append(json.loads(line))
        except ValueError: pass  # An incomplete last append is not evidence.
    return result


def retained_history_checks(report):
    """Match every request and both frames to the actual append-only test DB."""
    database=Path(report['database']).resolve()
    if report['individual_id']==CANONICAL or CANONICAL in str(database):
        raise ValueError('Never query canonical for validation history')
    checks={'requested_events_match':True,'executed_events_match':True,'frames_match_states':True,
            'numeric_formal_path':True,'test_only_authorship':True}
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
        events={}
        for kind,payload in db.execute("SELECT event_type,payload FROM events WHERE event_type IN ('ACTION_REQUESTED','ACTION_EXECUTED')"):
            value=json.loads(payload);events[(kind,value['action_id'])]=value
        for step in report['steps']:
            requested=events.get(('ACTION_REQUESTED',step['action_id']),{})
            executed=events.get(('ACTION_EXECUTED',step['action_id']),{})
            checks['requested_events_match'] &= requested.get('provenance',{}).get('source_state_version')==step['source_version']
            checks['executed_events_match'] &= executed.get('status')=='executed'
            checks['numeric_formal_path'] &= requested.get('method')=='perform' and requested.get('args')=={
                'code':step['action_code'],'parameters':step['parameters']}
            checks['test_only_authorship'] &= requested.get('provenance',{}).get('decision_authorship',{}).get('aggregate_source')=='TEST_ONLY'
            for version,frame in [(step['source_version'],step['source_frame']),
                                  (step['observation_version'],step['renewed_frame'])]:
                row=db.execute('SELECT individual_id,snapshot FROM states WHERE state_version=?',(version,)).fetchone()
                checks['frames_match_states'] &= bool(row and row[0]==report['individual_id']
                    and json.loads(row[1]).get('observation_frame')==frame)
    return checks


def server_positions(records):
    def simplify(value):
        if isinstance(value,list): return [simplify(v) for v in value]
        if isinstance(value,dict):
            if 'type' in value and 'value' in value: return simplify(value['value'])
            return {k:simplify(v) for k,v in value.items()}
        return value
    def text(value):
        if isinstance(value,str): return value
        if isinstance(value,list): return ''.join(text(v) for v in value)
        if isinstance(value,dict): return str(value.get('text',value.get('',''))) + text(value.get('extra',[]))
        return ''
    positions = []
    for r in records:
        if r['direction'] != 'IN' or r['name'] != 'system_chat': continue
        component=simplify(r['data'].get('content',{}))
        if not isinstance(component,dict) or component.get('translate')!='commands.data.entity.query': continue
        parts=component.get('with',[])
        if len(parts)!=2 or text(parts[0])!='BECA_Validate': continue
        for m in re.finditer(r'\[([-+\d.eE]+)d?,\s*([-+\d.eE]+)d?,\s*([-+\d.eE]+)d?\]', text(parts[1])):
            positions.append((r, dict(zip(('x', 'y', 'z'), map(float, m.groups())))))
    return positions


def review_report(path):
    """Re-decode retained evidence into a NEW report; never rewrite the live run."""
    path=Path(path).resolve()
    report=json.loads(path.read_text(encoding='utf-8'))
    if report.get('individual_id')==CANONICAL or report.get('source')!='TEST_ONLY':
        raise ValueError('Only independent TEST_ONLY evidence may be reviewed')
    wire=read_wire(path.parent/'wire-events.jsonl')
    steps=report['steps'];press,release=steps[:2]
    if [press['action_code'],release['action_code']]!=[34,34] or press['parameters']!={'control':0,'pressed':1} or release['parameters']!={'control':0,'pressed':0}:
        raise ValueError('Ground proof is not the explicit held-input pair')
    positions=server_positions(wire)
    before=[p for p in positions if p[0]['wire_sequence']<press['wire_after']]
    after=[p for p in positions if p[0]['wire_sequence']>release['wire_through']]
    first,last=before[-1],after[0]
    observed=release['raw_after']['position']
    changed=not at(first[1],last[1]) and all(abs(last[1][k]-observed[k])<.02 for k in ('x','y','z'))
    report['chains']['ground_movement']=verdict([press,release],[last[0]],
        {'server_before':first[1],'server_after':last[1],'renewed_position':observed} if changed else {},
        'Server Pos query decoded from colored NBT components. Post-frame read confirms renewed-frame coordinates; not a per-input ACK.')
    report['evidence_review']={'original_report':path.name,'original_report_sha256':sha256(path.read_bytes()).hexdigest(),
        'source':'TEST_ONLY_PASSIVE_WIRE_REVIEW','new_live_actions':0,'reason':'Decode native 26.1 colored NBT Pos query without changing retained evidence'}
    report.update(freeze_decision(report['chains']))
    report['retained_history_checks']=retained_history_checks(report)
    if not all(report.get(k) for k in ('canonical_completely_unchanged','boundary_preserved','identity_preserved')) or not all(report['retained_history_checks'].values()):
        report['WORLD_ENTRY_FREEZE']='blocked';report['blockers'].append('ISOLATION_OR_BOUNDARY_UNVERIFIED')
    reviewed=path.with_name('live-reviewed-'+uuid4().hex[:8]+'.json')
    write_json(reviewed,report)
    return reviewed,report


def make_fixture(raw, username, token):
    x, z = math.floor(raw['position']['x']), math.floor(raw['position']['z'])
    y = math.floor(raw['position']['y']) + 5
    if y > 308: raise ValueError('Fixture would exceed the ordinary world height; choose a lower separate area')
    dig, place, chest = ({'x': x, 'y': y + 1, 'z': z + 1}, {'x': x + 1, 'y': y, 'z': z}, {'x': x - 1, 'y': y + 1, 'z': z})
    entity = {'x': x + .5, 'y': y + 1, 'z': z - .65}
    # Each command is an external fixture operation, not a formal action.
    commands = [f'/fill {x-2} {y} {z-2} {x+2} {y} {z+2} polished_andesite keep',
        f'/fill {x-2} {y+1} {z-2} {x-2} {y+2} {z+2} barrier keep',
        f'/fill {x+2} {y+1} {z-2} {x+2} {y+2} {z+2} barrier keep',
        f'/fill {x-1} {y+1} {z-2} {x+1} {y+2} {z-2} barrier keep',
        f'/fill {x-1} {y+1} {z+2} {x+1} {y+2} {z+2} barrier keep',
        f'/setblock {x} {y+1} {z+1} dirt keep',
        f'/setblock {x-1} {y+1} {z} chest keep',
        f'/item replace block {x-1} {y+1} {z} container.0 with diamond 3',
        f'/gamemode survival {username}',
        f'/item replace entity {username} hotbar.0 with cobblestone 4',
        f'/item replace entity {username} hotbar.1 with snowball 3',
        f'/summon chicken {entity["x"]} {entity["y"]} {entity["z"]} {{NoAI:1b,PersistenceRequired:1b,Health:1.0f,Tags:["{token}"]}}',
        f'/tp {username} {x+.5} {y+1} {z+.5} 0 0']
    return {'source': 'TEST_FIXTURE', 'region': {'x': [x-2,x+2], 'y': [y,y+2], 'z': [z-2,z+2]},
            'commands': commands, 'dig': dig, 'place_reference': place,
            'placed': {**place,'y': y+1}, 'chest': chest, 'entity': entity,
            'center': {'x':x+.5,'y':y+1,'z':z+.5}, 'token':token}


def worker(args, database, directory):
    report = {'source':'TEST_ONLY', 'autonomous_behavior_claimed':False, 'recursive_success_claimed':False,
              'steps':[], 'chains':{}, 'conditional_validation':'CONDITIONAL_NOT_TESTED'}
    wire_path = directory / 'wire-events.jsonl'
    controls = queue.Queue()
    def reader():
        for line in sys.stdin:
            try: controls.put(json.loads(line))
            except ValueError: pass
        controls.put({'command':'terminate'})
    threading.Thread(target=reader,daemon=True).start()
    bridge = MinecraftBridge(directory / 'body.validation.local.json', adapter=ROOT/'debug/world_entry_wire.mjs',
                             port=args.port, log=lambda s: print(s,file=sys.stderr,flush=True))
    core = None
    try:
        limits = load_limits(ROOT/'supervisor/limits.yaml')
        resources = {k:limits[k] for k in RESOURCE_CAP_KEYS}
        resources['body_observation_caps'] = sensor_caps(directory/'body.validation.local.json')
        core = ACore(database,bridge,session_label='World-entry causal TEST_ONLY',
            session_context={'source':'TEST_ONLY','real_minecraft':True,'wire_recording':'external_passive'},
            physical_caps=FormalLimits.load(),resource_caps=resources)
        identity = core.state.individual_id
        assert identity != CANONICAL
        report.update(individual_id=identity,database=str(database),session_id=core.state.session_id)
        emit('CORE_STARTED',individual_id=identity,state_version=core.state.state_version,session_id=core.state.session_id)
        core.start();emit('BRIDGE_STARTED',pid=bridge.pid)
        def wait(seconds):
            deadline = time.monotonic()+seconds
            while True:
                while not controls.empty():
                    msg=controls.get_nowait()
                    if msg['command']=='terminate': raise RuntimeError('Supervisor terminated acceptance')
                    if msg['command']=='resource_sample': core.accept_resources(msg['payload'])
                emit('HEARTBEAT',individual_id=identity,state_version=core.state.state_version,
                     session_id=core.state.session_id,bridge_pid=bridge.pid)
                if time.monotonic()>=deadline: return
                time.sleep(min(.5,deadline-time.monotonic()))
        def refresh(delay=.2):
            wait(delay)
            core.accept_bridge_status(bridge.call('status'))
            raw=bridge.call('observe');core.accept_observation(raw)
            return raw
        deadline=time.monotonic()+35
        while not bridge.call('status')['connected']:
            if time.monotonic()>deadline: raise RuntimeError('World spawn timeout')
            wait(.5)
        raw=refresh(1)
        locked=deepcopy(core.state.internal_state['l0_state'])
        report['minecraft_version']=raw['encoding']['protocol_version']
        def wire_mark():
            return max((r['wire_sequence'] for r in read_wire(wire_path)),default=0)
        def since(mark):
            return [r for r in read_wire(wire_path) if r['wire_sequence']>mark]
        def command(text,delay=.3):
            mark=wire_mark();bridge.call('chat',{'message':text});wait(delay)
            report.setdefault('fixture_commands',[]).append({'source':'TEST_ONLY','command':text,
                                                           'wire_after':mark})
            return since(mark)
        def run(code,parameters=None,delay=.3):
            source=deepcopy(core.state.observation_frame);before=deepcopy(raw)
            version=core.state.state_version;mark=wire_mark()
            ok=core.execute_discrete_action(code,parameters or {})
            result=core.state.latest_action
            renewed=refresh(delay)
            records=since(mark)
            step={'step_id':f'input-{len(report["steps"])+1}', 'action_id':result['action_id'],
                'source_frame':source,'source_version':version,'action_code':code,'parameters':parameters or {},
                'input_sent':bool(ok and result.get('result',{}).get('result',{}).get('input_sent')),
                'reason_code':result.get('reason_code'),
                'authorship':result['provenance']['decision_authorship']['aggregate_source'],
                'out_wire_sequences':[r['wire_sequence'] for r in records if r['direction']=='OUT'],
                'wire_after':mark,'wire_through':wire_mark(),'observation_version':core.state.state_version,
                'renewed_frame':deepcopy(core.state.observation_frame),'raw_before':before,'raw_after':renewed}
            report['steps'].append(step)
            return renewed,step,records
        def observed_block(pos):
            candidates=[b for b in raw['nearbyBlocks'] if at(b['position'],pos)]
            if len(candidates)!=1: raise ValueError(f'Fixture block not in bounded observation: {pos}')
            return candidates[0]
        def aim(point):
            nonlocal raw
            eye={**raw['position'],'y':raw['position']['y']+1.62}
            dx,dy,dz=(point[k]-eye[k] for k in ('x','y','z'))
            yaw=math.atan2(-dx,-dz);pitch=math.atan2(dy,math.hypot(dx,dz))
            delta=(yaw-raw['orientation']['yaw']+math.pi)%(2*math.pi)-math.pi
            raw,step,records=run(8,{'yaw_delta':delta,'pitch_delta':pitch-raw['orientation']['pitch']})
            if not step['input_sent']: raise ValueError('Explicit view input failed')
        # Check permission without mutating the world, before preparing anything.
        token='BECA_'+uuid4().hex[:8]
        replies=command('/execute run tellraw @s {"text":"'+token+'"}',.5)
        if not any(token in json.dumps(r['data']) for r in replies if r['direction']=='IN' and r['name']=='system_chat'):
            report['startup_blocker']='TEST_FIXTURE_PERMISSION_UNAVAILABLE'
            report['permission_feedback']=[r for r in replies if r['name']=='system_chat']
            raise ValueError('Test robot lacks fixture command permission; provide a separate LAN test world with commands allowed')
        fixture=make_fixture(raw,'BECA_Validate',token)
        report['fixture']=fixture
        for text in fixture['commands']: command(text)
        raw=refresh(1)
        if not at(raw['position'],fixture['center']): raise ValueError('Fixture teleport not server-observed')
        observed_block(fixture['dig']);observed_block(fixture['place_reference']);observed_block(fixture['chest'])
        report['fixture_initial_observation']=deepcopy(core.state.observation_frame)
        # Ground control input; authoritative read-only server Pos queries, not only client physics.
        before_pos=raw['position'];pos_before=server_positions(command('/data get entity BECA_Validate Pos'))
        raw,press,_=run(34,{'control':0,'pressed':1},.15)
        raw,release,_=run(34,{'control':0,'pressed':0},.5)
        pos_after=server_positions(command('/data get entity BECA_Validate Pos'))
        observed_position=raw['position']
        server_changed=bool(pos_before and pos_after and not at(pos_before[-1][1],pos_after[-1][1])
                            and all(abs(pos_after[-1][1][k]-observed_position[k])<.02 for k in ('x','y','z')))
        report['chains']['ground_movement']=verdict([press,release], [p[0] for p in pos_after],
            {'before':before_pos,'after':observed_position,'server_before':pos_before[-1][1],
             'server_after':pos_after[-1][1]} if server_changed else {}, 'Held press/release, server Pos and renewed frame')
        command(f'/tp BECA_Validate {fixture["center"]["x"]} {fixture["center"]["y"]} {fixture["center"]["z"]} 0 0')
        raw=refresh()
        # Completed explicit dig. The experimenter fixes a wait, not the body.
        target=observed_block(fixture['dig'])
        aim({k:target['position'][k]+.5 for k in ('x','y','z')})
        ref=observed_block(fixture['dig'])['block_ref']
        raw,start,first=run(37,{'block_ref':ref},1.5)
        raw,finish,last=run(39,{},.7)
        changes=matching_blocks(first+last,fixture['dig'],0)
        missing=not any(at(b['position'],fixture['dig']) for b in raw['nearbyBlocks'])
        complete_coverage=not raw['coverage']['blocksTruncated'] and raw['coverage']['unloadedBlocks']==0
        report['chains']['completed_dig']=verdict([start,finish],changes,
            {'old_type_id':target['type'],'server_new_type_id':0,'absent_in_renewed_sample':True} if missing and complete_coverage and changes else {},
            'Explicit 1.5 s wait, finish input, inbound block update; no local air edit')
        # Placement with an explicit already-observed hotbar slot and face.
        raw,selected,_=run(16,{'slot':0})
        held=raw['inventorySlots'][36]
        support=observed_block(fixture['place_reference'])
        aim({'x':support['position']['x']+.5,'y':support['position']['y']+1,'z':support['position']['z']+.5})
        support=observed_block(fixture['place_reference'])
        raw,place,records=run(15,{'inventory_slot':36,'reference_block':support['block_ref'],'face':1},.7)
        placed=[b for b in raw['nearbyBlocks'] if at(b['position'],fixture['placed'])]
        changes=matching_blocks(records,fixture['placed'])
        valid=bool(placed and changes and raw['inventorySlots'][36]['count']==held['count']-1)
        report['chains']['placement']=verdict([place],changes,
            {'new_type_id':placed[0]['type'],'held_before':held,'held_after':raw['inventorySlots'][36]} if valid else {},
            'Explicit held slot/reference/top face, inbound block update and renewed occupied target')
        # Actual item use: a fixture snowball, chosen only by the experimenter.
        raw,_,_=run(16,{'slot':1});old=deepcopy(raw['inventorySlots'][37])
        raw,use,records=run(35,{'hand':0},.7)
        new=deepcopy(raw['inventorySlots'][37])
        consequence=server_slot(records,37,old['item_type_id'],old['count']-1)
        raw,release_use,_=run(36,{},.2)
        report['chains']['item_use']=verdict([use,release_use],consequence,
            {'before':old,'after':new} if new['count']==old['count']-1 and consequence else {},
            'Explicit main-hand held use and release; actual server inventory decrement')
        # Single attack on fixture entity at an explicitly prepared location.
        entities=[e for e in raw['nearbyEntities'] if at(e['position'],fixture['entity'])]
        if len(entities)!=1: raise ValueError('Prepared entity is not uniquely observed at its explicit fixture location')
        entity=entities[0];aim({**entity['position'],'y':entity['position']['y']+.35})
        raw,attack,records=run(24,{'entity_ref':entity['entity_ref']},1.3)
        gone=not any(e['id']==entity['id'] for e in raw['nearbyEntities'])
        destroyed=[r for r in records if r['direction']=='IN' and r['name']=='entity_destroy' and entity['id'] in r['data'].get('entityIds',[])]
        report['chains']['entity']=verdict([attack],destroyed,
            {'entity_id':entity['id'],'old_ref':entity['entity_ref'],'absent_in_renewed_sample':True} if gone and destroyed else {},
            'Single explicit attack, server removal and renewed bounded entity sample')
        # Actual container change. Reopening forces a fresh server window_items;
        # we do not treat Mineflayer's predicted click result as an ACK.
        chest=observed_block(fixture['chest']);aim({k:chest['position'][k]+.5 for k in ('x','y','z')})
        hit=raw['crosshair']
        if not hit or hit['target_ref']!=chest['block_ref']: raise ValueError('Explicit chest view has no current hit')
        params={'block_ref':hit['target_ref'],'hand':0,**{k:hit[k] for k in ('face','cursor_x','cursor_y','cursor_z')}}
        raw,opening,records=run(44,params,.5)
        if not raw['container']: raise ValueError('No actual container opened')
        before_window=deepcopy(raw['container']);old=before_window['slot_state'][0]
        first_window=[r for r in records if r['direction']=='IN' and r['name']=='window_items']
        raw,click,click_records=run(43,{'container_id':before_window['container_id'],'slot':0,'mode':1,'button':0},.4)
        predicted=deepcopy(raw['container']['slot_state'][0])
        raw,close,_=run(28,{'container_id':raw['container']['container_id']},.3)
        hit=raw['crosshair'];params={'block_ref':hit['target_ref'],'hand':0,**{k:hit[k] for k in ('face','cursor_x','cursor_y','cursor_z')}}
        raw,reopened,second_records=run(44,params,.5)
        after_window=deepcopy(raw['container'])
        resync=[r for r in second_records if r['direction']=='IN' and r['name']=='window_items']
        verified=[]
        for r in resync:
            wid=(r.get('normalized') or {}).get('window_id')
            verified.extend(server_slot([r],0,None,0,wid))
        valid=bool(old['count']==3 and after_window and after_window['slot_state'][0]['count']==0 and first_window and verified)
        report['chains']['container']=verdict([opening,click,close,reopened],verified,
            {'initial_server_slot':old,'predicted_after_click':predicted,'server_reopened_slot':after_window['slot_state'][0],
             'old_opaque_window':before_window['container_id'],'new_opaque_window':after_window['container_id'],
             'initial_server_wire_sequences':[r['wire_sequence'] for r in first_window]} if valid else {},
            'Single shift-click plus explicit close/reopen; fresh inbound window_items verifies server contents')
        if raw['container']: raw,_,_=run(28,{'container_id':raw['container']['container_id']})
        report['boundary_preserved']=all(core.state.internal_state['l0_state'][k]==locked[k]
            for k in ('locked_caps','locked_resource_caps','formal_condition_id','baseline_version','process_id'))
        report['identity_preserved']=core.state.individual_id==identity
    except Exception as error:
        report['error']=str(error);emit('CORE_ERROR',message=str(error))
    finally:
        if core:
            core.shutdown('world_entry_causal_TEST_ONLY')
            report['final_state_version']=core.state.state_version
            emit('CORE_STOPPED',individual_id=core.state.individual_id,state_version=core.state.state_version)
        else: bridge.close()
        report.update(freeze_decision(report['chains']))
        write_json(directory/'live-report.json',report)
    return int('error' in report or report['WORLD_ENTRY_FREEZE']!='passed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=parse_minecraft_port)
    parser.add_argument('--review-report',help='Offline re-decode retained independent wire evidence into a new report')
    parser.add_argument('--new-test',action='store_true',help='Required explicit authorization to create an independent validation A')
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--database');parser.add_argument('--directory')
    args=parser.parse_args()
    if args.review_report:
        reviewed,report=review_report(args.review_report)
        print(json.dumps({'report':str(reviewed),'WORLD_ENTRY_FREEZE':report['WORLD_ENTRY_FREEZE'],'blockers':report['blockers']}))
        return int(report['WORLD_ENTRY_FREEZE']!='passed')
    if args.port is None: parser.error('--port is required for a live run')
    if args.worker:
        database=Path(args.database).resolve();directory=Path(args.directory).resolve()
        if CANONICAL in str(database) or not database.is_relative_to(ROOT/'storage/individuals'):
            raise ValueError('Only separate validation databases are allowed')
        return worker(args,database,directory)
    if not args.new_test: parser.error('--new-test is required; canonical selection is never opened for runtime')
    canonical=canonical_fingerprint()
    if canonical['individual_id']!=CANONICAL: raise ValueError('Canonical selection differs; review isolation before running')
    selection=ROOT/'storage'/f'world-entry-causal-{uuid4().hex[:8]}.local.json'
    registration=create_lifetime(config=selection,label='World-entry causal validation TEST_ONLY')
    database=Path(registration['database']);directory=database.parent/'reports'/('live-'+uuid4().hex[:8])
    directory.mkdir(parents=True,exist_ok=False)
    config=json.loads((ROOT/'minecraft/config.json').read_text(encoding='utf-8-sig'))
    config.update(username='BECA_Validate',port=args.port)
    config['reconnect']['enabled']=False  # no automatic reconnect/replay during acceptance
    write_json(directory/'body.validation.local.json',config)
    write_json(directory/'canonical-before.json',canonical)
    supervisor=Supervisor(database,load_limits(ROOT/'supervisor/limits.yaml'))
    print(f'Validation A: {registration["individual_id"]}\nReport: {directory}',flush=True)
    try:
        supervisor.start(command=[sys.executable,'-u','-m','debug.world_entry_live','--worker','--port',str(args.port),
                                  '--database',str(database),'--directory',str(directory)])
        supervisor.run(duration=180)
    finally: supervisor.close()
    report_path=directory/'live-report.json'
    report=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {'error':'Worker report unavailable','chains':{}}
    after=canonical_fingerprint()
    report['canonical_completely_unchanged']=after==canonical
    write_json(directory/'canonical-after.json',after)
    report['input_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report.update(freeze_decision(report['chains']))
    report['retained_history_checks']=retained_history_checks(report)
    if not all(report.get(k) for k in ('boundary_preserved','identity_preserved')) or not all(report['retained_history_checks'].values()):
        report['WORLD_ENTRY_FREEZE']='blocked';report['blockers'].append('ISOLATION_OR_BOUNDARY_UNVERIFIED')
    if after!=canonical:
        report['WORLD_ENTRY_FREEZE']='blocked';report['blockers'].append('CANONICAL_CHANGED_EXTERNALLY')
    write_json(report_path,report)
    print(json.dumps({'report':str(report_path),'individual_id':registration['individual_id'],
                      'WORLD_ENTRY_FREEZE':report['WORLD_ENTRY_FREEZE'],'blockers':report['blockers'],
                      'canonical_completely_unchanged':after==canonical},ensure_ascii=False),flush=True)
    return int('error' in report or report['WORLD_ENTRY_FREEZE']!='passed')


if __name__=='__main__':
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'): stream.reconfigure(encoding='utf-8',errors='backslashreplace',line_buffering=True)
    raise SystemExit(main())
