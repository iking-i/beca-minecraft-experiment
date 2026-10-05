"""Validate pre-existing v2 evidence without producer or interpreter execution."""
from dataclasses import asdict
import json

from debug.froi_acceptance_material import digest, pack, unpack, restore_saved_handle
from experimental.gsc0.engine import Condition
from experimental.gsc0.model import encode
from integration.froi import History, HISTORY_TYPES, canonical, consume, encode_input
from individual.observation import FrameEncoder
from tools.froi_acceptance_v2 import material as m, checks as v2

BASE = '9f7a8b7a4186ff58b7ed279f9f64071999644814'
SESSION = 'S-09272552-fb87-4078-871b-1c752b1d4862'
PAIR = [15, 12]
LABEL = 'TEST_ONLY HISTORICAL COUNTERFACTUAL WITNESS'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def single(journal, kind):
    values = [p for k, p in journal if k == kind]
    require(len(values) == 1, 'Missing/ambiguous ' + kind)
    return values[0]


def equal(a, b):
    return canonical(a) == canonical(b)


def verify_read_output(output, read, handle):
    audit = output['read']
    mapping = {'status': read.status, 'organization_status': handle.status,
               'closure_complete': handle.complete, 'consumed_keys': read.consumed_keys,
               'direct_supports': read.supports, 'root_witnesses': read.roots, 'conflicts': read.conflicts}
    require(all(equal(audit[k], v) for k, v in mapping.items()), 'Saved consumer structural evidence mismatch')
    require(output['processing']['expected_outcomes'] == list(read.outcomes)
            and output['processing']['read_succeeded'] == read.succeeded, 'Saved processing does not use actual read')


def verify_chain(branch, continuation):
    """Exact read-failure/consequence/pending/re-entry identities, not log-only."""
    journal = branch['journal']
    formed = single(journal, 'FROI_ORGANIZATION_FORMED')
    read = single(journal, 'FROI_ORGANIZATION_CONSUMED')
    require(formed['status'] == 'COMPLETE' and formed['closure_complete'], 'Failure organization incomplete')
    require(read['status'] == 'UNRESOLVED_REFERENCE' and read['organization_status'] == 'COMPLETE'
            and read['closure_complete'], 'Not the fixed COMPLETE unresolved branch')
    require(equal(branch['read'], read), 'Branch read differs from consumed event')
    failures = [p for k, p in journal if k == 'CURRENT_LIMIT_ENCOUNTER'
                and p['auditor_metadata'].get('semantic_code') == 'FROI_UNRESOLVED_REFERENCE']
    require(len(failures) == 1, 'Missing/ambiguous failure consequence')
    failure = failures[0]
    require(failure['auditor_metadata']['classification'] == 'TEST_ONLY_INTERVENTION', 'Failure mislabeled as live')
    raw = failure['a_facing_payload']
    lid = raw['limit_id']
    require(equal(branch['pending_consequences'], branch['internal']['l0_state']['pending_consequences']), 'Branch pending disagreement')
    require(equal(continuation['original_raw_pending'], branch['pending_consequences']), 'Continuation did not receive exact pending state')
    require(continuation['category'] == 'TEST_ONLY', 'Continuation mislabeled')
    for output in (branch, continuation['output']):
        partial = single(output['journal'], 'RECURSIVE_PARTIAL_OUTPUT')
        feedback = single(output['journal'], 'RECURSIVE_FEEDBACK_STORED')
        experience = single(output['journal'], 'EXPERIENCE_FORMED')
        frame = single(output['journal'], 'OBSERVATION_FRAME')
        require(equal(partial['experience'], experience) and equal(output['experience'], experience), 'Experience identity mismatch')
        require(equal(partial['processing'], output['processing']) and equal(output['frame'], frame), 'Processing/frame mismatch')
        require(equal(feedback, output['feedback']) and equal(feedback, output['internal']['l0_state']['feedback']), 'Feedback mismatch')
        require(raw in frame['internal_observations'] and raw in experience['limit_consequences'], 'Exact raw consequence lost/changed')
        require(lid in partial['processing']['consumed_limit_ids'], 'Partial did not consume exact consequence')
        require(lid in feedback['observed_limit_ids'] and feedback['partial_id'] == partial['partial_id'], 'Feedback/partial identity mismatch')
    require(raw in branch['pending_consequences'], 'Failure missing from pending')
    out = continuation['output']
    reentry = single(out['journal'], 'LIMIT_FEEDBACK_REENTERED_RECURSION')
    partial = single(out['journal'], 'RECURSIVE_PARTIAL_OUTPUT')
    require(lid in reentry['limit_ids'] and reentry['partial_id'] == partial['partial_id']
            and reentry['frame_id'] == out['frame']['frame_id'], 'Re-entry identity mismatch')
    require(out['frame']['sequence_id'] == branch['frame']['sequence_id'] + 1, 'Not one consecutive continuation round')
    next_org = single(out['journal'], 'FROI_ORGANIZATION_FORMED')
    require(next_org['status'] == 'COMPLETE' and next_org['closure_complete'], 'Continuation organization incomplete')
    require(out['read']['organization_status'] == 'COMPLETE' and out['read']['closure_complete'], 'Continuation consumed incomplete organization')
    return {'limit_id': lid, 'raw_consequence': raw, 'category': LABEL,
            'test_only': True, 'formal_live_natural_failure': False,
            'organization_statuses': [formed['status'], next_org['status']],
            'checks': {'exact_raw_pending_frame_experience_partial_feedback_reentry': True}}


def validate_plan(plan, old_report):
    require(plan['versions'] == [16, 20, 22, 25] and plan['pair_versions'] == PAIR
            and plan['session'] == SESSION, 'Pre-existing selection differs')
    require(old_report['measurement_commit'] == BASE and old_report['FROI1_ACCEPTANCE'] == 'PARTIAL', 'Not frozen v2 historical report')
    require(old_report['session']['session_id'] == SESSION, 'Wrong session')


def isolated_history(cp, history, branch, continuation):
    """Reconstruct the SAVED v2 ledger only; no engine or producer call."""
    events = [json.loads(e) for e in history.events]
    seq = history.event_cutoff
    present = {e['payload']['frame_id'] for e in events if e['event_type'] == 'OBSERVATION_FRAME'}
    frames = {v['frame_id'] for k, v in branch['journal'] if k == 'OBSERVATION_FRAME'}
    needed = {f for k, v in branch['journal'] if k == 'EXPERIENCE_FORMED' for f in v['frame_ids']} - present - frames
    supplemental = continuation['checkpoint_frame_source_material']
    require([r['payload']['frame_id'] for r in supplemental] == sorted(needed), 'Supplemental material exceeds exact checkpoint frame needs')
    for row in supplemental:
        seq += 1
        events.append({**row, 'event_sequence': seq, 'event_id': 'TEST_ONLY:CHECKPOINT_FRAME:' + row['event_id'],
                       'state_version': cp.payload['state_version']})
    for index, (kind, payload) in enumerate(branch['journal']):
        if kind in HISTORY_TYPES:
            seq += 1
            events.append({'event_sequence': seq, 'event_id': f'TEST_ONLY:{cp.digest}:{index}',
                           'individual_id': history.individual_id, 'state_version': cp.payload['state_version'],
                           'event_type': kind, 'payload': payload})
    h = History(history.individual_id, cp.payload['state_version'], seq, tuple(canonical(e) for e in events))
    require(digest(pack(history)) == continuation['producer_history_digest']
            and digest(pack(h)) == continuation['isolated_history_digest'], 'Saved continuation history binding mismatch')
    return h


def validate_saved(artifact, evidence, plan, old_report):
    validate_plan(plan, old_report)
    cp = artifact.checkpoint
    require(cp.payload['state_version'] == 16 and cp.payload['session_id'] == SESSION, 'Not fixed A16 checkpoint')
    t2, t3 = evidence['T2'], evidence['T3']
    require(t2['status'] == t3['status'] == 'PASS', 'Missing prior executed T2/T3')
    require(t2['checkpoint_digest'] == t3['checkpoint_digest'] == cp.digest, 'Checkpoint mismatch')
    histories = [unpack(x) for x in t2['histories']]
    handles = [unpack(x) for x in t2['handles']]
    require(len(histories) == len(handles) == len(t2['outputs']) == len(t2['reads']) == len(evidence['T2_continuations']) == 2, 'Fixed two-branch cardinality mismatch')
    require([h.state_version for h in histories] == PAIR, 'History reselection')
    require(t2['provenance']['category'] == 'TEST_ONLY' and t2['provenance']['only_intervened_variable'] == 'producer_history', 'Counterfactual provenance mismatch')
    encoded = [encode_input(h, cp.request) for h in histories]
    ca, cb = [e.condition for e in encoded]
    union = lambda a, b: tuple(sorted(set(a) | set(b), key=lambda x: encode(x.key)))
    condition = Condition(union(ca.nodes, cb.nodes), union(ca.values, cb.values), ca.signatures,
                          union(ca.references, cb.references), ca.version)
    require(unpack(t2['condition']) == condition, 'Joint Condition changed')
    with m.readonly(artifact.payload['database']) as db:
        expected_next = next(m.events(db, after=max(r['event_sequence'] for r in artifact.payload['round_events']), types=('WORLD_OBSERVATION',)))
        for i, (h, handle, block) in enumerate(zip(histories, handles, encoded)):
            require(h == m.read_history(artifact.payload['database'], PAIR[i]), 'History differs from real complete prefix')
            require(handle.complete and handle.request == cp.request and handle.condition == condition
                    and handle.history_cutoff == h.event_cutoff, 'T2 handle boundary mismatch/incomplete')
            registry = json.loads(block.registry_json)
            for declaration in (*condition.nodes, *condition.values, *condition.references):
                registry['DECL:' + encode(declaration.key)] = {'source': 'EXTERNAL_FIXED_MECHANISM',
                    'codec': 'FROI-1', 'declaration': declaration.key}
            require(handle.registry_json == canonical(registry)
                    and set(handle.input_records) == {(s.fact.key, s.sources, s.rule) for s in block.seeds}, 'T2 seed/registry mismatch')
            read = consume(handle, cp.request)
            require(equal(asdict(read), t2['reads'][i]), 'Saved T2 read differs from actual frozen consumer')
            branch = t2['outputs'][i]
            require(equal(single(branch['journal'], 'FROI_ORGANIZATION_FORMED'), handle.audit()), 'Branch handle/graph differs')
            verify_read_output(branch, read, handle)
            require(equal(branch['journal'][:len(cp.payload['journal'])], cp.payload['journal']), 'Branch did not use same exact checkpoint prefix')
            continuation = evidence['T2_continuations'][i]
            require(continuation['status'] == 'PASS' and continuation['source_event'] == expected_next, 'Continuation not from fixed next real observation')
            for row in continuation['checkpoint_frame_source_material']:
                actual = list(m.events(db, version=row['state_version'], types=('OBSERVATION_FRAME',)))
                require(row in actual, 'Invented supplemental checkpoint frame')
            ih = isolated_history(cp, h, branch, continuation)
            output = continuation['output']
            audit = single(output['journal'], 'FROI_ORGANIZATION_FORMED')
            # Restore the saved handle with its exact serialized request, never recompute closure.
            from integration.froi import ReadRequest, ReferenceOrigin
            read_frame = audit['input_registry']['CURRENT_FRAME:' + audit['current_frame_id']]['frame']
            request = ReadRequest(audit['individual_id'], audit['source_state_version'], canonical(read_frame),
                                  audit['requested_reference'], ReferenceOrigin(**audit['reference_origin']))
            require(request.source_state_version == 17 and request.frame['frame_id'] == output['frame']['frame_id'], 'Continuation request/frame mismatch')
            require(request.reference == branch['feedback']['next_relation_ref'] and request.origin == ih.origin(branch['feedback']), 'Continuation query/origin mismatch')
            next_handle = restore_saved_handle(audit, ih, request)
            require(next_handle.complete, 'Continuation incomplete')
            next_read = consume(next_handle, request)
            verify_read_output(output, next_read, next_handle)
            decoded = FrameEncoder(h.individual_id).encode(expected_next['payload']['observation'], output['frame']['sequence_id'], output['frame']['body_epoch']).to_dict()
            require(all(equal(decoded[k], output['frame'][k]) for k in decoded if k not in ('delta', 'internal_observations')), 'Continuation frame differs from real observation')
    require([r['status'] for r in t2['reads']] == ['READ_SUCCEEDED', 'UNRESOLVED_REFERENCE'], 'Not fixed failure branch')
    require(handles[0].graph_content() != handles[1].graph_content(), 'No organization difference')
    fields = ('read_succeeded', 'expected_outcomes', 'same_context_as_prediction', 'outcome_previously_observed')
    require(any(t2['outputs'][0]['processing'][k] != t2['outputs'][1]['processing'][k] for k in fields), 'T2 log-only difference')
    require(t3['unscreened_replay'] == 'PASS' and t3['handle_digest'] == digest(artifact.handle.audit()), 'Prior strict T3 replay missing/mismatched')
    cp.verify_handle(artifact.handle)
    verify_read_output(t3['normal'], consume(artifact.handle, cp.request), artifact.handle)
    require(t3['normal']['read']['status'] == consume(artifact.handle, cp.request).status
            and t3['screened']['read']['status'] == 'TEST_ONLY_EFFECT_SCREENED', 'T3 read mismatch')
    require(any(t3['normal']['processing'][k] != t3['screened']['processing'][k] for k in fields), 'T3 log-only difference')
    witness = verify_chain(t2['outputs'][1], evidence['T2_continuations'][1])
    require(witness['raw_consequence']['object_refs'] == [cp.request.reference]
            and witness['raw_consequence']['source_state_version'] == 16
            and witness['raw_consequence']['frame_id'] == cp.frame.frame_id, 'Failure is not bound to exact query/frame/version')
    return {'T1': v2.verify_t1(artifact), 'T2': {'status': 'PASS', 'evidence': 'verified saved v2 T2'},
            'T3': {'status': 'PASS', 'evidence': 'verified saved v2 strict replay/ablation'},
            'T4': {'status': 'PASS', **witness}, 'T4_WITNESS_SOURCE': LABEL}
