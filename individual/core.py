"""One running subject state chain. Policy and external Supervisor stay separate."""

import argparse
from hashlib import sha256
from copy import deepcopy
from dataclasses import asdict, replace
import json
import math
from pathlib import Path
import queue
import signal
import sys
import threading
import time
from uuid import uuid4

from .bridge import BridgeError, MinecraftBridge, ROOT, parse_minecraft_port
from .events import EventStore
from .identity import ExperimentLease
from .actions import body_command, select_action
from .action_space import provision, bind_parameters, formal_command, DEFINITIONS
from .internal_state import InternalState
from .policies import PolicyRegistry
from .observation import FrameEncoder
from .structure import StructuralEngine
from .formal_l0 import FormalL0Engine, FormalLimits, select_uniform_action
from .formal_boundary import preflight, validate_boundary, normalize_resource_caps, sensor_caps
from .decision_provenance import decision_authorship
from .state import observation_fields, utc_now


class ACore:
    ACTION_METHODS = frozenset({'move', 'interact', 'chat'})

    def __init__(self, database, bridge, policy=None, observation_interval=1.0, session_context=None,
                 session_label='Minecraft', initialize_lifetime=False, experiment_profile='formal_l0', physical_caps=None,
                 resource_caps=None, froi=False, froi_caps=None, froi_async=False, worker_factory=None):
        if experiment_profile not in ('formal_l0', 'legacy_policy_debug'):
            raise ValueError('Unknown experiment profile')
        if not math.isfinite(observation_interval) or observation_interval <= 0:
            raise ValueError('Observation interval must be positive')
        if not initialize_lifetime and not Path(database).is_file():
            raise ValueError('An existing individual lifetime is required; session startup cannot create a replacement A')
        self._experiment_profile = 'legacy_policy_debug' if policy is not None else experiment_profile
        if froi and self._experiment_profile != 'formal_l0':
            raise ValueError('FROI requires the formal_l0 path')
        self._froi_async = froi and froi_async
        from integration.froi_worker import Worker
        self._worker_factory = worker_factory or Worker
        self._computation = None
        self._external_resources = None
        self._wait_controls = []
        self._froi = froi
        from integration.froi import load_caps, preflight as froi_preflight
        self._froi_caps = froi_caps if froi_caps is not None else load_caps()
        froi_preflight(database, froi, self._froi_caps)
        if froi:
            from .formal_froi import FormalFROIEngine
            self._engine = FormalFROIEngine(physical_caps, normalize_resource_caps(resource_caps), self._froi_caps)
        else:
            self._engine = (FormalL0Engine(physical_caps, normalize_resource_caps(resource_caps))
                            if self._experiment_profile == 'formal_l0' else StructuralEngine(physical_caps))
        if self._experiment_profile == 'formal_l0':
            preflight(database, self._engine.caps, self._engine.resource_caps)
        else:
            preflight(database, None)  # Refuse sealed formal history before any writes.
        self._lease = ExperimentLease(database).acquire()
        self._store = None
        try:
            preflight(database, self._engine.caps if self._experiment_profile == 'formal_l0' else None,
                      self._engine.resource_caps if self._experiment_profile == 'formal_l0' else None)
            self._store = EventStore(database)
            if not initialize_lifetime and self._store.latest_state() is None:
                raise ValueError('Session startup requires committed lifetime history')
            previous = self._store.latest_state()
            if (experiment_profile == 'legacy_policy_debug' or policy is not None) and previous and previous.internal_state.get('l0_state', {}).get('profile') == 'formal_l0':
                raise ValueError('Formal lifetime cannot resume through legacy adaptation; use an independent debug fixture')
            self._state = self._store.open_session({**(session_context or {}),
                'experiment_profile': self._experiment_profile, 'froi_enabled': froi,
                'froi_caps': asdict(self._froi_caps) if froi else None}, session_label,
                formal_caps=self._engine.caps if self._experiment_profile == 'formal_l0' else None,
                resource_caps=self._engine.resource_caps if self._experiment_profile == 'formal_l0' else None)
        except BaseException:
            if self._store:
                self._store.close()
            self._lease.release()
            raise
        self._bridge = bridge
        self._policy = policy  # Explicit debug injection only; absent in normal A.
        self._encoder = FrameEncoder(self._state.individual_id)
        self._body_epoch = self._state.carrier_epoch
        self._session_active = True
        self._await_fresh_observation = True
        self._pending_actions = []
        self._next_action = 0.0
        self._observation_interval = observation_interval
        self._next_observation = 0.0
        self._bridge_status = {'state': 'stopped', 'connected': False, 'attempt': 0}
        self._had_connection = False
        self._body_dead = False
        self._paused = False
        self._closed = False

    @property
    def state(self):
        return self._state.detached()

    def _transition(self, event_type, payload, additional_events=(), **changes):
        if self._closed:
            raise RuntimeError('A Core is closed')
        if changes.get('internal_state', {}).get('l0_state', {}).get('froi_detached_test_only'):
            raise ValueError('Detached FROI test state cannot be persisted to formal A')
        if self._experiment_profile == 'formal_l0':
            validate_boundary(self._state.internal_state, self._engine.caps, self._engine.resource_caps)
            validate_boundary(changes.get('internal_state', self._state.internal_state), self._engine.caps, self._engine.resource_caps)
        if not self._session_active:
            changes.setdefault('session_id', None)
        next_state = replace(self._state, state_version=self._state.state_version + 1,
                             last_update_at=utc_now(), **deepcopy(changes))
        self._store.transition(self._state, next_state, event_type, deepcopy(payload), deepcopy(additional_events))
        self._state = next_state
        return self.state

    def start(self):
        self._bridge.launch()
        self._transition('BRIDGE_PROCESS_STARTED', {'pid': self._bridge.pid}, status='connecting')
        try:
            self._bridge.call('start')
        except BridgeError as error:
            self._transition('BRIDGE_DISCONNECTED', {'code': error.code, 'message': str(error)}, status='waiting_for_bridge')
            if not self._bridge.alive:
                raise

    def accept_observation(self, observation):
        if not self._session_active:
            raise RuntimeError('Open a session before accepting environment observations')
        if self._computation is not None:
            raise RuntimeError('ONE_IN_FLIGHT_JOB: recursive checkpoint is frozen')
        fields = observation_fields(observation)
        sequence = self._state.environment_sequence + 1
        frame = self._encoder.encode(observation, sequence, self._body_epoch)
        if self._froi:
            from integration.froi import OrganizationSession, history_from_store
            organization = OrganizationSession(history_from_store(self._store, self._state), self._froi_caps)
            if self._froi_async:
                continuation = self._engine.advance_steps(self._state.internal_state, frame,
                    self._state.state_version + 1, self._pending_actions, organization=organization)
                try:
                    read_frame, feedback, version = next(continuation)
                except StopIteration as done:
                    internal, frame, journal = done.value
                else:
                    from integration.froi_worker import JobSpec
                    job = JobSpec.create(organization.history, read_frame, feedback, version,
                                         self._state.session_id, organization.caps)
                    try:
                        worker = self._worker_factory(job)
                    except Exception as error:
                        continuation.close()
                        self._transition('FROI_JOB_EXECUTION', {'job': job.audit(),
                            'execution_status': 'WORKER_FAILED', 'reason': str(error), 'partial_published': False})
                        raise RuntimeError('FROI host execution: WORKER_FAILED') from error
                    self._computation = {'job': job, 'worker': worker, 'continuation': continuation,
                        'observation': deepcopy(observation), 'fields': fields, 'sequence': sequence,
                        'base_version': self._state.state_version, 'base_internal': deepcopy(self._state.internal_state)}
                    return self.state
            else:
                internal, frame, journal = self._engine.advance(self._state.internal_state, frame,
                    self._state.state_version + 1, self._pending_actions, organization=organization)
        else:
            internal, frame, journal = self._engine.advance(self._state.internal_state, frame,
                                     self._state.state_version + 1, self._pending_actions)
        return self._commit_observation(observation, fields, sequence, internal, frame, journal)

    def _commit_observation(self, observation, fields, sequence, internal, frame, journal):
        provision(internal, observation.get('actionSpace'), self._state.state_version + 1, journal)
        if self._experiment_profile == 'formal_l0' and 'action.parameter_binding' in internal.policy_registry:
            internal.policy_registry['action.parameter_binding']['formal_path_enabled'] = True
        journal.append(('SENSOR_DEBUG_MAPPING', deepcopy(self._encoder.debug_mapping)))
        result = self._transition('WORLD_OBSERVATION', {'observation': deepcopy(observation), 'frame_id': frame.frame_id},
                                environment_sequence=sequence, internal_state=internal.to_dict(),
                                observation_frame=frame.to_dict(), additional_events=journal, **fields)
        self._pending_actions = []
        self._await_fresh_observation = False
        return result

    def _cancel_computation(self, reason, classification='CANCELLED'):
        pending = self._computation
        if pending is None:
            return
        pending['worker'].cancel()
        pending['continuation'].close()
        self._computation = None
        self._transition('FROI_JOB_EXECUTION', {'job': pending['job'].audit(),
            'execution_status': classification, 'reason': reason, 'partial_published': False},
            additional_events=self._wait_controls)
        self._wait_controls = []

    def _poll_computation(self):
        pending = self._computation
        result = pending['worker'].poll()
        if result is None:
            return
        from integration.froi_worker import validate_result
        from integration.froi import ReadResult, consume
        job = pending['job']
        classification = validate_result(job, result)
        if (self._state.individual_id != job.individual_id or self._state.session_id != job.session_id
            or self._state.state_version != pending['base_version']
            or self._state.internal_state != pending['base_internal']):
            classification = 'STALE_RESULT'
        if classification != 'RETURNED':
            self._cancel_computation(result.diagnostic or classification, classification)
            raise RuntimeError('FROI host execution: ' + classification)
        handle = result.handle
        read = consume(handle, handle.request) if handle else ReadResult('INVALID', (), (), (), (), ())
        try:
            pending['continuation'].send((handle, read, {'reason': result.diagnostic} if result.diagnostic else {}))
        except StopIteration as done:
            internal, frame, journal = done.value
        else:
            self._cancel_computation('Unexpected second checkpoint', 'WORKER_FAILED')
            raise RuntimeError('ONE_IN_FLIGHT_JOB: unexpected second read')
        pending['worker'].thread.join(timeout=0)
        self._computation = None
        journal.extend([('FROI_JOB_SUBMITTED', job.audit()), ('FROI_JOB_EXECUTION', {
            'job_id': job.job_id, 'execution_status': 'RETURNED',
            'computation_status': handle.status if handle else 'INVALID', 'exact_identity_verified': True}),
            *self._wait_controls])
        self._wait_controls = []
        self._commit_observation(pending['observation'], pending['fields'], pending['sequence'], internal, frame, journal)
        if pending.get('after_action'):
            self._next_observation = self._next_action = time.monotonic() + self._observation_interval
        else:
            # Resume the original tick's action stage. Starting another observation
            # first would starve that stage whenever every read requires a worker.
            self._next_observation = float('inf')
            self._next_action = time.monotonic()

    def accept_bridge_status(self, status, source=None):
        if not isinstance(status, dict) or 'state' not in status:
            raise ValueError('Invalid bridge status')
        previous = self._bridge_status
        if status == previous:
            return self.state
        if self._computation is not None:
            self._cancel_computation('bridge_status_changed')
        self._bridge_status = deepcopy(status)
        event_type = 'BRIDGE_STATE_CHANGED'
        runtime_status = 'waiting_for_bridge'
        ready = status.get('connected') and not status.get('lastError')
        if ready:
            if self._body_dead and previous.get('attempt') == status.get('attempt'):
                event_type = 'BODY_RESPAWNED'
            elif not previous.get('connected') or previous.get('lastError'):
                event_type = 'BRIDGE_RECONNECTED' if self._had_connection else 'BRIDGE_CONNECTED'
            self._had_connection = True
            self._body_dead = False
            runtime_status = 'running'
        elif status['state'] == 'dead':
            self._body_dead = True
            event_type = 'BODY_DIED'
            runtime_status = 'body_dead'
        elif status['state'] == 'spawning':
            event_type = 'BODY_RESPAWNING'
            runtime_status = 'waiting_for_spawn'
        elif previous.get('connected') or previous['state'] in ('dead', 'spawning'):
            event_type = 'BRIDGE_DISCONNECTED'
        elif status['state'] == 'connecting':
            runtime_status = 'connecting'
        changes = {}
        if event_type in ('BODY_DIED', 'BRIDGE_DISCONNECTED'):
            internal = InternalState.from_dict(self._state.internal_state) if self._state.internal_state else InternalState()
            incident = {'event_type': event_type, 'state_version': self._state.state_version + 1,
                        'frame_id': self._state.observation_frame.get('frame_id') if self._state.observation_frame else None,
                        'action_id': self._state.latest_action.get('action_id') if self._state.latest_action else None,
                        'carrier_only': True, 'subject_death_inferred': False, 'causality': 'unresolved'}
            internal.continuity_incidents = (internal.continuity_incidents + [incident])[-16:]
            internal.structure_revision += 1
            changes['internal_state'] = internal.to_dict()
        epoch = self._body_epoch + int(event_type in ('BODY_DIED', 'BRIDGE_DISCONNECTED', 'BRIDGE_RECONNECTED'))
        result = self._transition(event_type, {'previous': previous, 'current': status, 'source': source},
                                carrier_epoch=epoch,
                                status='paused' if self._paused else runtime_status, **changes)
        self._body_epoch = epoch
        return result

    def execute_action(self, action, initiator='policy'):
        if self._computation is not None:
            raise RuntimeError('No actions while computation checkpoint is frozen')
        if not self._session_active:
            raise RuntimeError('Actions require an active session')
        if self._policy is None and initiator != 'supervisor_pause':
            raise ValueError('Normal A uses only execute_discrete_action; raw body commands are debug-only')
        if not isinstance(action, dict) or action.get('method') not in self.ACTION_METHODS:
            raise ValueError('Only move/interact/chat body actions are allowed')
        args = action.get('args', {})
        if not isinstance(args, dict):
            raise ValueError('Action args must be an object')
        if self._await_fresh_observation and initiator != 'supervisor_pause':
            raise RuntimeError('A fresh session observation must precede an action')
        if self._paused and not (action['method'] == 'move' and args.get('direction') == 'stop'):
            raise RuntimeError('Actions are paused')
        requested = {'action_id': str(uuid4()), 'method': action['method'], 'args': deepcopy(args),
                     'status': 'requested', 'initiator': initiator}
        self._transition('ACTION_REQUESTED', requested, latest_action=requested)
        try:
            result = self._bridge.call(action['method'], deepcopy(args))
        except Exception as error:
            failed = {**requested, 'status': 'failed', 'error': {'code': getattr(error, 'code', 'ACTION_FAILED'), 'message': str(error)}}
            self._transition('ACTION_FAILED', failed, latest_action=failed)
            self._pending_actions.append({'action_id': failed['action_id'], 'action_code': -1, 'status': 'failed'})
            return False
        executed = {**requested, 'status': 'executed', 'result': result}
        self._transition('ACTION_EXECUTED', executed, latest_action=executed)
        self._pending_actions.append({'action_id': executed['action_id'], 'action_code': -1, 'status': 'executed'})
        return True

    def execute_discrete_action(self, action_code=None, parameters=None):
        if self._computation is not None:
            raise RuntimeError('No actions while computation checkpoint is frozen')
        if self._paused or self._closed or not self._session_active:
            raise RuntimeError('Actions are paused or stopped')
        if not self._state.observation_frame or self._await_fresh_observation:
            raise RuntimeError('An observation must precede an action')
        internal = InternalState.from_dict(self._state.internal_state)
        pattern = (internal.l0_state['current_pattern'] if self._experiment_profile == 'formal_l0' else
                   internal.observation_history_window[-1]['unit_id'])
        selector = select_uniform_action if self._experiment_profile == 'formal_l0' else select_action
        body = self._state.observation_frame['nearby_data'].get('body')
        if body:
            available = [entry['code'] for entry in body['action_space'] if entry['currently_available']]
            if action_code is None:
                action_code, selection = selector(internal, pattern, available)
                parameters = bind_parameters(action_code, self._state.observation_frame, internal, selection)
            else:
                if action_code not in DEFINITIONS:
                    raise ValueError('Unknown body capability code')
                selection = {'source': 'EXPLICIT_CAPABILITY_TEST', 'category': 'TEST_ONLY', 'reward': None}
                parameters = deepcopy(parameters or {})
            command = formal_command(action_code, parameters)
        else:
            if action_code is not None or parameters is not None:
                raise ValueError('Legacy test carrier has no formal parameterized action registry')
            action_code, selection = selector(internal, pattern, (0, 1, 2))
            command = body_command(action_code, PolicyRegistry(internal).parameters('body.actions')['duration_ms'])
        duration_ms = PolicyRegistry(internal).parameters('body.actions')['duration_ms']
        authorship = decision_authorship(selection)
        requested = {'action_id': str(uuid4()), 'action_code': action_code, 'status': 'requested',
            'initiator': authorship['initiator'],
            'method': command['method'] if command else 'wait',
            'args': deepcopy(command['args']) if command else {'durationMs': duration_ms},
            'provenance': {'source_state_version': self._state.state_version,
                'internal_state_before_version': self._state.state_version,
                'capability_category': 'BODY_CAPABILITY',
                'decision_authorship': authorship,
                'source_structure_revision': self._state.internal_state['structure_revision'],
                'frame_id': self._state.observation_frame['frame_id'],
                'integration_id': internal.latest_integration.get('integration_id'),
                'generation_id': internal.latest_generation.get('generation_id'), 'selection': selection}}
        internal.latest_action = deepcopy(requested)
        internal.structure_revision += 1
        effects = []
        if authorship['aggregate_source'] in ('EXTERNAL_FIXED_POLICY', 'MIXED_POLICY'):
            effects.append(('EXTERNAL_POLICY_EFFECT', {
                'action_id': requested['action_id'], 'source': authorship['aggregate_source'],
                'decision_authorship': deepcopy(authorship),
                'selection': deepcopy(selection), 'profile': self._experiment_profile,
                'parameter_binding': deepcopy(selection.get('parameter_binding'))}))
        self._transition('ACTION_REQUESTED', requested, additional_events=effects, latest_action=requested, internal_state=internal.to_dict())
        try:
            if command:
                result = self._bridge.call(command['method'], command['args'])
            else:
                time.sleep(duration_ms / 1000)
                result = {'waited_ms': duration_ms}
        except Exception as error:
            reason_code = getattr(error, 'code', 'ACTION_FAILED')
            final = {**requested, 'status': 'failed', 'reason_code': reason_code, 'error': {
                'code': reason_code, 'message': str(error), 'details': getattr(error, 'details', None)}}
            kind = 'ACTION_FAILED'
        else:
            final = {**requested, 'status': 'executed', 'result': result}
            kind = 'ACTION_EXECUTED'
        internal.latest_action = deepcopy(final)
        self._transition(kind, final, latest_action=final, internal_state=internal.to_dict())
        self._pending_actions.append({**{key: final[key] for key in ('action_id', 'action_code', 'status')},
            'parameters': deepcopy(parameters or {}), 'reason_code': final.get('reason_code')})
        return kind == 'ACTION_EXECUTED'

    def accept_resources(self, resources):
        if not isinstance(resources, dict):
            raise ValueError('Invalid external resource sample')
        internal = InternalState.from_dict(self._state.internal_state) if self._state.internal_state else InternalState()
        if self._computation is not None:
            self._external_resources = deepcopy(resources)
            return self.state
        internal.resource_state = deepcopy(resources)
        internal.structure_revision += 1
        return self._transition('RESOURCE_OBSERVED', resources, internal_state=internal.to_dict())

    def telemetry(self):
        state = self._state
        internal = state.internal_state
        delta = internal.get('detected_changes', {})
        structures = internal.get('latest_structure_changes', {})
        generation = internal.get('latest_generation', {})
        return deepcopy({'units': len(internal.get('units', {})), 'relations': len(internal.get('relations', {})),
                'active_processes': len(internal.get('active_processes', {})),
                'structure_revision': internal.get('structure_revision', 0),
                'revision_meaning': 'state_and_evidence_revision_not_layer_ascent',
                'experiment_profile': self._experiment_profile, 'active_recursive_layer': 'L0',
                'upward_recursion_observed': False,
                'computation_worker': self._computation['worker'].telemetry() if self._computation else None,
                'computation_wait': self._computation is not None,
                'external_resources_while_waiting': self._external_resources,
                'manual_paused': self._paused,
                'new_structures': structures.get('new', []),
                'removed_or_merged': structures.get('removed', []) + structures.get('merged', []),
                'observation_delta': {'change_id': delta.get('change_id'), 'changed': len(delta.get('changes', [])),
                                      'maintained': len(delta.get('maintained_channels', []))},
                'action': state.latest_action, 'resources': internal.get('resource_state', {}),
                'generation': {key: generation.get(key) for key in ('generation_id', 'root', 'requested_quantity',
                    'granted_quantity', 'feedback_integration_id', 'feedback_state_version', 'origin_state_version')},
                'integration_id': internal.get('latest_integration', {}).get('integration_id'),
                'policy_migration_status': PolicyRegistry(InternalState.from_dict(internal)).summary()})

    def pause(self):
        if not self._paused:
            self._paused = True
            if self._computation is not None:
                self._wait_controls.append(('SUPERVISOR_PAUSED', {'recursive_checkpoint_frozen': True,
                    'source': 'EXTERNAL_FIXED_MECHANISM'}))
                return
            self._transition('SUPERVISOR_PAUSED', {'observations_continue': True}, status='paused')
            if self._session_active and self._bridge_status.get('connected'):
                self.execute_action({'method': 'move', 'args': {'direction': 'stop'}}, initiator='supervisor_pause')

    def resume(self):
        if self._paused:
            self._paused = False
            if self._computation is not None:
                self._wait_controls.append(('SUPERVISOR_RESUMED', {'recursive_checkpoint_frozen': True}))
                return
            self._transition('SUPERVISOR_RESUMED', {}, status=('between_sessions' if not self._session_active else
                'running' if self._bridge_status.get('connected') else 'waiting_for_bridge'))

    def _observe(self):
        try:
            observation = self._bridge.call('observe')
        except BridgeError as error:
            self._transition('OBSERVATION_FAILED', {'code': error.code, 'message': str(error)})
            return
        try:
            self.accept_observation(observation)
        except ValueError as error:
            self._transition('INPUT_REJECTED', {'message': str(error)})

    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        for message in self._bridge.drain_events():
            if message['kind'] == 'lifecycle':
                self.accept_bridge_status(message['status'], source=message)
            elif message['kind'] in ('transport_error', 'exited'):
                self._transition('BRIDGE_DISCONNECTED', message, status='waiting_for_bridge')
                raise BridgeError('BRIDGE_EXITED', 'Bridge process stopped; experiment will terminate without restarting A')
        if not self._bridge.alive:
            raise BridgeError('BRIDGE_EXITED', 'Bridge process is not alive')
        if self._computation is not None:
            self._poll_computation()
            return
        if not self._session_active:
            return
        if (not self._bridge_status.get('connected') and self._bridge_status.get('state') != 'dead') or self._bridge_status.get('lastError'):
            return
        if now >= self._next_observation:
            self._observe()
            self._next_observation = now + self._observation_interval
        if self._computation is not None:
            return
        if not self._paused and not self._await_fresh_observation and self._policy is not None:
            action = self._policy.next_action(self.state, now)
            if action:
                success = self.execute_action(action)
                self._policy.action_finished(success, self.state)
                self._observe()
                if self._computation is not None:
                    self._computation['after_action'] = True
                self._next_observation = time.monotonic() + self._observation_interval
        elif not self._paused and now >= self._next_action and self._state.observation_frame and not self._await_fresh_observation:
            self.execute_discrete_action()
            self._observe()
            if self._computation is not None:
                self._computation['after_action'] = True
            self._next_action = time.monotonic() + self._observation_interval
            self._next_observation = self._next_action

    def end_session(self, reason='manual_session_end', carrier_stop=False):
        self._cancel_computation(reason)
        if self._closed:
            raise RuntimeError('A Core is closed')
        if self._session_active:
            self._state = self._store.end_session(self._state, reason, carrier_stop)
            self._session_active = False
            self._pending_actions = []  # Unobserved effects are not replayed across session boundaries.
            self._await_fresh_observation = True
        return self.state

    def begin_session(self, environment=None, label='Minecraft'):
        if self._closed or self._session_active:
            raise RuntimeError('End the current session before opening another')
        self._state = self._store.open_session({**(environment or {}), 'experiment_profile': self._experiment_profile}, label, carrier_restart=False,
            formal_caps=self._engine.caps if self._experiment_profile == 'formal_l0' else None,
            resource_caps=self._engine.resource_caps if self._experiment_profile == 'formal_l0' else None,
            runtime_status='paused' if self._paused else 'running' if self._bridge_status.get('connected') else 'waiting_for_bridge')
        self._session_active = True
        self._body_epoch = self._state.carrier_epoch
        self._await_fresh_observation = True
        self._next_observation = self._next_action = 0.0
        return self.state

    def shutdown(self, reason='manual_terminate'):
        if self._closed:
            return
        try:
            # Session shutdown never destroys lifetime structure or recursive lineage.
            if self._session_active:
                self.end_session(reason, carrier_stop=True)
            else:
                self._transition('CARRIER_STOPPED', {'reason': reason,
                    'lifetime_ended': False, 'physical_continuity_after_stop': 'unproven'}, status='dormant')
        finally:
            self._closed = True
            try:
                self._bridge.close()
            finally:
                self._store.close()
                self._lease.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db')
    parser.add_argument('--branch-db', help='Explicitly run a labeled snapshot branch, never the original mainline')
    parser.add_argument('--session-label', default='Minecraft')
    parser.add_argument('--minecraft-config', default=str(ROOT / 'minecraft/config.json'))
    parser.add_argument('--minecraft-port', type=parse_minecraft_port,
                        help='External connection override for this carrier run only')
    parser.add_argument('--observe-interval', type=float, default=0.5)
    parser.add_argument('--smoke-policy', action='store_true', help='Explicit stage-2 debug probe; not normal A')
    parser.add_argument('--legacy-policy-debug', action='store_true', help='Explicit old fixed-policy debug path; not formal evidence')
    parser.add_argument('--physical-caps', default=str(ROOT / 'individual/experiment.json'))
    parser.add_argument('--froi', action='store_true', help='FROI-1 organization relation-read integration; no action authorship claim')
    parser.add_argument('--froi-caps', help='External frozen GSC-0 capacity JSON for this lifetime')
    parser.add_argument('--environment-caps', type=json.loads, default={}, help='External Supervisor resource ceilings for this condition')
    parser.add_argument('--policy-wait', type=float, default=1.0)
    parser.add_argument('--move-ms', type=int, default=200)
    args = parser.parse_args()
    from .lifetime import resolve_runtime_database
    try:
        args.db = str(resolve_runtime_database(args.db, args.branch_db))
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if not math.isfinite(args.policy_wait) or args.policy_wait < 0 or not 1 <= args.move_ms <= 1000:
        parser.error('Policy wait must be nonnegative; movement probe must be 1–1000ms')
    controls = queue.Queue()
    output_lock = threading.Lock()

    def emit(kind, **payload):
        with output_lock:
            print(json.dumps({'kind': kind, **payload}, ensure_ascii=False), flush=True)

    def read_controls():
        for line in sys.stdin:
            try:
                message = json.loads(line)
                if message.get('command') in ('pause', 'resume', 'terminate', 'resource_sample', 'end_session', 'begin_session', 'new_session'):
                    controls.put(message)
            except (ValueError, AttributeError):
                pass
        controls.put({'command': 'terminate'})  # Parent disappearing ends this experiment.

    bridge = MinecraftBridge(args.minecraft_config, port=args.minecraft_port,
                             log=lambda text: print(text, file=sys.stderr, flush=True))
    core = None
    reason = 'manual_terminate'
    try:
        policy = None
        if args.smoke_policy:
            from debug.smoke_policy import DeterministicPolicy
            policy = DeterministicPolicy(args.policy_wait, args.move_ms)
        config_text = Path(args.minecraft_config).read_text(encoding='utf-8')
        config = json.loads(config_text)
        if 'body_observation_caps' in args.environment_caps and args.environment_caps['body_observation_caps'] != sensor_caps(args.minecraft_config):
            raise ValueError('Body sensor capacities changed between Supervisor preflight and Core startup')
        if args.minecraft_port is not None:
            config['port'] = args.minecraft_port
        context = {'minecraft_config': str(Path(args.minecraft_config).resolve()),
                   'configuration_hash': sha256(config_text.encode()).hexdigest(),
                   'minecraft_port_override': args.minecraft_port,
                   'minecraft_connection': {key: config.get(key) for key in ('host', 'port', 'username', 'version')},
                   'body_observation_config': config.get('observation', {}),
                   'observe_interval': args.observe_interval, 'smoke_policy': args.smoke_policy,
                   'experiment_profile': 'legacy_policy_debug' if args.legacy_policy_debug or args.smoke_policy else 'formal_l0',
                   'physical_caps': asdict(FormalLimits.load(args.physical_caps))}
        from integration.froi import load_caps as load_froi_caps
        core = ACore(args.db, bridge, policy, args.observe_interval, context, args.session_label,
                     experiment_profile=context['experiment_profile'],
                     physical_caps=FormalLimits.load(args.physical_caps) if context['experiment_profile']=='formal_l0' else None,
                     resource_caps=args.environment_caps, froi=args.froi,
                     froi_caps=load_froi_caps(args.froi_caps), froi_async=True)
        emit('CORE_STARTED', individual_id=core.state.individual_id, state_version=core.state.state_version,
             session_id=core.state.session_id, lifetime_role='snapshot_branch' if args.branch_db else 'mainline')
        threading.Thread(target=read_controls, daemon=True).start()
        signal.signal(signal.SIGINT, lambda *_: controls.put({'command': 'terminate'}))
        signal.signal(signal.SIGTERM, lambda *_: controls.put({'command': 'terminate'}))
        core.start()
        emit('BRIDGE_STARTED', pid=bridge.pid)
        heartbeat_at = 0.0
        while True:
            terminate = False
            while not controls.empty():
                message = controls.get_nowait()
                command = message['command']
                if command == 'terminate':
                    termination = message.get('payload') or {}
                    reason = termination.get('reason', 'manual_terminate')
                    core._cancel_computation(reason, termination.get('worker_execution_status', 'CANCELLED'))
                    terminate = True
                    break
                if command == 'resource_sample':
                    core.accept_resources(message['payload'])
                elif command == 'pause':
                    core.pause()
                elif command == 'resume':
                    core.resume()
                elif command == 'end_session':
                    core.end_session()
                    emit('SESSION_CHANGED', session_id=None, state_version=core.state.state_version)
                elif command in ('begin_session', 'new_session'):
                    if command == 'begin_session' and core._session_active:
                        emit('CONTROL_REJECTED', command=command, reason='session_already_active')
                        continue
                    if command == 'new_session':
                        core.end_session('manual_session_switch')
                    core.begin_session(context, args.session_label)
                    emit('SESSION_CHANGED', session_id=core.state.session_id, state_version=core.state.state_version)
            if terminate:
                break
            core.tick()
            if time.monotonic() >= heartbeat_at:
                snapshot = core.state
                emit('HEARTBEAT', individual_id=snapshot.individual_id, state_version=snapshot.state_version,
                     session_id=snapshot.session_id if core._session_active else None,
                     environment_sequence=snapshot.environment_sequence, status='paused' if core._paused else snapshot.status, bridge_pid=bridge.pid,
                     structure=core.telemetry())
                heartbeat_at = time.monotonic() + 1.0
            time.sleep(0.05)
    except Exception as error:
        reason = 'core_error'
        emit('CORE_ERROR', message=str(error))
        return_code = 1
    else:
        return_code = 0
    finally:
        if core:
            core.shutdown(reason)
            emit('CORE_STOPPED', individual_id=core.state.individual_id, state_version=core.state.state_version)
        else:
            bridge.close()
    return return_code


if __name__ == '__main__':
    sys.exit(main())
