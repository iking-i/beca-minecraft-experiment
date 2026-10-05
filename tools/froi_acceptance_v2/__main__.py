"""Explicit external v2 acceptance. No A/Minecraft startup or formal writes."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import time

from debug.froi_acceptance_material import ROOT, unpack
from tools.froi_acceptance_v2 import material as m, checks as c


def write(path, value):
    path=Path(path)
    if path.exists(): raise ValueError('Never overwrite historical evidence')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as stream:
        for token in m.ENCODER.iterencode(value):
            for off in range(0,len(token),65536): stream.write(token[off:off+65536])
        stream.write('\n')


def tooling_contract():
    path=ROOT/'FROI_ACCEPTANCE_FREEZE_V2.json'
    if not path.exists(): return {'status':'NOT_TESTABLE','reason':'v2 not frozen'}
    manifest=json.loads(path.read_text(encoding='utf8'))
    actual={p.relative_to(ROOT).as_posix():m.file_hash(p) for p in sorted((ROOT/'tools/froi_acceptance_v2').glob('*.py'))}
    original=c.frozen_contract()
    ok=actual==manifest['measurement_tool_hashes'] and original['status']=='PASS' and manifest['engineering_regression']['passed']
    return {'status':'PASS' if ok else 'FAIL','v1_contract':original,
            'measurement_tool_hashes':actual,'manifest_digest':m.file_hash(path)}


def attempt(fn):
    try: return fn()
    except (ValueError,KeyError,FileNotFoundError,TypeError) as error:
        reason=str(error)
        return c.report('MATERIAL_UNAVAILABLE' if 'MATERIAL_UNAVAILABLE' in reason else 'FAIL',reason=reason)


def validate_local(a, *, pair_versions=None, limit_id=None, continuation=False):
    """Identical frozen item predicates; PRE/POST/T5 are applied by batch boundary."""
    database=a.payload['database'];result={'T1':c.verify_t1(a)}
    result['T2']=attempt(lambda:c.run_t2(a,[m.read_history(database,v) for v in pair_versions])) if pair_versions else c.report('MATERIAL_UNAVAILABLE',reason='No explicitly specified paired real history prefixes')
    result['T3']=attempt(lambda:c.run_t3(a))
    result['T4']=attempt(lambda:c.trace_t4(database,limit_id)) if limit_id else c.report('MATERIAL_UNAVAILABLE',reason='No specified real read-failure consequence')
    if result['T4'].get('organization_statuses') and any(s!='COMPLETE' for s in result['T4']['organization_statuses']):
        result['T4'].update(status='NOT_TESTABLE',trace_integrity_status=result['T4']['status'],reason='Trace retained, but incomplete organization cannot satisfy formal acceptance')
    if continuation:
        if result['T2'].get('outputs'):
            from individual.internal_state import InternalState
            from individual.observation import ObservationFrame
            result['T2_continuations']=[]
            for saved,history in zip(result['T2']['outputs'],result['T2']['histories']):
                output=(InternalState.from_dict(saved['internal']),ObservationFrame(**saved['frame']),saved['journal'])
                result['T2_continuations'].append(attempt(lambda:c.detached_continue(a,output,intervention_history=unpack(history))))
        if result['T3']['status']=='PASS':
            from integration.froi import resume_detached
            branch=resume_detached(c.engine_for(a.checkpoint),a.checkpoint,a.handle,screen_effect=True)
            result['detached_continuation']=attempt(lambda:c.detached_continue(a,branch))
        else: result['detached_continuation']=c.report('NOT_TESTABLE',reason='T3 replay gate not passed')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',required=True);p.add_argument('--session',required=True)
    p.add_argument('--versions',nargs='+',type=int,required=True)
    p.add_argument('--pair-versions',nargs=2,type=int,required=True)
    p.add_argument('--limit-id',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();out=Path(args.output).resolve()
    if out.exists():p.error('Output directory exists; preserve previous evidence')
    contract=tooling_contract()
    if contract['status']!='PASS':p.error('Frozen v1/v2 contract rejected')
    out.mkdir(parents=True);metrics=m.Metrics();m.ACTIVE_METRICS=metrics
    with m.readonly(args.database) as db:
        names=[r[1] for r in db.execute('PRAGMA table_info(sessions)')]
        row=db.execute('SELECT * FROM sessions WHERE session_id=?',(args.session,)).fetchone()
        if row is None:raise ValueError('MATERIAL_UNAVAILABLE: specified session missing')
        session=dict(zip(names,row));session['environment']=json.loads(session['environment'])
        end=db.execute('SELECT ended_at,end_version,reason,interrupted FROM session_ends WHERE session_id=?',(args.session,)).fetchone()
        if end is None:raise ValueError('Source session must be ended/quiescent')
    write(out/'measurement-plan.json',{'versions':args.versions,'pair_versions':args.pair_versions,
        'limit_id':args.limit_id,'session':args.session,'category':'EXPERIMENTER',
        'selection':'User fixed COMPLETE sequence; pre-existing A16 paired prefix plan15/12; no outcome search',
        'runtime_commit':'MATERIAL_UNAVAILABLE','memory_budget_bytes':512*1024*1024})
    print('EXPORT freeze: streaming entire database and canonical events/states',flush=True)
    exported,source=m.freeze(args.database,metrics)
    for v in args.versions:
        text=m.export_manifest(args.database,v,exported,source,metrics=metrics)
        write(out/f'artifact-A{v}.json',json.loads(text))
    print('PRE independent source reread: streaming entire database',flush=True)
    before,verified_source=m.freeze(args.database,metrics)
    if before!=exported or verified_source!=source:raise ValueError('PRE source/database freeze mismatch')
    summaries=[]
    for v in args.versions:
        print(f'Executing A{v}: T1/T3; fixed T2 pair only for A{args.versions[0]}',flush=True)
        text=m.canonical(json.loads((out/f'artifact-A{v}.json').read_text(encoding='utf8')))
        a=m.load_manifest(text,before,verified_source,metrics)
        if a.checkpoint.payload['session_id']!=args.session:raise ValueError('Cross-session checkpoint')
        r=validate_local(a,pair_versions=args.pair_versions if v==args.versions[0] else None,
                         limit_id=args.limit_id,continuation=True)
        binding={'individual_id':a.checkpoint.request.individual_id,'session_id':args.session,
                 'state_version':v,'frame_id':a.checkpoint.frame.frame_id,
                 'query':a.checkpoint.request.reference,'checkpoint_digest':a.checkpoint.digest,
                 'handle_digest':m.digest(a.handle.audit()),'graph_digest':a.handle.audit()['graph_digest'],
                 'history_cutoff':a.history.event_cutoff,'history_digest':m.digest(m.pack(a.history))}
        r['item_metadata']={k:{'tested_object':binding,'evidence_kind':kind,
            'status':r[k]['status'],'blocker':r[k].get('reason'),
            'COMPLETE_gate':a.handle.complete if k in ('T1','T3') else
                all(x=='COMPLETE' for x in r[k].get('organization_statuses',[])) if k=='T4' else
                [m.unpack(x).complete for x in r[k].get('handles',[])]}
            for k,kind in [('T1','ACTUAL_LIVE_RECORDED'),('T2','DETACHED_REAL_HISTORY_COUNTERFACTUAL'),
                           ('T3','DETACHED_EXACT_CHECKPOINT_EFFECT_SCREENING'),('T4','ACTUAL_LIVE_RECORDED_TRACE')]}
        r['item_metadata']['T2']['paired_history_versions']=args.pair_versions if v==args.versions[0] else None
        r['item_metadata']['T4']['tested_object']={'limit_id':args.limit_id,'actual_versions':[27,30]}
        write(out/f'evidence-A{v}.json',r)
        summaries.append({'version':v,'artifact_digest':a.digest,'statuses':{k:r[k]['status'] for k in ('T1','T2','T3','T4')}})
        del a,r
    print('POST whole-session freeze; no incomplete result excluded',flush=True)
    after,after_source=m.freeze(args.database,metrics)
    post_contract=tooling_contract(); t5=[]
    for v in args.versions:
        text=m.canonical(json.loads((out/f'artifact-A{v}.json').read_text(encoding='utf8')))
        a=m.load_manifest(text,before,verified_source,metrics)
        r=json.loads((out/f'evidence-A{v}.json').read_text(encoding='utf8'))
        result=c.verify_t5(a,before,after,r)
        if contract!=post_contract:result['status']='FAIL';result['measurement_tool_FREEZE']='FAIL'
        result['item_metadata']={'evidence_kind':'FULL_SOURCE_DATABASE_FREEZE_AND_CONTROLLED_OBJECTS',
            'tested_object':{'session_id':args.session,'checkpoint_version':v,'checkpoint_digest':a.checkpoint.digest},
            'COMPLETE_gate':result['checks']['all_used_organizations_COMPLETE'],
            'blocker':[k for k,ok in result['checks'].items() if not ok]}
        write(out/f'T5-A{v}.json',result);t5.append({'version':v,**result})
        del a,r
    with m.readonly(args.database) as db:
        # Full session status inventory: never drop the 117 incomplete rounds.
        inventory=[{'state_version':r[0],'status':r[1],'closure_complete':bool(r[2])} for r in db.execute(
            "SELECT state_version,json_extract(payload,'$.status'),json_extract(payload,'$.closure_complete') FROM events WHERE event_type='FROI_ORGANIZATION_FORMED' ORDER BY event_sequence")]
    resources=metrics.result(sum(p.stat().st_size for p in out.iterdir() if p.is_file()))
    summary={'harness':'FROI-1 ACCEPTANCE HARNESS v2','category':'EXPERIMENTER','session':session,
        'session_end':dict(zip(('ended_at','end_version','reason','interrupted'),end)),
        'runtime_commit':'MATERIAL_UNAVAILABLE','measurement_commit':before['repository_commit'],
        'tooling_contract':contract,'source_freeze_PRE':before,'source_freeze_POST':after,
        'source_event_digest_PRE':verified_source,'source_event_digest_POST':after_source,
        'checkpoints':summaries,'T5':t5,'all_session_organization_results':inventory,
        'resources':resources,'BOUNDED_MEMORY_VALIDATION':'PASS' if resources['peak_rss_bytes']<=512*1024*1024 else 'FAIL',
        'FROI1_ACCEPTANCE':'PASS' if all(s['status']=='PASS' for s in t5) and all(all(x=='PASS' for x in r['statuses'].values()) for r in summaries) else 'PARTIAL',
        'official_FROI_pass_claimed':False,'CURRENT_RUN_REUSED_WITHOUT_MINECRAFT_RERUN':'YES'}
    write(out/'report.json',summary)
    lines=['# FROI-1 v2 live acceptance','',f"Session: {args.session}",f"Individual: {session['individual_id']}",
        f"Measurement commit: {before['repository_commit']}",'Runtime commit: MATERIAL_UNAVAILABLE',
        f"Ended: {end[0]}; reason: {end[2]}",'','| Checkpoint | T1 | T2 | T3 | T4 | T5 |','|---|---|---|---|---|---|']
    for row,last in zip(summaries,t5):lines.append('| A'+str(row['version'])+' | '+' | '.join(row['statuses'][k] for k in ('T1','T2','T3','T4'))+' | '+last['status']+' |')
    lines += ['', 'Each evidence-A*.json retains exact tested objects, real T1 inputs and T4 trace, detached T2/T3 outputs, replay gates and blockers. T5-A*.json retains every fixed freeze/COMPLETE predicate.',
        'T2 uses the original A16 prefix pair15/12 only. Other checkpoints have no new pair supplied; no favorable history search.',
        'A27 -> A30 uses the original fixed actual limit. RESOURCE_LIMIT is never COMPLETE; the trace status is retained separately from formal T4 NOT_TESTABLE.',
        'No original database/source/caps were written, no world/body/action was executed; all 121 organization statuses including 117 RESOURCE_LIMIT remain inventoried.',
        '', 'Resources:', '```json',json.dumps(resources,indent=2),'```','',f"FROI1_ACCEPTANCE = {summary['FROI1_ACCEPTANCE']}",
        'CURRENT_RUN_REUSED_WITHOUT_MINECRAFT_RERUN = YES','RUNTIME_COMMIT = MATERIAL_UNAVAILABLE']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'output':str(out),'checkpoints':summaries,'T5':[x['status'] for x in t5], 'resources':resources}),flush=True)


if __name__=='__main__':main()
