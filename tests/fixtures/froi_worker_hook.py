"""TEST_ONLY task carrier delay/crash controls, never enabled by runtime CLI."""
import os
import pickle
import sys
import time
from integration.froi_worker import execute

job = pickle.load(sys.stdin.buffer)
mode = sys.argv[1]
if mode == 'crash':
    os._exit(23)
if mode == 'exception':
    raise RuntimeError('TEST_ONLY worker transport failure')
if mode == 'malformed':
    sys.stdout.buffer.write(b'not a serialized result')
else:
    time.sleep(float(mode))
    pickle.dump(execute(job), sys.stdout.buffer)
sys.stdout.buffer.flush()
