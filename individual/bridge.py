"""Only the explicit body API crosses the Python/Node process boundary."""

import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def parse_minecraft_port(value):
    text = str(value).strip()
    if not text.isascii() or not text.isdecimal() or not 1 <= int(text) <= 65535:
        raise ValueError('端口必须是 1 到 65535 的整数')
    return int(text)


class BridgeError(RuntimeError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.details = details


class MinecraftBridge:
    METHODS = frozenset({'start', 'status', 'observe', 'perform', 'move', 'interact', 'chat', 'close'})

    def __init__(self, config, adapter=None, timeout=20.0, log=None, port=None):
        self.config = str(Path(config).resolve())
        self.adapter = str(Path(adapter or ROOT / 'bridge/server.js').resolve())
        self.timeout = timeout
        self.port = parse_minecraft_port(port) if port is not None else None
        self.log = log or (lambda message: None)
        self.process = None
        self._events = queue.Queue()
        self._pending = {}
        self._lock = threading.Lock()
        self._request_id = 0
        self._threads = []
        self._closing = False

    @property
    def pid(self):
        return self.process.pid if self.process else None

    @property
    def alive(self):
        return self.process is not None and self.process.poll() is None

    def launch(self):
        if self.process is not None:
            raise RuntimeError('Bridge process is already launched')
        argv = ['node', self.adapter, self.config]
        if self.port is not None:
            argv.append(str(self.port))
        self.process = subprocess.Popen(argv, cwd=ROOT,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1)
        for target in (self._read_output, self._read_errors):
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            self._threads.append(thread)

    def _read_output(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                if message.get('kind') == 'response':
                    with self._lock:
                        waiting = self._pending.get(message.get('id'))
                    if waiting:
                        waiting.put(message)
                elif message.get('kind') == 'lifecycle':
                    self._events.put(message)
                else:
                    raise ValueError('Unknown bridge message')
        except (ValueError, OSError) as error:
            self._events.put({'kind': 'transport_error', 'error': str(error)})
        finally:
            with self._lock:
                waiting = list(self._pending.values())
            for pending in waiting:
                pending.put({'ok': False, 'error': {'code': 'BRIDGE_EXITED', 'message': 'Bridge output closed'}})
            self._events.put({'kind': 'exited'})

    def _read_errors(self):
        for line in self.process.stderr:
            self.log(line.rstrip())

    def call(self, method, args=None, timeout=None):
        if method not in self.METHODS:
            raise BridgeError('UNKNOWN_METHOD', 'Only body methods are available')
        if not self.alive or self._closing:
            raise BridgeError('BRIDGE_EXITED', 'Bridge is not running')
        waiting = queue.Queue()
        with self._lock:
            self._request_id += 1
            request_id = self._request_id
            self._pending[request_id] = waiting
            try:
                self.process.stdin.write(json.dumps({'id': request_id, 'method': method, 'args': args or {}}, allow_nan=False) + '\n')
                self.process.stdin.flush()
            except (OSError, ValueError) as error:
                self._pending.pop(request_id, None)
                raise BridgeError('BRIDGE_EXITED', str(error)) from error
        try:
            try:
                response = waiting.get(timeout=self.timeout if timeout is None else timeout)
            except queue.Empty as error:
                raise BridgeError('BRIDGE_TIMEOUT', f'{method} response timed out; action will not be replayed') from error
            if not response.get('ok'):
                error = response.get('error', {})
                raise BridgeError(error.get('code', 'BRIDGE_ERROR'), error.get('message', 'Bridge call failed'), error.get('details'))
            return response.get('result')
        finally:
            with self._lock:
                self._pending.pop(request_id, None)

    def drain_events(self):
        result = []
        while True:
            try:
                result.append(self._events.get_nowait())
            except queue.Empty:
                return result

    def close(self):
        if self.process is None or self._closing:
            return
        try:
            if self.alive:
                try:
                    self.call('close', timeout=2)
                except BridgeError:
                    pass
        finally:
            self._closing = True
            if not self.process.stdin.closed:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
            for thread in self._threads:
                thread.join(timeout=1)
            self.process.stdout.close()
            self.process.stderr.close()

