"""EXPERIMENTER FROI-1 harness v1. Never starts A or Minecraft.

Explicit commands export/validate; --help or facility tests do not execute live
T1--T5. Reports/artifacts are external files created exclusively, never replaced.
"""
import argparse
import json
from pathlib import Path

from debug.froi_acceptance_material import ValidationArtifact, export_artifact, freeze, read_history, unpack
from debug.froi_acceptance_checks import (report,verify_t1,run_t2,run_t3,trace_t4,
    verify_t5,detached_continue,engine_for,frozen_contract)
from integration.froi import resume_detached


def external_write(path, text):
    path=Path(path).resolve()
    if path.suffix not in ('.json',): raise ValueError('External evidence output must be JSON')
    if path.exists(): raise ValueError('Never overwrite existing evidence')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream: stream.write(text+'\n')


def validate(artifact, *, pair_versions=None, limit_id=None, continuation=False):
    database=artifact.payload['database'];before=freeze(database)
    contract=frozen_contract()
    if contract['status']!='PASS' or artifact.payload['source_freeze']!=before:
        return {'harness':'FROI-1-acceptance-v1','official_FROI_pass_claimed':False,
            **{k:report('NOT_TESTABLE',reason='PRE freeze gate rejected') for k in ('T1','T2','T3','T4')},
            'T5':report('FAIL',reason='PRE source/database freeze mismatch',contract=contract,PRE=before)}
    def attempt(function):
        try: return function()
        except (ValueError,KeyError,FileNotFoundError,TypeError) as error:
            reason=str(error)
            return report('MATERIAL_UNAVAILABLE' if 'MATERIAL_UNAVAILABLE' in reason else 'FAIL',reason=reason)
    result={'harness':'FROI-1-acceptance-v1','category':'EXPERIMENTER','artifact_digest':artifact.digest,
        'T1':verify_t1(artifact)}
    result['T2']=attempt(lambda:run_t2(artifact,[read_history(database,v) for v in pair_versions])) if pair_versions else report('MATERIAL_UNAVAILABLE',reason='No explicitly specified paired real history prefixes')
    result['T3']=attempt(lambda:run_t3(artifact))
    result['T4']=attempt(lambda:trace_t4(database,limit_id)) if limit_id else report('MATERIAL_UNAVAILABLE',reason='No specified real read-failure consequence')
    if result['T4'].get('organization_statuses') and any(s!='COMPLETE' for s in result['T4']['organization_statuses']):
        result['T4'].update(status='NOT_TESTABLE',trace_integrity_status=result['T4']['status'],reason='Trace retained, but incomplete organization cannot satisfy formal acceptance')
    if continuation:
        if result['T2'].get('outputs'):
            from individual.internal_state import InternalState
            from individual.observation import ObservationFrame
            result['T2_continuations']=[]
            for saved,history in zip(result['T2']['outputs'],result['T2']['histories']):
                output=(InternalState.from_dict(saved['internal']),ObservationFrame(**saved['frame']),saved['journal'])
                result['T2_continuations'].append(attempt(lambda:detached_continue(artifact,output,intervention_history=unpack(history))))
        if result['T3']['status']=='PASS':
            branch=resume_detached(engine_for(artifact.checkpoint),artifact.checkpoint,artifact.handle,screen_effect=True)
            result['detached_continuation']=attempt(lambda:detached_continue(artifact,branch))
        else: result['detached_continuation']=report('NOT_TESTABLE',reason='T3 replay gate not passed')
    after=freeze(database)
    result['T5']=verify_t5(artifact,before,after,result)
    result['official_FROI_pass_claimed']=all(result[k]['status']=='PASS' for k in ('T1','T2','T3','T4','T5'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    export=commands.add_parser('export',help='Read-only export of an existing exact live read')
    export.add_argument('--database',required=True);export.add_argument('--version',type=int,required=True);export.add_argument('--output',required=True)
    run=commands.add_parser('validate',help='Explicitly execute detached acceptance on existing material')
    run.add_argument('--artifact',required=True);run.add_argument('--output',required=True)
    run.add_argument('--pair-versions',type=int,nargs=2);run.add_argument('--limit-id');run.add_argument('--continuation',action='store_true')
    args=parser.parse_args()
    if Path(args.output).exists(): parser.error('Output exists; historical evidence is never overwritten')
    try:
        if args.command=='export':
            artifact=export_artifact(args.database,args.version)
            external_write(args.output,artifact.serialize())
            print(json.dumps({'status':'PASS','export_only':True,'artifact_digest':artifact.digest}))
        else:
            artifact=ValidationArtifact.deserialize(Path(args.artifact).read_text(encoding='utf-8'))
            result=validate(artifact,pair_versions=args.pair_versions,limit_id=args.limit_id,continuation=args.continuation)
            external_write(args.output,json.dumps(result,ensure_ascii=False,indent=2))
            print(json.dumps({k:v['status'] for k,v in result.items() if isinstance(v,dict) and 'status' in v}))
    except (ValueError,KeyError,FileNotFoundError) as error:
        reason=str(error)
        status='MATERIAL_UNAVAILABLE' if 'MATERIAL_UNAVAILABLE' in reason or 'HISTORICAL_CHECKPOINT_NOT_RECONSTRUCTABLE' in reason else 'NOT_TESTABLE' if 'NOT_TESTABLE' in reason else 'FAIL'
        external_write(args.output,json.dumps(report(status,reason=reason),indent=2))
        print(json.dumps(report(status,reason=reason)))
        return 1
    return 0


if __name__=='__main__': raise SystemExit(main())
