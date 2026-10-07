"""TEST_ONLY offline memory-input control. Never starts a body or canonical A.

Each measurement runs in a separate process with an isolated temporary audit DB.
Optionally use one read-only persisted A-state snapshot, never its event history.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import pickle
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

import psutil

from individual.core import ACore
from individual.observation import FrameEncoder, ObservationFrame
from individual.state import AState
from integration.current_structure import current_organization
from integration.froi import consume
from integration.froi_worker import JobSpec, execute, validate_result
from tests.test_core import FakeBridge
from tests.test_structure import observation


def measure(count, source_db=None):
    Path('.test-tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir='.test-tmp') as directory:
        core = ACore(Path(directory) / 'TEST_ONLY.db', FakeBridge(),
                     initialize_lifetime=True, froi=True)
        try:
            for _ in range(3):
                core.accept_observation(observation())
            state = core.state
            if source_db:
                db = sqlite3.connect(Path(source_db).resolve().as_uri() + '?mode=ro', uri=True)
                try:
                    db.execute('PRAGMA query_only=ON')
                    raw = db.execute('select snapshot from states order by state_version desc limit 1').fetchone()[0]
                    state = AState(**json.loads(raw))
                finally:
                    db.close()
                from individual.formal_froi import FormalFROIEngine
                from individual.formal_l0 import FormalLimits
                from experimental.gsc0.engine import Caps
                local = state.internal_state['l0_state']
                core._engine = FormalFROIEngine(FormalLimits(**local['locked_caps']),
                    local['locked_resource_caps'], Caps(**local['froi_boundary']['caps']))
                core._froi_caps = core._engine.froi_caps
            with core._store.connection:
                for _ in range(count):
                    core._store._insert_event(core._state, 'OBSERVATION_FRAME',
                        {'TEST_ONLY_EXTERNAL_SENTINEL': 'x' * 2048})
            external = core._store.connection.execute('select count(*) from events').fetchone()[0]
            # No SELECT of external events is permitted during measured preparation.
            def authorize(action, table, *rest):
                return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and table == 'events' else sqlite3.SQLITE_OK
            core._store.connection.set_authorizer(authorize)
            process = psutil.Process()
            before = process.memory_info().rss
            peak = [before]
            stop = threading.Event()
            def sample():
                while not stop.wait(.005):
                    peak[0] = max(peak[0], process.memory_info().rss)
            sampler = threading.Thread(target=sample, daemon=True)
            sampler.start()
            try:
                for _ in range(10):
                    session = current_organization(core._store, state, core._froi_caps)
                    session.session_id = state.session_id
                    if source_db:
                        frame = replace(ObservationFrame(**state.observation_frame),
                            sequence_id=state.environment_sequence + 1,
                            frame_id=f'{state.individual_id}:E{state.environment_sequence + 1}')
                    else:
                        frame = FrameEncoder(state.individual_id).encode(observation(),
                            state.environment_sequence + 1, state.carrier_epoch)
                    cp = core._engine.prepare_read_checkpoint(state.internal_state, frame,
                        state.state_version + 1, [], organization=session)
                    job = JobSpec.create(session.history, cp.frame, cp.feedback,
                        state.state_version + 1, state.session_id, session.caps)
                    result = execute(job)
                    if validate_result(job, result) != 'RETURNED':
                        raise AssertionError('Invalid pressure result')
                    read = consume(result.handle, result.handle.request)
                    job_size, cp_size = len(pickle.dumps(job)), len(cp.serialize().encode())
                    status = result.handle.status
                    peak[0] = max(peak[0], process.memory_info().rss)
                    del session, frame, cp, job, result, read
                after = process.memory_info().rss
            finally:
                stop.set(); sampler.join()
            return {'test_only': True, 'extra_external_events': count,
                    'external_event_count': external,
                    'current_internal_state_bytes': len(json.dumps(state.internal_state, separators=(',', ':')).encode()),
                    'runtime_job_bytes': job_size, 'checkpoint_bytes': cp_size,
                    'rss_before_mib': before / 2**20, 'rss_after_release_mib': after / 2**20,
                    'sampled_peak_mib': peak[0] / 2**20,
                    'organization_status': status, 'preparations': 10,
                    'external_history_reads': 0}
        finally:
            core._store.connection.set_authorizer(None)
            core.shutdown('TEST_ONLY pressure complete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', type=int)
    parser.add_argument('--current-state-db')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.child is not None:
        print(json.dumps(measure(args.child, args.current_state_db)))
        return
    measurements = []
    for count in (0, 1000, 10000):
        command = [sys.executable, '-m', 'debug.current_structure_pressure', '--child', str(count)]
        if args.current_state_db:
            command.extend(['--current-state-db', str(Path(args.current_state_db).resolve())])
        run = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf8')
        measurements.append(json.loads(run.stdout))
    report = {'test_only': True, 'canonical_db_written': False, 'measurements': measurements,
              'job_size_independent_of_external_history': len({r['runtime_job_bytes'] for r in measurements}) == 1,
              'external_history_reads': 0}
    print(json.dumps(report, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    if not report['job_size_independent_of_external_history']:
        raise SystemExit('Job input changes with external history')


if __name__ == '__main__':
    main()
