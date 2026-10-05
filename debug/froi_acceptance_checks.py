"""Frozen EXPERIMENTER / TEST_ONLY T1--T5 facilities, never live runtime."""
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from uuid import UUID
from unittest.mock import patch

from experimental.gsc0.engine import Caps, Condition
from experimental.gsc0.model import encode
from individual.formal_froi import FormalFROIEngine
from individual.formal_l0 import FormalLimits
from individual.observation import FrameEncoder, ObservationFrame
from integration.froi import (VERSION, HISTORY_TYPES, ReadResult, OrganizationSession,
    canonical, consume, encode_input, produce, resume_detached)
from integration.froi_worker import JobSpec
from integration.read_checkpoint import AUDIT_EVENT
from debug.froi_acceptance_material import (ValidationArtifact, digest, freeze, pack,
    readonly, event_rows, read_history, ROOT, protected_files)

STATUSES = ('PASS','FAIL','PARTIAL','NOT_EXECUTED','NOT_TESTABLE','MATERIAL_UNAVAILABLE')
# Fixed observational boundaries. No result-dependent exclusions and no UUID
# wildcard: normal replay reinjects recorded post-read entropy in creation order.
EXTERNAL_JOURNAL_TYPES = frozenset(('WORLD_OBSERVATION','STATE_UPDATED',
    'SENSOR_DEBUG_MAPPING','FROI_JOB_SUBMITTED','FROI_JOB_EXECUTION',
    'BODY_INTERFACE_PARAMETER_UPDATED','BODY_CAPABILITIES_PROVISIONED'))
REPLAY_IGNORED_FIELDS = ('journal.FROI_READ_CHECKPOINT_AUDIT',)


def report(status, **evidence):
    if status not in STATUSES: raise ValueError('Invalid acceptance status')
    return {'status':status, **evidence}


def engine_for(cp):
    p = cp.payload
    return FormalFROIEngine(FormalLimits(**p['caps']), p['resource_caps'], Caps(**p['froi_caps']))


def contaminated(value):
    if isinstance(value, dict):
        if value.get('test_only') is True or value.get('category') in ('TEST_ONLY','TEST_FIXTURE'):
            return True
        if value.get('source') in ('TEST_ONLY','TEST_FIXTURE'): return True
        return any(contaminated(v) for v in value.values())
    if isinstance(value, list): return any(contaminated(v) for v in value)
    return False


def verify_t1(artifact, *, fixture_control=False):
    p, cp, h, handle = artifact.payload, artifact.checkpoint, artifact.history, artifact.handle
    if p['material_scope'] != 'FORMAL_RECORDED' and not fixture_control:
        return report('NOT_TESTABLE',reason='TEST_ONLY fixture is not live acceptance')
    try:
        # Independently reread the committed source; envelope hashes alone are insufficient.
        actual = read_history(p['database'], h.state_version)
        if actual != h: raise ValueError('History differs from complete recorded prefix')
        with readonly(p['database']) as db:
            rows = event_rows(db)
            original_state=json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=?',(cp.payload['state_version'],)).fetchone()[0])
            prior_state=json.loads(db.execute('SELECT snapshot FROM states WHERE state_version=?',(h.state_version,)).fetchone()[0])
        if rows != p['source_events']: raise ValueError('Source event material changed/missing/corrupt')
        round_rows=[r for r in rows if r['state_version']==cp.payload['state_version']]
        if round_rows != p['round_events'] or original_state != p['formal_snapshot']:
            raise ValueError('Original formal processing material changed')
        if p['event_range'] != [round_rows[0]['event_sequence'],round_rows[-1]['event_sequence']] or p['history_digest'] != digest(pack(h)):
            raise ValueError('Recorded event range/history digest mismatch')
        saved_cp=[r['payload'] for r in round_rows if r['event_type']==AUDIT_EVENT]
        saved_org=[r['payload'] for r in round_rows if r['event_type']=='FROI_ORGANIZATION_FORMED']
        if len(saved_cp)!=1 or saved_cp[0]['checkpoint']!=cp.serialize() or len(saved_org)!=1 or canonical(saved_org[0])!=canonical(handle.audit()):
            raise ValueError('Artifact differs from actual saved checkpoint/handle')
        if prior_state['internal_state']['l0_state']['feedback'] != cp.feedback:
            raise ValueError('Checkpoint query does not come from actual prior feedback')
        if not fixture_control and '.test-tmp' in __import__('pathlib').Path(p['database']).parts:
            raise ValueError('Known fixture database cannot be formal material')
        if cp.request.reference != cp.feedback['next_relation_ref'] or h.origin(cp.feedback) != cp.request.origin:
            raise ValueError('Query/origin is not actual unique feedback')
        records, _, _ = h.material()
        if any(r[0]['experience_id'] == cp.payload['experience']['experience_id'] for r in records):
            raise ValueError('Current incomplete experience used as history')
        if contaminated([json.loads(e) for e in h.events]): raise ValueError('TEST_ONLY historical input')
        for event in (json.loads(e) for e in h.events):
            if event['event_type']!='OBSERVATION_FRAME': continue
            old=event['payload']
            raw_sources=[r['payload'] for r in rows if r['event_type']=='WORLD_OBSERVATION'
                and r['state_version']==event['state_version'] and r['payload'].get('frame_id')==old['frame_id']]
            if len(raw_sources)!=1: raise ValueError('Historical frame lacks unique real WORLD_OBSERVATION')
            decoded=FrameEncoder(h.individual_id).encode(raw_sources[0]['observation'],old['sequence_id'],old['body_epoch']).to_dict()
            if any(decoded[k]!=old[k] for k in decoded if k not in ('delta','internal_observations')):
                raise ValueError('Historical raw world/frame encoding mismatch')
        frames = [r['payload'] for r in rows if r['state_version']==cp.payload['state_version'] and r['event_type']=='OBSERVATION_FRAME']
        worlds = [r['payload'] for r in rows if r['state_version']==cp.payload['state_version'] and r['event_type']=='WORLD_OBSERVATION']
        if len(frames)!=1 or len(worlds)!=1 or worlds[0]['frame_id'] != cp.frame.frame_id:
            raise ValueError('Current real observation/frame source unavailable')
        original = FrameEncoder(h.individual_id).encode(worlds[0]['observation'],cp.frame.sequence_id,cp.frame.body_epoch).to_dict()
        for key in original:
            if key not in ('delta','internal_observations') and original[key] != cp.payload['frame'][key]:
                raise ValueError('Raw world observation / checkpoint frame mismatch: '+key)
        for key in cp.payload['frame']:
            if key != 'internal_observations' and frames[0][key] != cp.payload['frame'][key]:
                raise ValueError('Recorded frame / checkpoint mismatch: '+key)
        encoded = encode_input(h, cp.request)
        if encoded.condition != handle.condition or encoded.registry_json != handle.registry_json:
            raise ValueError('Codec declarations/input registry mismatch')
        registry = json.loads(handle.registry_json)
        seed_pack = []
        for seed in encoded.seeds:
            if not all(s in registry for s in seed.sources): raise ValueError('Seed source missing')
            seed_pack.append({'key':seed.fact.key,'rule':seed.rule,'sources':seed.sources})
        # Exact root/input material, including declarations, is checked without closure.
        expected_records = {(s.fact.key,s.sources,s.rule) for s in encoded.seeds}
        if set(handle.input_records) != expected_records:
            raise ValueError('Encoded seed/input records mismatch (selection or corruption)')
        expected_roots = {('Root',s) for seed in encoded.seeds for s in seed.sources}
        expected_roots.update(('Root','DECL:'+encode(d.key)) for d in
            (*handle.condition.nodes,*handle.condition.values,*handle.condition.references))
        if set(handle.roots) != expected_roots:
            raise ValueError('Input/declaration root mismatch')
        support_keys=set(dict(handle.supports));witnesses=dict(handle.root_witnesses)
        if support_keys!={f.key for f in handle.graph} or set(witnesses)!=support_keys:
            raise ValueError('Graph lineage coverage mismatch')
        for roots in witnesses.values():
            if not roots or not set(roots)<=expected_roots: raise ValueError('Invalid finite root witness')
        job = JobSpec.create(h,cp.frame,cp.feedback,cp.payload['state_version'],cp.payload['session_id'],Caps(**cp.payload['froi_caps']))
        if cp.payload['job_id'] != job.job_id or cp.payload['job_input_digest'] != digest(json.loads(job.identity)):
            # job digest uses canonical identity text, equal to digest(decoded identity).
            raise ValueError('Job/source binding mismatch')
        if not handle.complete: return report('NOT_TESTABLE',reason='Organization incomplete')
        return report('PASS',scope='TEST_ONLY_ENGINEERING' if fixture_control else 'FORMAL_RECORDED',
            history_digest=digest(pack(h)),events=[json.loads(e)['event_id'] for e in h.events],
            records=[r[0]['experience_id'] for r in records],seed_evidence=seed_pack,
            condition=pack(encoded.condition),registry=registry,reference_origin=asdict(cp.request.origin))
    except (ValueError,KeyError,TypeError,FileNotFoundError) as error:
        return report('FAIL',reason=str(error))


def original_journal(artifact):
    return [(r['event_type'],r['payload']) for r in artifact.payload['round_events']
        if r['event_type'] not in EXTERNAL_JOURNAL_TYPES and r['event_type'] != AUDIT_EVENT]


def entropy_for_replay(cp, journal):
    prefix = [(k,p) for k,p in cp.payload['journal']]
    if canonical(journal[:len(prefix)]) != canonical(prefix):
        raise ValueError('Saved journal prefix differs from exact checkpoint')
    values = []
    for kind,p in journal[len(prefix):]:
        if kind == 'CURRENT_LIMIT_ENCOUNTER': values.append(UUID(p['limit_id']))
        elif kind == 'RECURSIVE_PARTIAL_OUTPUT': values.append(UUID(p['partial_id']))
        elif kind == 'INTEGRATION_COMPLETED': values.append(UUID(p['integration_id']))
    return values


def apply_recorded_commit_boundary(result, artifact):
    """Replay existing deterministic carrier provisioning, not action or A execution."""
    from individual.action_space import provision
    internal, frame, journal = result
    world = next(r['payload']['observation'] for r in artifact.payload['round_events'] if r['event_type']=='WORLD_OBSERVATION')
    provision(internal,world.get('actionSpace'),artifact.checkpoint.payload['state_version'],journal)
    if 'action.parameter_binding' in internal.policy_registry:
        internal.policy_registry['action.parameter_binding']['formal_path_enabled']=True
    return internal, frame, journal


def unscreened_replay(artifact):
    cp,handle=artifact.checkpoint,artifact.handle
    cp.verify_handle(handle)
    saved_consumed = [r['payload'] for r in artifact.payload['round_events'] if r['event_type']=='FROI_ORGANIZATION_CONSUMED']
    if len(saved_consumed)!=1: raise ValueError('Original consumed evidence unavailable')
    original = original_journal(artifact)
    entropy = entropy_for_replay(cp,original)
    with patch('individual.formal_froi.uuid4',side_effect=entropy) as entropy_source:
        output = engine_for(cp).resume_from_read_checkpoint(cp,handle,consume(handle,cp.request),saved_consumed[0]['diagnostics'])
    if entropy_source.call_count != len(entropy): raise ValueError('Replay UUID creation path mismatch')
    internal,frame,journal=apply_recorded_commit_boundary(output,artifact)
    actual_journal=[(k,p) for k,p in journal if k!=AUDIT_EVENT and k not in EXTERNAL_JOURNAL_TYPES]
    if canonical(actual_journal)!=canonical(original): raise ValueError('UNSCREENED_REPLAY journal mismatch')
    state=artifact.payload['formal_snapshot']
    if internal.to_dict()!=state['internal_state'] or frame.to_dict()!=state['observation_frame']:
        raise ValueError('UNSCREENED_REPLAY formal state/frame mismatch')
    return output


def causal_output(output):
    internal,frame,journal=output
    partial=next((p for k,p in journal if k=='RECURSIVE_PARTIAL_OUTPUT'),None)
    read=partial['processing']['organization_read'] if partial else None
    return {'read':read,'processing':partial['processing'] if partial else None,
        'experience':partial['experience'] if partial else None,
        'pending_consequences':internal.l0_state.get('pending_consequences'),
        'feedback':internal.l0_state.get('feedback'),'internal':internal.to_dict(),
        'frame':frame.to_dict(),'journal':journal}


def processing_effect(a,b):
    # Exclude UUID/log-only changes; actual consumer outcome/check/failure path required.
    pa,pb=causal_output(a)['processing'],causal_output(b)['processing']
    fields=('read_succeeded','expected_outcomes','same_context_as_prediction','outcome_previously_observed')
    return pa is not None and pb is not None and any(pa[k]!=pb[k] for k in fields)


def run_t3(artifact, *, fixture_control=False):
    t1=verify_t1(artifact,fixture_control=fixture_control)
    if t1['status']!='PASS': return report('NOT_TESTABLE',reason='T1 gate',T1=t1)
    try:
        unscreened_replay(artifact)
    except (ValueError,KeyError,TypeError,StopIteration) as error:
        return report('FAIL',reason=str(error),unscreened_replay='FAIL',ablation_executed=False)
    cp,handle=artifact.checkpoint,artifact.handle
    before=digest((cp.serialize(),pack(handle),pack(artifact.history)))
    normal=resume_detached(engine_for(cp),cp,handle)
    screened=resume_detached(engine_for(cp),cp,handle,screen_effect=True)
    if before!=digest((cp.serialize(),pack(handle),pack(artifact.history))):
        return report('FAIL',reason='Screening mutated input')
    return report('PASS' if processing_effect(normal,screened) else 'FAIL',
        unscreened_replay='PASS',checkpoint_digest=cp.digest,handle_digest=digest(handle.audit()),
        ignored_fields=REPLAY_IGNORED_FIELDS,normal=causal_output(normal),screened=causal_output(screened))


@dataclass(frozen=True)
class HistoricalIntervention:
    """TEST_ONLY adapter. Original checkpoint is NEVER edited/rebound.

    Different producer cutoffs are validated against each exact real prefix.
    This does not call or weaken ReadCheckpoint.verify_handle: the live contract
    remains rejecting the alternative cutoff. Only this external adapter is
    accepted by the common interpreter through its checkpoint protocol.
    """
    checkpoint: object
    history: object
    handle: object
    condition: object

    @property
    def payload(self): return self.checkpoint.payload
    @property
    def requires_read(self): return self.checkpoint.requires_read
    def verify_engine(self,engine): self.checkpoint.verify_engine(engine)
    def verify_handle(self,handle):
        if handle!=self.handle or handle.request!=self.checkpoint.request or handle.history_cutoff!=self.history.event_cutoff or handle.condition!=self.condition:
            raise ValueError('TEST_ONLY historical intervention identity mismatch')
        if handle.request.individual_id!=self.history.individual_id: raise ValueError('Cross-individual history')
    def artifact(self,handle):
        self.verify_handle(handle)
        return {'category':'TEST_ONLY','recursive_input':False,'intervention':'HISTORICAL_INPUT',
            'original_checkpoint_digest':self.checkpoint.digest,'original_history_cutoff':self.payload['history_cutoff'],
            'intervened_history_cutoff':self.history.event_cutoff,'history_digest':digest(pack(self.history)),
            'handle_digest':digest(handle.audit()),'test_only':True}


def run_t2(artifact, histories, *, fixture_control=False):
    gate=verify_t1(artifact,fixture_control=fixture_control)
    if gate['status']!='PASS': return report('NOT_TESTABLE',reason='T1 gate',T1=gate)
    cp=artifact.checkpoint
    if len(histories)!=2: return report('MATERIAL_UNAVAILABLE',reason='Two explicitly specified real prefixes required')
    try:
        for h in histories:
            if h!=read_history(artifact.payload['database'],h.state_version): raise ValueError('Fabricated/selected historical material')
            if contaminated([json.loads(e) for e in h.events]): raise ValueError('TEST_ONLY historical input')
            encode_input(h,cp.request)
        if histories[0]==histories[1]: return report('NOT_TESTABLE',reason='Histories identical')
        encoded=[encode_input(h,cp.request) for h in histories]
        ca,cb=(e.condition for e in encoded)
        union=lambda a,b:tuple(sorted(set(a)|set(b),key=lambda x:encode(x.key)))
        condition=Condition(union(ca.nodes,cb.nodes),union(ca.values,cb.values),ca.signatures,union(ca.references,cb.references),ca.version)
        handles=[produce(h,cp.request,Caps(**cp.payload['froi_caps']),condition) for h in histories]
        if any(not h.complete for h in handles):
            return report('NOT_TESTABLE',reason='Both COMPLETE required',organization_statuses=[h.status for h in handles])
        before=digest((cp.serialize(),pack(histories),pack(condition)))
        outputs=[]
        for history,handle in zip(histories,handles):
            boundary=HistoricalIntervention(cp,history,handle,condition)
            outputs.append(engine_for(cp).resume_from_read_checkpoint(boundary,handle,consume(handle,cp.request),
                {'category':'TEST_ONLY','historical_intervention':True,'fixed_checkpoint_digest':cp.digest},detached=True))
        if before!=digest((cp.serialize(),pack(histories),pack(condition))): raise ValueError('Historical intervention mutated controlled input')
        reads=[consume(h,cp.request) for h in handles]
        changed=handles[0].graph_content()!=handles[1].graph_content() and asdict(reads[0])!=asdict(reads[1]) and processing_effect(*outputs)
        return report('PASS' if changed else 'FAIL',condition=pack(condition),checkpoint_digest=cp.digest,
            provenance={'category':'TEST_ONLY','only_intervened_variable':'producer_history',
                'history_selection':'Explicit full-prefix boundaries supplied before production; no outcome search',
                'checkpoint_history_inconsistency_disclosed':True},
            histories=[pack(h) for h in histories],handles=[pack(h) for h in handles],
            reads=[asdict(r) for r in reads],outputs=[causal_output(o) for o in outputs])
    except (ValueError,KeyError,TypeError,FileNotFoundError) as error:
        return report('FAIL',reason=str(error))


def trace_t4(database,limit_id):
    with readonly(database) as db:
        rows=event_rows(db)
        snapshots={r[0]:json.loads(r[1]) for r in db.execute('SELECT state_version,snapshot FROM states')}
    encounters=[r for r in rows if r['event_type']=='CURRENT_LIMIT_ENCOUNTER' and r['payload']['limit_id']==limit_id]
    if len(encounters)!=1: return report('MATERIAL_UNAVAILABLE',reason='Unique actual consequence unavailable')
    event=encounters[0];raw=event['payload']['a_facing_payload'];version=event['state_version']
    consumed=[r for r in rows if r['state_version']==version and r['event_type']=='FROI_ORGANIZATION_CONSUMED']
    if len(consumed)!=1 or consumed[0]['payload']['status']=='READ_SUCCEEDED': return report('NOT_TESTABLE',reason='Not a read-failure consequence round')
    semantic=event['payload']['auditor_metadata']['semantic_code']
    if semantic!='FROI_'+consumed[0]['payload']['status']: return report('NOT_TESTABLE',reason='Consequence is not from organization read')
    following=[r for r in rows if r['state_version']>version and r['event_type']=='WORLD_OBSERVATION']
    if not following: return report('MATERIAL_UNAVAILABLE',reason='Next actual observation unavailable')
    next_version=following[0]['state_version']
    evidence={}
    def single(v,kind):
        matches=[r for r in rows if r['state_version']==v and r['event_type']==kind]
        if len(matches)!=1: raise ValueError('Missing/ambiguous '+kind)
        evidence[f'{v}:{kind}']=matches[0]
        return matches[0]['payload']
    try:
        evidence['encounter']=event
        single(version,'FROI_ORGANIZATION_FORMED');single(version,'FROI_ORGANIZATION_CONSUMED')
        for v in (version,next_version):
            exp=single(v,'EXPERIENCE_FORMED');part=single(v,'RECURSIVE_PARTIAL_OUTPUT');frame=single(v,'OBSERVATION_FRAME')
            if raw not in exp['limit_consequences'] or raw not in frame['internal_observations']:
                raise ValueError('Exact raw consequence lost or changed')
            if part['experience']!=exp or limit_id not in part['processing']['consumed_limit_ids']:
                raise ValueError('Partial does not consume exact consequence')
            feedback=single(v,'RECURSIVE_FEEDBACK_STORED')
            if feedback['partial_id']!=part['partial_id'] or limit_id not in feedback['observed_limit_ids']:
                raise ValueError('Feedback consequence/partial identity mismatch')
        state=snapshots[version]['internal_state']['l0_state']
        if raw not in state['pending_consequences']: raise ValueError('Pending raw consequence mismatch')
        reentry=single(next_version,'LIMIT_FEEDBACK_REENTERED_RECURSION')
        if limit_id not in reentry['limit_ids'] or reentry['partial_id']!=evidence[f'{next_version}:RECURSIVE_PARTIAL_OUTPUT']['payload']['partial_id']:
            raise ValueError('Reentry identity mismatch')
        return report('PASS',limit_id=limit_id,raw_consequence=raw,next_version=next_version,evidence=evidence,
            current_pending=state['pending_consequences'],next_observation=following[0],
            organization_statuses=[r['payload']['status'] for r in rows if r['state_version'] in (version,next_version) and r['event_type']=='FROI_ORGANIZATION_FORMED'])
    except (ValueError,KeyError) as error: return report('FAIL',reason=str(error),evidence=evidence)


def detached_continue(artifact, result, *, intervention_history=None):
    """One isolated continuation with the NEXT recorded raw observation, never a body."""
    cp=artifact.checkpoint;p=artifact.payload
    if not result[0].l0_state.get('froi_detached_test_only'): raise ValueError('Continuation must be detached')
    next_rows=[r for r in p['next_round_events'] if r['event_type']=='WORLD_OBSERVATION']
    if not next_rows: return report('MATERIAL_UNAVAILABLE',reason='Next recorded observation missing')
    next_row=next_rows[0]
    with readonly(p['database']) as db: actual=event_rows(db)
    if next_row not in actual: return report('FAIL',reason='Invented/corrupt observation')
    next_frame_rows=[r for r in actual if r['state_version']==next_row['state_version'] and r['event_type']=='OBSERVATION_FRAME']
    if len(next_frame_rows)!=1: return report('MATERIAL_UNAVAILABLE',reason='Exact next frame unavailable')
    epoch=next_frame_rows[0]['payload']['body_epoch']
    sequence=next_frame_rows[0]['payload']['sequence_id']
    if sequence!=result[1].sequence_id+1:
        return report('NOT_TESTABLE',reason='Recorded next observation is not the next frame in this isolated stream')
    frame=FrameEncoder(cp.request.individual_id).encode(next_row['payload']['observation'],sequence,epoch)
    # Isolated ledger consists of verified original H plus the branch's completed
    # input events. Generated records are explicitly TEST_ONLY, never real H pair.
    h=artifact.history if intervention_history is None else intervention_history
    if intervention_history is not None and (h!=read_history(p['database'],h.state_version) or h.individual_id!=cp.request.individual_id):
        return report('FAIL',reason='Unverified paired branch history')
    events=[json.loads(x) for x in h.events];seq=h.event_cutoff
    # The fixed checkpoint can refer to a prior real frame not contained in a
    # shorter intervened history. Supply ONLY those exact already recorded frame
    # materials required by the branch's newly completed experience, not missing
    # historical experience/answer records. This is disclosed TEST_ONLY input.
    present={e['payload']['frame_id'] for e in events if e['event_type']=='OBSERVATION_FRAME'}
    branch_frames={v['frame_id'] for k,v in result[2] if k=='OBSERVATION_FRAME'}
    needed={f for k,v in result[2] if k=='EXPERIENCE_FORMED' for f in v['frame_ids']}-present-branch_frames
    supplemental=[]
    for frame_id in sorted(needed):
        matches=[r for r in actual if r['event_type']=='OBSERVATION_FRAME' and r['payload']['frame_id']==frame_id
            and r['state_version']<cp.payload['state_version']]
        if len(matches)!=1: return report('MATERIAL_UNAVAILABLE',reason='Exact checkpoint-referenced prior real frame unavailable')
        source=matches[0];seq+=1;supplemental.append(source)
        events.append({**deepcopy(source),'event_sequence':seq,'event_id':'TEST_ONLY:CHECKPOINT_FRAME:'+source['event_id'],
            'state_version':cp.payload['state_version']})
    for index,(kind,payload) in enumerate(result[2]):
        if kind in HISTORY_TYPES:
            seq+=1;events.append({'event_sequence':seq,'event_id':f'TEST_ONLY:{cp.digest}:{index}',
                'individual_id':h.individual_id,'state_version':cp.payload['state_version'],
                'event_type':kind,'payload':deepcopy(payload)})
    from integration.froi import History
    isolated=History(h.individual_id,cp.payload['state_version'],seq,tuple(canonical(e) for e in events))
    session=OrganizationSession(isolated,Caps(**cp.payload['froi_caps']));session.test_only=True
    session.session_id=cp.payload['session_id']
    actions=[]
    for r in p['next_round_events']:
        if r['event_sequence']>=next_row['event_sequence']: break
        if r['event_type'] in ('ACTION_EXECUTED','ACTION_FAILED'):
            raw=r['payload'];actions.append({key:deepcopy(raw[key]) for key in ('action_id','action_code','status')})
            actions[-1]['parameters']=deepcopy(raw.get('parameters',{}));actions[-1]['reason_code']=raw.get('reason_code')
    output=engine_for(cp).advance(result[0].to_dict(),frame,cp.payload['state_version']+1,actions,organization=session)
    partial=next((v for k,v in output[2] if k=='RECURSIVE_PARTIAL_OUTPUT'),None)
    required=result[0].l0_state['pending_consequences']
    ok=partial is not None and all(x in partial['experience']['limit_consequences'] and x['limit_id'] in partial['processing']['consumed_limit_ids'] for x in required)
    return report('PASS' if ok else 'FAIL',category='TEST_ONLY',source_event=next_row,
        original_raw_pending=required,producer_history_digest=digest(pack(h)),
        checkpoint_frame_source_material=supplemental,
        isolated_history_digest=digest(pack(isolated)),output=causal_output(output))


def verify_t5(artifact, before, after, acceptance_evidence=None):
    cp=artifact.checkpoint;h=artifact.handle
    checks={'PRE_POST_source_and_database_invariance':before==after,
        'artifact_source_freeze_matches_PRE':artifact.payload['source_freeze']==before,
        'COMPLETE':h.complete,'codec_version':VERSION=='FROI-1',
        'checkpoint_handle_identity':h.request==cp.request and h.history_cutoff==cp.payload['history_cutoff'],
        'caps':cp.payload['froi_caps']==asdict(engine_for(cp).froi_caps),
        'checkpoint_not_recursive_input':AUDIT_EVENT not in HISTORY_TYPES,
        'fixture_exclusion':artifact.payload['material_scope']=='FORMAL_RECORDED'}
    # Code-level controls are frozen by exact hashes; their behavioral checks live
    # in engineering regressions. Never claim a keyword scan proves absence.
    checks['exact_codec_condition']=h.condition==encode_input(artifact.history,cp.request).condition
    checks['registry_identity']=h.registry_json==encode_input(artifact.history,cp.request).registry_json
    checks['frozen_behavior_contract']=frozen_contract()['status']=='PASS'
    used_statuses=[h.status]
    if acceptance_evidence:
        from debug.froi_acceptance_material import unpack
        used_statuses.extend(unpack(x).status for x in acceptance_evidence.get('T2',{}).get('handles',[]))
        used_statuses.extend(acceptance_evidence.get('T4',{}).get('organization_statuses',[]))
        continuation=acceptance_evidence.get('detached_continuation',{})
        read=continuation.get('output',{}).get('read')
        if read: used_statuses.append(read['organization_status'])
        for continuation in acceptance_evidence.get('T2_continuations',[]):
            read=continuation.get('output',{}).get('read')
            if read: used_statuses.append(read['organization_status'])
    checks['all_used_organizations_COMPLETE']=all(s=='COMPLETE' for s in used_statuses)
    return report('PASS' if all(checks.values()) else 'FAIL',checks=checks,PRE=before,POST=after,used_organization_statuses=used_statuses,
        protected_behavior_controls='See frozen engineering regression manifest; no result-dependent edits')


def frozen_contract():
    path=ROOT/'FROI_ACCEPTANCE_FREEZE.json'
    if not path.is_file(): return report('NOT_TESTABLE',reason='Harness not frozen')
    manifest=json.loads(path.read_text(encoding='utf-8'))
    current=protected_files()
    changes=[p for p,h in manifest['protected_source_hashes'].items() if current.get(p)!=h]
    additions=sorted(set(current)-set(manifest['protected_source_hashes']))
    regression=manifest['engineering_regression']
    checks={name:bool(regression['passed'] and not changes and not additions) for name in
        ('no_recent_N','no_pruning','no_Composition_skip','no_partial_as_COMPLETE',
         'no_old_relation_fallback','no_query_substitution','no_fixture_contamination',
         'no_favorable_record_selection','no_worker_fault_RESOURCE_LIMIT_relabel',
         'detached_persistence_rejected')}
    return report('PASS' if all(checks.values()) else 'FAIL',checks=checks,
        enforcement='Exact frozen source hashes bound to executed engineering controls; not keyword inference',
        changed=changes,added_sources=additions,freeze_source_commit=manifest['freeze_source_commit'])
