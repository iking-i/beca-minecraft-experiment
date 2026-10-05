"""External experiment audit boundary; never recursive input or a memory policy.

The immutable payload retains JSON object insertion order: FormalL0's mechanical
channel order and outcome iteration order are part of its execution state.
No Python generator, engine, EventStore, or mutable object is serialized.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from integration.froi import ReadRequest, ReferenceOrigin, canonical

SCHEMA = 'FROI-EXACT-READ-CHECKPOINT-1'
AUDIT_EVENT = 'FROI_READ_CHECKPOINT_AUDIT'


def ordered_json(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


@dataclass(frozen=True)
class ReadCheckpoint:
    content: str

    def __post_init__(self):
        p = json.loads(self.content)
        if ordered_json(p) != self.content or p['schema'] != SCHEMA:
            raise ValueError('Noncanonical or incompatible read checkpoint')
        if set(p) != {'schema', 'internal', 'frame', 'state_version', 'journal',
                'experience', 'feedback', 'prior_limits', 'new_limits', 'retained_frame',
                'delta', 'unit_id', 'pid', 'root', 'action_code', 'test_only',
                'caps', 'resource_caps', 'froi_caps', 'individual_id', 'session_id',
                'history_cutoff', 'request', 'request_error', 'job_id', 'job_input_digest'}:
            raise ValueError('Incomplete or unexpected checkpoint schema')
        request = self.request
        if request is not None and (
                request.individual_id != p['individual_id']
                or request.source_state_version != p['state_version']
                or request.frame_json != canonical(p['frame'])
                or request.reference != p['feedback'].get('next_relation_ref')):
            raise ValueError('ReadRequest checkpoint boundary mismatch')
        if self.requires_read and request is None and not p['request_error']:
            raise ValueError('Read checkpoint lacks an exact request or invalid-origin witness')
        if p['experience'] is not None:
            experience = p['experience']
            if (p['feedback'] != p['internal']['l0_state'].get('feedback', {})
                    or p['pid'] != p['internal']['l0_state'].get('process_id')
                    or p['pid'] not in p['internal']['active_processes']
                    or experience['root'] != p['root']
                    or experience['outcome'] != p['unit_id']
                    or experience['action_code'] != p['action_code']
                    or experience['frame_id'] != p['frame']['frame_id']
                    or experience['limit_consequences'] != p['frame']['internal_observations']
                    or p['frame']['internal_observations'] != p['prior_limits'] + p['new_limits']):
                raise ValueError('Continuation-local checkpoint inconsistency')

    @property
    def payload(self):
        return json.loads(self.content)

    @property
    def digest(self):
        return sha256(self.content.encode()).hexdigest()

    @property
    def frame(self):
        from individual.observation import ObservationFrame
        return ObservationFrame(**self.payload['frame'])

    @property
    def feedback(self):
        return self.payload['feedback']

    @property
    def request(self):
        value = self.payload['request']
        if value is None:
            return None
        return ReadRequest(**{**value, 'origin': ReferenceOrigin(**value['origin'])})

    @property
    def requires_read(self):
        p = self.payload
        return p['experience'] is not None and bool(p['feedback'].get('next_relation_ref'))

    def serialize(self):
        return canonical({'content': self.content, 'digest': self.digest})

    @classmethod
    def deserialize(cls, serialized):
        envelope = json.loads(serialized)
        if set(envelope) != {'content', 'digest'}:
            raise ValueError('Invalid checkpoint envelope')
        checkpoint = cls(envelope['content'])
        if envelope['digest'] != checkpoint.digest:
            raise ValueError('Checkpoint digest mismatch')
        return checkpoint

    @classmethod
    def capture(cls, engine, organization, internal, frame, state_version,
                journal, experience, feedback, prior_limits, new_limits,
                retained_frame, delta, unit_id, pid, root, action_code):
        request, error, cutoff, individual = None, None, None, None
        history = getattr(organization, 'history', None)
        supplied = getattr(organization, 'checkpoint_request', None)
        if history is not None:
            individual, cutoff = history.individual_id, history.event_cutoff
        elif supplied is not None:
            individual = supplied.individual_id
            cutoff = organization.history_cutoff
        if experience is not None and feedback.get('next_relation_ref'):
            try:
                origin = history.origin(feedback) if history is not None else supplied.origin
                request = ReadRequest(individual, state_version, canonical(frame.to_dict()),
                                      feedback['next_relation_ref'], origin)
            except (ValueError, KeyError, TypeError) as exc:
                error = str(exc)
        saved = dict(schema=SCHEMA, internal=internal.to_dict(), frame=frame.to_dict(),
            state_version=state_version, journal=journal, experience=experience,
            feedback=feedback, prior_limits=prior_limits, new_limits=new_limits,
            retained_frame=retained_frame, delta=delta, unit_id=unit_id, pid=pid,
            root=root, action_code=action_code, test_only=organization.test_only,
            caps=asdict(engine.caps), resource_caps=engine.resource_caps,
            froi_caps=asdict(engine.froi_caps), individual_id=individual,
            session_id=getattr(organization, 'session_id', None), history_cutoff=cutoff,
            request=asdict(request) if request else None, request_error=error,
            job_id=None, job_input_digest=None)
        checkpoint = cls(ordered_json(saved))
        if checkpoint.requires_read and history is not None:
            from integration.froi_worker import JobSpec
            job = JobSpec.create(history, frame, feedback, state_version,
                                 saved['session_id'], engine.froi_caps)
            checkpoint = checkpoint.bind_job(job)
        return checkpoint

    def bind_job(self, job):
        p = self.payload
        if (job.individual_id != p['individual_id'] or job.session_id != p['session_id']
                or job.source_state_version != p['state_version']
                or job.frame_json != canonical(p['frame'])
                or job.feedback_json != canonical(p['feedback'])
                or job.history.event_cutoff != p['history_cutoff']
                or job.caps_json != canonical(p['froi_caps'])):
            raise ValueError('Job checkpoint boundary mismatch')
        origin = json.loads(job.origin_json)
        if self.request is not None and origin.get('origin') != asdict(self.request.origin):
            raise ValueError('Job reference origin mismatch')
        if self.request is None and origin.get('invalid') != p['request_error']:
            raise ValueError('Job invalid-origin boundary mismatch')
        if p['job_id'] not in (None, job.job_id):
            raise ValueError('Checkpoint job identity changed')
        p['job_id'] = job.job_id
        p['job_input_digest'] = sha256(job.identity.encode()).hexdigest()
        return type(self)(ordered_json(p))

    def verify_engine(self, engine):
        p = self.payload
        if (p['caps'] != asdict(engine.caps) or p['resource_caps'] != engine.resource_caps
                or p['froi_caps'] != asdict(engine.froi_caps)):
            raise ValueError('Checkpoint interpreter capacities mismatch')
        from individual.formal_boundary import validate_boundary
        validate_boundary(p['internal'], engine.caps, engine.resource_caps)

    def verify_handle(self, handle):
        if not self.requires_read:
            if handle is not None:
                raise ValueError('No actual read at this checkpoint')
            return
        if handle is None:
            if self.request is not None:
                raise ValueError('Exact read checkpoint requires an organization result')
            return
        if handle.request != self.request or handle.history_cutoff != self.payload['history_cutoff']:
            raise ValueError('Organization checkpoint boundary mismatch')

    def artifact(self, handle):
        self.verify_handle(handle)
        p = self.payload
        return {'category': 'EXPERIMENT_AUDIT', 'recursive_input': False,
                'schema': SCHEMA, 'checkpoint': self.serialize(),
                'checkpoint_digest': self.digest, 'individual_id': p['individual_id'],
                'session_id': p['session_id'], 'state_version': p['state_version'],
                'frame_id': p['frame']['frame_id'],
                'q_t': p['feedback'].get('next_relation_ref'), 'job_id': p['job_id'],
                'organization_handle_digest': sha256(canonical(handle.audit()).encode()).hexdigest() if handle else None,
                'organization_graph_digest': handle.audit()['graph_digest'] if handle else None,
                'test_only': p['test_only']}
