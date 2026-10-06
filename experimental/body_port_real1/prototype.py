"""Offline real-history adapter and supported connection reader. Never executes."""
from dataclasses import dataclass, asdict
import json
import math
import sqlite3
from pathlib import Path

from experimental.body_port0.prototype import BodyPort, Member, Shared, Support, Organization, form
from individual.action_space import CATALOG_DATA, DEFINITIONS
from individual.observation import FrameEncoder, ObservationFrame
from individual.change_detection import detect_changes


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def number(value):
    if value is None:
        return ('absent', '')
    if type(value) is int:
        return ('int', str(value))
    if type(value) is float and math.isfinite(value):
        return ('float', value.hex())
    raise ValueError('Nonfinite/non-numeric change material')


@dataclass(frozen=True)
class Evidence:
    identity: str
    content: str


@dataclass(frozen=True)
class RealExperience:
    individual_id: str
    session_id: str
    experience_id: str
    action_id: str
    port: BodyPort
    execution_status: str
    before: Evidence
    after: Evidence
    receipt: Evidence
    experience: Evidence
    request: Evidence
    provisioning: Evidence
    raw_before: Evidence
    raw_after: Evidence
    session: Evidence

    @property
    def roots(self):
        return (self.before, self.after, self.receipt, self.experience, self.request,
                self.provisioning, self.raw_before, self.raw_after, self.session)


@dataclass(frozen=True)
class RealChange:
    scope: tuple
    changes: tuple


def payload(evidence):
    return json.loads(evidence.content)['payload']


def verified_change(e):
    """Validate actual records, preserving the full frames as independent roots."""
    if not isinstance(e.port, BodyPort) or any(not isinstance(r, Evidence) for r in e.roots):
        raise ValueError('Missing port identity or real input evidence')
    roots = tuple(json.loads(x.content) for x in e.roots[:-1])
    expected_types = ('OBSERVATION_FRAME', 'OBSERVATION_FRAME', 'ACTION_EXECUTED',
                      'EXPERIENCE_FORMED', 'ACTION_REQUESTED', 'BODY_CAPABILITIES_PROVISIONED',
                      'WORLD_OBSERVATION', 'WORLD_OBSERVATION')
    if tuple(r['event_type'] for r in roots) != expected_types:
        raise ValueError('Wrong source event types')
    if any(r['individual_id'] != e.individual_id or r['session_id'] != e.session_id for r in roots):
        raise ValueError('Cross-identity/session material')
    xp, req, receipt = payload(e.experience), payload(e.request), payload(e.receipt)
    before, after = payload(e.before), payload(e.after)
    raw_before, raw_after = payload(e.raw_before), payload(e.raw_after)
    session = json.loads(e.session.content)
    if session['session_id'] != e.session_id or session['individual_id'] != e.individual_id:
        raise ValueError('Wrong session provenance')
    if not session['environment'].get('minecraft_connection'):
        raise ValueError('No recorded Minecraft source')
    if (e.execution_status != 'executed' or receipt['status'] != 'executed'
            or req['status'] != 'requested' or req['method'] != 'perform'
            or receipt['method'] != 'perform' or receipt['action_id'] != e.action_id
            or req['action_id'] != e.action_id or xp['experience_id'] != e.experience_id
            or xp['action_ids'] != [e.action_id] or xp['action_statuses'] != ['executed']
            or xp['action_parameters'] != [{}] or xp['action_reason_codes'] != [None]
            or xp['causality'] != 'temporal_association_only'):
        raise ValueError('Not an unambiguous successful recorded execution')
    code = e.port.code
    definition = DEFINITIONS.get(code)
    installed = payload(e.provisioning)['after']
    native = [a for a in installed['actions'] if a['code'] == code]
    if (type(code) is not int or e.port.version != CATALOG_DATA['version']
            or installed['version'] != e.port.version or not definition
            or not definition['formal_enabled'] or definition['parameters']
            or len(native) != 1 or not native[0]['formal_enabled']
            or native[0]['parameter_schema']['properties']):
        raise ValueError('Not a recorded native parameterless primitive port')
    expected_args = {'code': code, 'parameters': {}}
    if (req['args'] != expected_args or receipt['args'] != expected_args
            or req['action_code'] != code or receipt['action_code'] != code or xp['action_code'] != code):
        raise ValueError('Action code/parameters identity mismatch')
    trace = receipt['result']
    if (trace['code'] != code or trace['parameters'] != {}
            or trace['result'] != {'input_sent': 1, 'effect_acknowledged': 0}
            or trace['effect_attribution'] != 'temporal_observation_only'
            or not trace.get('started_at') or not trace.get('finished_at')
            or 'before' not in trace or 'after' not in trace):
        raise ValueError('Incomplete real execution receipt')
    if (xp['frame_ids'] != [before['frame_id'], after['frame_id']]
            or xp['frame_id'] != after['frame_id'] or xp['sequence_id'] != after['sequence_id']
            or req['provenance']['frame_id'] != before['frame_id']
            or after['sequence_id'] != before['sequence_id'] + 1
            or (before['encoding_namespace'], before['body_epoch']) !=
               (after['encoding_namespace'], after['body_epoch'])):
        raise ValueError('Frame boundary mismatch')
    for frame, raw in ((before, raw_before), (after, raw_after)):
        if raw['frame_id'] != frame['frame_id']:
            raise ValueError('Raw frame identity mismatch')
        encoded = FrameEncoder(e.individual_id).encode(raw['observation'], frame['sequence_id'], frame['body_epoch'])
        if (canonical(encoded.numeric_channels) != canonical(frame['numeric_channels'])
                or encoded.encoding_namespace != frame['encoding_namespace']
                or encoded.timestamp != frame['timestamp']):
            raise ValueError('Raw observation/encoded frame disagreement')
    delta = detect_changes(ObservationFrame(**before), ObservationFrame(**after), [e.action_id]).to_dict()
    if (delta['sample_gap'] or canonical(delta) != canonical(after['delta'])
            or xp['change_id'] != delta['change_id'] or not delta['changes']):
        raise ValueError('Missing/inconsistent observed change')
    return RealChange((e.individual_id, before['encoding_namespace'], before['body_epoch'], e.port.version),
                      tuple((c['channel_id'], c['kind'], number(c['before']), number(c['after']), number(c['delta']))
                            for c in delta['changes']))


def encode_real(e):
    c = verified_change(e)
    facts = set(e.roots) | {e, c, e.port, Member(e.experience_id, c), Member(e.experience_id, e.port)}
    proofs = {Support(r, 'RECORDED_INPUT', frozenset()) for r in e.roots}
    proofs.add(Support(e, 'VERIFIED_REAL_EXPERIENCE', frozenset(e.roots)))
    proofs.add(Support(c, 'EXACT_RECORDED_DIFFERENCE', frozenset((e.before, e.after, e.raw_before, e.raw_after))))
    proofs.add(Support(e.port, 'NATIVE_EXECUTED_IDENTITY', frozenset((e, e.provisioning))))
    proofs.add(Support(Member(e.experience_id, c), 'RECORD_INCIDENCE', frozenset((e, c))))
    proofs.add(Support(Member(e.experience_id, e.port), 'RECORD_INCIDENCE', frozenset((e, e.port))))
    return Organization(frozenset(facts), frozenset(proofs), False), c


def connections(organization, current):
    """Read only supported formed organization; no raw history or execution."""
    if organization is None or not organization.complete:
        return {'status': 'UNRESOLVED', 'ports': ()}
    proofs = {}
    for p in organization.supports:
        proofs.setdefault(p.conclusion, set()).add(p)
    def supported(f, visiting=frozenset()):
        if f not in organization.facts or f in visiting:
            return False
        return any(all(supported(x, visiting | {f}) for x in p.premises) for p in proofs.get(f, ()))
    ports = set()
    for f in organization.facts:
        if isinstance(f, Shared) and current in f.endpoints and supported(f):
            ports.update(x for x in f.endpoints if isinstance(x, BodyPort) and supported(x)
                         and x.version == CATALOG_DATA['version'] and x.code in DEFINITIONS
                         and DEFINITIONS[x.code]['formal_enabled'] and not DEFINITIONS[x.code]['parameters'])
    result = tuple(sorted(ports, key=lambda p: (p.version, p.code)))
    return {'status': 'CONNECTED' if len(result) == 1 else 'AMBIGUOUS' if result else 'UNRESOLVED', 'ports': result}


def screen(organization, facts):
    """Detached access ablation only; never modifies records or recomputes."""
    return Organization(organization.facts - frozenset(facts), organization.supports, organization.complete)


def load_candidates(database):
    """Directed, read-only reads in one snapshot; all candidates, no result search."""
    conn = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA query_only=ON')
    conn.execute('BEGIN')
    rejected, accepted = [], []
    cutoff = conn.execute('SELECT MAX(event_sequence) FROM events').fetchone()[0]
    def one(kind, field, value):
        rows = conn.execute("SELECT e.*,ss.session_id FROM events e JOIN state_sessions ss USING(state_version) "
                            "WHERE event_type=? AND json_extract(payload,?)=?", (kind, '$.' + field, value)).fetchall()
        if len(rows) != 1:
            raise ValueError('Missing/ambiguous ' + kind)
        r = dict(rows[0]); r['payload'] = json.loads(r['payload'])
        return Evidence(r['event_id'], canonical(r))
    try:
        rows = conn.execute("SELECT event_id,json_extract(payload,'$.experience_id') FROM events "
                            "WHERE event_type='EXPERIENCE_FORMED' ORDER BY event_id").fetchall()
        for event_id, experience_id in rows:
            try:
                xp = one('EXPERIENCE_FORMED', 'experience_id', experience_id)
                x = payload(xp)
                if len(x['action_ids']) != 1:
                    raise ValueError('Non-single action interval')
                action_id = x['action_ids'][0]
                request = one('ACTION_REQUESTED', 'action_id', action_id)
                receipt = one('ACTION_EXECUTED', 'action_id', action_id)
                before, after = (one('OBSERVATION_FRAME', 'frame_id', f) for f in x['frame_ids'])
                raw_before, raw_after = (one('WORLD_OBSERVATION', 'frame_id', f) for f in x['frame_ids'])
                req_record = json.loads(request.content)
                provisioning_rows = conn.execute("SELECT e.*,ss.session_id FROM events e JOIN state_sessions ss USING(state_version) "
                                                  "WHERE event_type='BODY_CAPABILITIES_PROVISIONED' AND event_sequence<? "
                                                  "ORDER BY event_sequence DESC LIMIT 1", (req_record['event_sequence'],)).fetchall()
                if not provisioning_rows:
                    raise ValueError('No recorded capability catalog')
                pr = dict(provisioning_rows[0]); pr['payload'] = json.loads(pr['payload'])
                provisioning = Evidence(pr['event_id'], canonical(pr))
                session_id = req_record['session_id']
                sr = dict(conn.execute('SELECT * FROM sessions WHERE session_id=?', (session_id,)).fetchone())
                sr['environment'] = json.loads(sr['environment'])
                a, b = json.loads(raw_before.content)['event_sequence'], json.loads(raw_after.content)['event_sequence']
                r, t = req_record['event_sequence'], json.loads(receipt.content)['event_sequence']
                interval_actions = conn.execute("SELECT count(*) FROM events WHERE event_type='ACTION_REQUESTED' "
                                                "AND event_sequence>? AND event_sequence<?", (a, b)).fetchone()[0]
                if not a < r < t < b or interval_actions != 1:
                    raise ValueError('Execution not uniquely inside observed interval')
                e = RealExperience(req_record['individual_id'], session_id, experience_id, action_id,
                                   BodyPort(payload(provisioning)['after']['version'], x['action_code']),
                                   'executed', before, after, receipt, xp, request, provisioning,
                                   raw_before, raw_after, Evidence(session_id, canonical(sr)))
                verified_change(e)
                accepted.append(e)
            except (ValueError, KeyError, TypeError) as error:
                rejected.append({'event_id': event_id, 'experience_id': experience_id, 'reason': str(error)})
        accepted.sort(key=lambda e: (e.experience_id, e.experience.identity))
        return accepted, rejected, cutoff
    finally:
        conn.close()
