"""Non-A subprocess fixture to exercise external process supervision."""

import json
import queue
import subprocess
import sys
import threading
import time

mode = sys.argv[1]
child = subprocess.Popen(['node', '-e', 'process.stdin.resume();process.stdin.on("end",()=>process.exit(0));'],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def emit(kind, **payload):
    print(json.dumps({'kind': kind, **payload}), flush=True)

emit('CORE_STARTED', individual_id='fixture-only', state_version=0)
emit('BRIDGE_STARTED', pid=child.pid)
emit('CONTROL', command='set_limits', limits={'max_core_ram_mb': 999999})
controls = queue.Queue()

def read():
    for line in sys.stdin:
        controls.put(json.loads(line)['command'])

threading.Thread(target=read, daemon=True).start()
started = time.monotonic()
status = 'running'
version = 0
try:
    while True:
        if mode == 'bridge_exit' and time.monotonic() - started > 0.25 and child.poll() is None:
            child.terminate()
        if not controls.empty():
            command = controls.get_nowait()
            if mode != 'ignore':
                if command == 'terminate':
                    break
                if command in ('pause', 'resume'):
                    status = 'paused' if command == 'pause' else 'running'
                    version += 1
        emit('HEARTBEAT', individual_id='fixture-only', state_version=version,
             environment_sequence=0, status=status, bridge_pid=child.pid)
        time.sleep(0.03)
finally:
    child.stdin.close()
    if child.poll() is None:
        child.wait(timeout=2)
    emit('CORE_STOPPED', individual_id='fixture-only', state_version=version)
