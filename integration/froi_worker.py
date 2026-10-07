"""Task-scoped compute carrier. No EventStore, mutable A, selector or rule changes."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
import pickle
import subprocess
import sys
import threading
import psutil

from experimental.gsc0.engine import Caps
from integration.froi import VERSION, ReadRequest, canonical, encode_input, produce


@dataclass(frozen=True)
class JobSpec:
    individual_id: str
    session_id: str | None
    source_state_version: int
    history: object
    frame_json: str
    feedback_json: str
    caps_json: str
    origin_json: str
    codec_version: str = VERSION
    froi_version: str = VERSION

    @classmethod
    def create(cls, history, frame, feedback, version, session_id, caps):
        try:
            origin = {'origin': asdict(history.origin(feedback))}
        except (ValueError, KeyError, TypeError) as error:
            origin = {'invalid': str(error)}
        return cls(history.individual_id, session_id, version, history,
                   canonical(frame.to_dict()), canonical(feedback), canonical(asdict(caps)), canonical(origin))

    @property
    def identity(self):
        # Complete immutable input material binds the mechanically reconstructed
        # Condition/seeds, not merely frame ID or a query label.
        return canonical(asdict(self))

    @property
    def job_id(self):
        return 'FROI-J-' + sha256(self.identity.encode()).hexdigest()

    def audit(self):
        audit = {'job_id': self.job_id, 'individual_id': self.individual_id,
                'session_id': self.session_id, 'source_state_version': self.source_state_version,
                'history_state_version': self.history.state_version,
                'history_cutoff': self.history.event_cutoff,
                'current_frame_id': json.loads(self.frame_json)['frame_id'],
                'requested_reference': json.loads(self.feedback_json)['next_relation_ref'],
                'reference_origin': json.loads(self.origin_json),
                'codec_version': self.codec_version, 'froi_version': self.froi_version,
                'caps': json.loads(self.caps_json), 'immutable_input_identity': self.identity,
                'source': 'EXTERNAL_FIXED_MECHANISM'}
        if hasattr(self.history, 'encode_current'):
            audit['runtime_source'] = {'version': self.history.version,
                                     'external_history_loaded': False,
                                     'cutoff_kind': 'state_version'}
        return audit


@dataclass(frozen=True)
class JobResult:
    job_id: str
    input_identity: str
    execution_status: str
    handle: object = None
    diagnostic: str = ''


def execute(job):
    """Only existing produce() defines COMPLETE / RESOURCE_LIMIT / INVALID."""
    from integration.froi import ReferenceOrigin
    if job.codec_version != VERSION or job.froi_version != VERSION:
        raise ValueError('Unsupported frozen interface version')
    origin = json.loads(job.origin_json)
    if 'invalid' in origin:
        return JobResult(job.job_id, job.identity, 'RETURNED', diagnostic=origin['invalid'])
    request = ReadRequest(job.individual_id, job.source_state_version, job.frame_json,
                          json.loads(job.feedback_json)['next_relation_ref'], ReferenceOrigin(**origin['origin']))
    handle = produce(job.history, request, Caps(**json.loads(job.caps_json)))
    return JobResult(job.job_id, job.identity, 'RETURNED', handle)


def validate_result(job, result):
    if result.job_id != job.job_id or result.input_identity != job.identity:
        return 'STALE_RESULT'
    if result.execution_status != 'RETURNED':
        return result.execution_status
    handle = result.handle
    if handle is not None:
        origin = json.loads(job.origin_json).get('origin')
        if (handle.request.individual_id != job.individual_id
            or handle.request.source_state_version != job.source_state_version
            or handle.request.frame_json != job.frame_json
            or handle.request.reference != json.loads(job.feedback_json)['next_relation_ref']
            or asdict(handle.request.origin) != origin
            or handle.history_cutoff != job.history.event_cutoff):
            return 'STALE_RESULT'
        if handle.condition is not None:
            try:
                if handle.condition != encode_input(job.history, handle.request).condition:
                    return 'STALE_RESULT'
            except (ValueError, KeyError, TypeError):
                return 'STALE_RESULT'
    elif 'invalid' not in json.loads(job.origin_json):
        return 'WORKER_FAILED'
    return 'RETURNED'


class Worker:
    """One process per job; pipe I/O runs outside the Core control loop."""
    def __init__(self, job, command=None):
        self.job = job
        self.result = None
        self.cancelled = False
        self.process = subprocess.Popen(command or [sys.executable, '-u', '-m', 'integration.froi_worker'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, 'PYTHONUTF8': '1'})
        self.thread = threading.Thread(target=self._exchange, daemon=True)
        self.thread.start()

    def _exchange(self):
        try:
            output, errors = self.process.communicate(pickle.dumps(self.job))
            if self.cancelled:
                return
            if self.process.returncode:
                self.result = JobResult(self.job.job_id, self.job.identity, 'WORKER_EXITED',
                    diagnostic=errors.decode('utf8', errors='replace'))
            else:
                result = pickle.loads(output)
                if not isinstance(result, JobResult):
                    raise ValueError('Invalid worker result envelope')
                self.result = result
        except Exception as error:
            if not self.cancelled:
                self.result = JobResult(self.job.job_id, self.job.identity, 'WORKER_FAILED', diagnostic=str(error))

    def poll(self):
        return self.result

    def cancel(self):
        self.cancelled = True
        try:
            children = psutil.Process(self.process.pid).children(recursive=True)
        except psutil.NoSuchProcess:
            children = []
        # Windows venv launchers may own a real Python child. Reap the entire
        # task carrier, not just its launcher, using handles owned by this job.
        for child in reversed(children):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        if self.process.poll() is None:
            self.process.kill()
        self.thread.join(timeout=2)
        self.process.wait(timeout=2)
        psutil.wait_procs(children, timeout=2)
        return JobResult(self.job.job_id, self.job.identity, 'CANCELLED')

    def telemetry(self):
        return {'pid': self.process.pid, 'job_id': self.job.job_id,
                'alive': self.process.poll() is None, 'waiting': self.result is None,
                'source': 'EXTERNAL_FIXED_MECHANISM', 'subject': False}


def main():
    # -m executes this file as __main__; serialize the stable importable classes.
    from integration.froi_worker import execute as run_job, JobResult as Envelope
    job = pickle.load(sys.stdin.buffer)  # Private local parent/child pipe, not network input.
    try:
        result = run_job(job)
    except Exception as error:
        result = Envelope(job.job_id, job.identity, 'WORKER_FAILED', diagnostic=repr(error))
    pickle.dump(result, sys.stdout.buffer)
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
