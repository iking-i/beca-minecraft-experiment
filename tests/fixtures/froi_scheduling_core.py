"""TEST_ONLY actual Core.main / Supervisor integration with an inert fake body."""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from individual.core import ACore, main
from integration.froi_worker import Worker
from tests.test_core import FakeBridge
from tests.test_structure import observation


class Body(FakeBridge):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def launch(self):
        super().launch()
        self.child = subprocess.Popen(['node', '-e', 'setInterval(()=>{},1000)'],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.pid = self.child.pid

    def call(self, method, args=None):
        return observation() if method == 'observe' else super().call(method, args)

    def close(self):
        super().close()
        if hasattr(self, 'child'):
            self.child.terminate()
            self.child.wait(timeout=2)


original = ACore.__init__

def initialize(self, *args, **kwargs):
    kwargs['worker_factory'] = lambda job: Worker(job, [sys.executable, '-m',
        'tests.fixtures.froi_worker_hook', '20'])
    original(self, *args, **kwargs)


if __name__ == '__main__':
    with patch('individual.core.MinecraftBridge', Body), patch.object(ACore, '__init__', initialize), \
         patch('individual.lifetime.resolve_runtime_database', lambda db, branch: Path(db).resolve()):
        raise SystemExit(main())
