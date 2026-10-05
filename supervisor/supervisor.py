"""Parent process monitors Core/Bridge and owns pause, resume and termination."""

import argparse
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import threading
import time

import psutil
import yaml

from individual.state import utc_now

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIMITS = dict(sample_interval_seconds=0.5, max_core_ram_mb=512,
                      max_bridge_ram_mb=1024, max_total_cpu_percent=200,
                      cpu_violation_samples=5, heartbeat_timeout_seconds=45,
                      shutdown_grace_seconds=6, max_runtime_seconds=0, max_lifetime_storage_mb=65536)


def load_limits(path):
    supplied = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    if not isinstance(supplied, dict) or set(supplied) - DEFAULT_LIMITS.keys():
        raise ValueError('Invalid Supervisor limits')
    limits = {**DEFAULT_LIMITS, **supplied}
    for key, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'Invalid resource limit: {key}')
        if value < 0 or (key != 'max_runtime_seconds' and value == 0):
            raise ValueError(f'Resource limit must be positive: {key}')
    if not isinstance(limits['cpu_violation_samples'], int):
        raise ValueError('cpu_violation_samples must be an integer')
    return limits


class Supervisor:
    def __init__(self, database, limits, log=print):
        self.database = Path(database).resolve()
        self.limits = deepcopy(limits)
        self.log = log
        self.process = None
        self._core = None
        self._bridge = None
        self._owned_children = {}
        self._messages = queue.Queue()
        self._controls = queue.Queue()
        self._threads = []
        self._heartbeat = None
        self._session_id = None
        self._last_heartbeat = None
        self._started_at = None
        self._stopping_at = None
        self._stop_reason = None
        self._cpu_violations = 0
        self._sample = None
        self._closed = False
        self._audit_path = self.database.with_name(self.database.stem + '.supervisor.db')
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        self._audit = sqlite3.connect(self._audit_path)
        self._audit.execute('CREATE TABLE IF NOT EXISTS supervisor_events(sequence INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, event_type TEXT, payload TEXT)')
        self._record('SUPERVISOR_STARTED', {'limits': self.limits, 'subject_member': False})

    def _record(self, kind, payload):
        with self._audit:
            self._audit.execute('INSERT INTO supervisor_events(timestamp,event_type,payload) VALUES (?,?,?)',
                                (utc_now(), kind, json.dumps(payload, ensure_ascii=False, allow_nan=False)))

    def start(self, core_args=None, command=None):
        if self.process is not None:
            raise RuntimeError('Supervisor already started')
        argv = command or [sys.executable, '-u', '-m', 'individual.core', '--db', str(self.database), *(core_args or [])]
        env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONUNBUFFERED': '1'}
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        self.process = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1,
                                        env=env, creationflags=flags, start_new_session=os.name != 'nt')
        self._core = psutil.Process(self.process.pid)
        self._core.cpu_percent()
        self._started_at = time.monotonic()
        for target in (self._read_output, self._read_errors):
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            self._threads.append(thread)
        self._record('CORE_LAUNCHED', {'pid': self.process.pid})

    def _read_output(self):
        for line in self.process.stdout:
            try:
                self._messages.put(json.loads(line))
            except ValueError:
                self._messages.put({'kind': 'INVALID_CORE_OUTPUT', 'line': line.rstrip()})

    def _read_errors(self):
        for line in self.process.stderr:
            self.log(f'[Body/Core] {line.rstrip()}')

    def control(self, command):
        if command not in ('pause', 'resume', 'terminate', 'end_session', 'begin_session', 'new_session'):
            raise ValueError('Only lifecycle/session controls are available')
        self._controls.put(command)

    def status(self):
        return deepcopy({'core_pid': self.process.pid if self.process else None,
                         'bridge_pid': self._bridge.pid if self._bridge else None,
                         'heartbeat': self._heartbeat, 'resources': self._sample,
                         'stopping': self._stopping_at is not None,
                         'stop_reason': self._stop_reason, 'session_id': self._session_id})

    def _send(self, command, payload=None):
        try:
            if self.process.poll() is None:
                self.process.stdin.write(json.dumps({'command': command, 'payload': payload}) + '\n')
                self.process.stdin.flush()
        except (OSError, ValueError):
            pass

    def _drain_messages(self):
        while True:
            try:
                message = self._messages.get_nowait()
            except queue.Empty:
                return
            kind = message.get('kind')
            if kind not in ('CORE_STARTED', 'BRIDGE_STARTED', 'HEARTBEAT', 'CORE_ERROR', 'CORE_STOPPED', 'SESSION_CHANGED'):
                self._record('IGNORED_CORE_OUTPUT', message)
                continue
            self._record(kind, message)
            if kind == 'HEARTBEAT':
                self._heartbeat = message
                self._last_heartbeat = time.monotonic()
                self.log(json.dumps(message, ensure_ascii=False, separators=(',', ':')))
            elif kind == 'CORE_STARTED':
                self._session_id = message.get('session_id')
                if message.get('lifetime_role') == 'snapshot_branch':
                    self.log('快照实验分支：不是原始 A 主线。')
                self.log(f"Individual: {message['individual_id']} | SQLite: {self.database}")
                self.log(f"Session: {self._session_id} | Continuing at A{message['state_version']}")
            elif kind == 'SESSION_CHANGED':
                self._session_id = message['session_id']
                self.log(f"Session: {self._session_id} | A{message['state_version']}; lifetime preserved")
            elif kind == 'CORE_ERROR':
                self.log(f"Core error: {message.get('message')}")
            # Outbound messages are telemetry only. They cannot change limits or send controls.

    def _process_sample(self, process):
        if process is None:
            return {'alive': False, 'cpu_percent': 0.0, 'ram_mb': 0.0}
        try:
            return {'pid': process.pid, 'alive': process.is_running() and process.status() != psutil.STATUS_ZOMBIE,
                    'cpu_percent': process.cpu_percent(interval=None),
                    'ram_mb': process.memory_info().rss / (1024 * 1024)}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {'pid': process.pid, 'alive': False, 'cpu_percent': 0.0, 'ram_mb': 0.0}

    def _collect(self):
        try:
            children = self._core.children(recursive=True)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            children = []
        for child in children:
            if child.pid not in self._owned_children:
                child.cpu_percent()
                self._owned_children[child.pid] = child
            try:
                if child.name().lower() in ('node', 'node.exe'):
                    self._bridge = self._owned_children[child.pid]
            except psutil.NoSuchProcess:
                pass
        core = self._process_sample(self._core)
        # Include a possible Windows venv launcher/real Python child in Core usage.
        for process in self._owned_children.values():
            if self._bridge and process.pid == self._bridge.pid:
                continue
            extra = self._process_sample(process)
            core['cpu_percent'] += extra['cpu_percent']
            core['ram_mb'] += extra['ram_mb']
        bridge = self._process_sample(self._bridge)
        self._sample = {'timestamp': utc_now(), 'core': core, 'bridge': bridge}
        self._sample['storage'] = {'used_mb': sum(p.stat().st_size for p in self.database.parent.iterdir()
            if p.is_file() and (p.name.startswith(self.database.name) or p.name.startswith(self._audit_path.name))) / (1024 * 1024),
            'max_mb': self.limits['max_lifetime_storage_mb'], 'source': 'ENVIRONMENT_CONSTRAINT'}
        self._sample['pressure'] = max(core['ram_mb'] / self.limits['max_core_ram_mb'],
            bridge['ram_mb'] / self.limits['max_bridge_ram_mb'],
            (core['cpu_percent'] + bridge['cpu_percent']) / self.limits['max_total_cpu_percent'])
        self._record('RESOURCE_SAMPLE', self._sample)
        if self._stopping_at is None:
            self._send('resource_sample', self._sample)
        return self._sample

    def _request_termination(self, reason):
        if self._stopping_at is not None:
            return
        self._stop_reason = reason
        self._stopping_at = time.monotonic()
        self._record('TERMINATION_REQUESTED', {'reason': reason})
        self._send('terminate')

    def _enforce(self, sample):
        core, bridge = sample['core'], sample['bridge']
        if sample.get('storage', {}).get('used_mb', 0) > self.limits['max_lifetime_storage_mb']:
            self._request_termination('lifetime_storage_limit')
        if core['ram_mb'] > self.limits['max_core_ram_mb']:
            self._request_termination('core_ram_limit')
        elif bridge['ram_mb'] > self.limits['max_bridge_ram_mb']:
            self._request_termination('bridge_ram_limit')
        if core['cpu_percent'] + bridge['cpu_percent'] > self.limits['max_total_cpu_percent']:
            self._cpu_violations += 1
        else:
            self._cpu_violations = 0
        if self._cpu_violations >= self.limits['cpu_violation_samples']:
            self._request_termination('cpu_limit')
        if self._bridge is not None and not bridge['alive']:
            self._request_termination('bridge_process_exited')

    def _kill_owned(self):
        # Handles are only descendants discovered by the parent, never arbitrary Core-supplied PIDs.
        for child in reversed(list(self._owned_children.values())):
            try:
                if child.is_running():
                    child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if self.process and self.process.poll() is None:
            self.process.kill()
        if self.process:
            self.process.wait(timeout=5)

    def run(self, duration=0, verify_loop=False):
        if self.process is None:
            raise RuntimeError('Supervisor has not launched the Core')
        next_sample = 0.0
        next_verification = 0.0
        duration = duration or self.limits['max_runtime_seconds']
        try:
            while self.process.poll() is None:
                self._drain_messages()
                while not self._controls.empty():
                    command = self._controls.get_nowait()
                    self._record('MANUAL_CONTROL', {'command': command})
                    if command == 'terminate':
                        self._request_termination('manual_terminate')
                    elif self._stopping_at is None:
                        self._send(command)
                now = time.monotonic()
                if duration and now - self._started_at >= duration:
                    self._request_termination('runtime_limit')
                if now >= next_sample:
                    sample = self._collect()
                    if self._stopping_at is None:
                        self._enforce(sample)
                    next_sample = now + self.limits['sample_interval_seconds']
                if verify_loop and self._session_id and self._stopping_at is None and now >= next_verification and self.database.exists():
                    from individual.experiment_audit import audit
                    try:
                        proof = audit(self.database, check_chain=False, session_id=self._session_id)
                    except (sqlite3.Error, ValueError):
                        proof = None  # Database initialization may still be in progress.
                    if proof and proof.get('baseline_goal_observed'):
                        self._record('EXPERIMENT_ACCEPTED', {key: proof[key] for key in (
                            'checks', 'counts', 'processes_with_repeated_publications', 'recognition_status')})
                        self.log('V0-A/V0-B baseline evidence recorded; architecture recognition remains not_observed.')
                        self._request_termination('verification_complete')
                    next_verification = now + 2.0
                heartbeat_at = self._last_heartbeat or self._started_at
                if now - heartbeat_at > self.limits['heartbeat_timeout_seconds']:
                    self._request_termination('core_unresponsive')
                if self._stopping_at is not None and now - self._stopping_at > self.limits['shutdown_grace_seconds']:
                    self._record('FORCED_TERMINATION', {'reason': self._stop_reason,
                                 'final_core_event_not_guaranteed': True})
                    self._kill_owned()
                    break
                time.sleep(0.05)
        except KeyboardInterrupt:
            self._request_termination('manual_terminate')
            deadline = time.monotonic() + self.limits['shutdown_grace_seconds']
            while self.process.poll() is None and time.monotonic() < deadline:
                self._drain_messages()
                time.sleep(0.05)
            if self.process.poll() is None:
                self._record('FORCED_TERMINATION', {'reason': 'manual_terminate', 'final_core_event_not_guaranteed': True})
                self._kill_owned()
        finally:
            if self.process.poll() is not None:
                self._kill_owned()
                for thread in self._threads:
                    thread.join(timeout=1)
                self._drain_messages()
                self._record('SUPERVISOR_STOPPED', {'core_exit_code': self.process.returncode, 'reason': self._stop_reason})
                for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                    stream.close()
                self._audit.close()
                self._closed = True
        return self.process.returncode or (1 if self._stop_reason not in (None, 'manual_terminate', 'runtime_limit', 'verification_complete') else 0)

    def close(self):
        if self._closed:
            return
        try:
            if self.process:
                self._collect()
                self._kill_owned()
        finally:
            if self.process:
                for thread in self._threads:
                    thread.join(timeout=1)
                for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                    if not stream.closed:
                        stream.close()
            self._audit.close()
            self._closed = True


def cli():
    parser = argparse.ArgumentParser(description='BECA-V0 formal L0: V0-A/V0-B baseline')
    parser.add_argument('--db', help='Compatibility: must name the pinned lifetime database')
    parser.add_argument('--branch-db', help='Explicit snapshot branch; never the original A mainline')
    parser.add_argument('--session-label', default='Minecraft')
    parser.add_argument('--minecraft-config', default=str(ROOT / 'minecraft/config.json'))
    from individual.bridge import parse_minecraft_port
    connection = parser.add_mutually_exclusive_group()
    connection.add_argument('--minecraft-port', '--port', type=parse_minecraft_port,
                            help='本次连接端口，不修改配置文件；指定后不再询问')
    connection.add_argument('--use-config-port', action='store_true',
                            help='直接使用配置文件中的端口，不在启动时询问')
    parser.add_argument('--limits', default=str(ROOT / 'supervisor/limits.yaml'))
    parser.add_argument('--duration', type=float, default=0, help='0 keeps running; positive value ends this experiment')
    parser.add_argument('--observe-interval', type=float, default=0.5)
    parser.add_argument('--smoke-policy', action='store_true', help='Explicit stage-2 debug path')
    parser.add_argument('--legacy-policy-debug', action='store_true', help='Old fixed-policy debug mode; excluded from formal evidence')
    parser.add_argument('--physical-caps', default=str(ROOT / 'individual/experiment.json'))
    parser.add_argument('--froi', action='store_true', help='Enable frozen FROI-1 organization consumer')
    parser.add_argument('--froi-caps', help='Frozen external GSC-0 capacity JSON')
    parser.add_argument('--verify-loop', action='store_true', help='External verification of V0-A/V0-B only; no recognition or ascent inferred')
    parser.add_argument('--policy-wait', type=float, default=1.0)
    parser.add_argument('--move-ms', type=int, default=200)
    args = parser.parse_args()
    if args.duration < 0 or not math.isfinite(args.duration):
        parser.error('duration must be finite and nonnegative')
    supervisor = None
    try:
        from individual.lifetime import resolve_runtime_database
        args.db = str(resolve_runtime_database(args.db, args.branch_db))
        from individual.formal_l0 import FormalLimits
        caps = FormalLimits.load(args.physical_caps)
        limits = load_limits(args.limits)
        from individual.formal_boundary import preflight, RESOURCE_CAP_KEYS, sensor_caps
        resource_caps = {key: limits[key] for key in RESOURCE_CAP_KEYS}
        resource_caps['body_observation_caps'] = sensor_caps(args.minecraft_config)
        preflight(args.db, None if args.legacy_policy_debug or args.smoke_policy else caps, resource_caps)
        from integration.froi import preflight as froi_preflight, load_caps as load_froi_caps
        if args.froi and (args.legacy_policy_debug or args.smoke_policy):
            raise ValueError('FROI cannot run through a debug policy')
        froi_preflight(args.db, args.froi, load_froi_caps(args.froi_caps))
        from .connection import choose_minecraft_port
        port = choose_minecraft_port(args.minecraft_config, args.minecraft_port, args.use_config_port)
        supervisor = Supervisor(args.db, limits)
        core_args = ['--minecraft-config', str(Path(args.minecraft_config).resolve()),
                     '--observe-interval', str(args.observe_interval), '--policy-wait', str(args.policy_wait),
                     '--move-ms', str(args.move_ms), '--session-label', args.session_label,
                     '--physical-caps', str(Path(args.physical_caps).resolve()),
                     '--environment-caps', json.dumps(resource_caps)]
        if port is not None:
            core_args.extend(['--minecraft-port', str(port)])
        if args.froi:
            core_args.append('--froi')
        if args.froi_caps:
            core_args.extend(['--froi-caps', str(Path(args.froi_caps).resolve())])
        if args.legacy_policy_debug:
            core_args.append('--legacy-policy-debug')
        if args.branch_db:
            # Child validates the same explicit branch designation.
            core_args.extend(['--branch-db', str(Path(args.branch_db).resolve())])
        if args.smoke_policy:
            core_args.append('--smoke-policy')
        supervisor.start(core_args)
        def read_console():
            for line in sys.stdin:
                command = line.strip().lower()
                if command == 'status':
                    print(json.dumps(supervisor.status(), ensure_ascii=False, indent=2), flush=True)
                elif command in ('pause', 'resume', 'terminate', 'exit', 'end_session', 'begin_session', 'new_session'):
                    supervisor.control('terminate' if command == 'exit' else command)
                elif command:
                    print('Commands: pause / resume / status / end_session / begin_session / new_session / terminate', flush=True)
        threading.Thread(target=read_console, daemon=True).start()
        print('Supervisor running. Commands: pause / resume / status / terminate; Ctrl+C terminates.', flush=True)
        return supervisor.run(args.duration, args.verify_loop)
    except Exception as error:
        print(f'Startup/monitor error: {error}', file=sys.stderr)
        return 1
    finally:
        if supervisor:
            supervisor.close()

