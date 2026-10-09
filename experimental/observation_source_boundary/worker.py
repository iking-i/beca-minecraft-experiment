"""Independent-process OFF continuation and interrupted-publication controls."""
import json
import os
import sys
from pathlib import Path
from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from experimental.body_interface_references.runner import sample
from .effects.channel import EffectConfig
from .lifecycle import BoundaryCore


def main(phase, path):
    path = Path(path)
    c = BoundaryCore(path, FakeBridge(), config=EffectConfig(str(path),
        origin_state=initial()[0] if phase=='create' else None),
        initialize_lifetime=phase=='create', full_history_enabled=False)
    if phase == 'crash':
        original = c._source_store.flush
        def crash(descriptor):
            original(descriptor)
            os._exit(73)
        c._source_store.flush = crash
        c.accept_observation(sample(c.state.environment_sequence + 1,0))
        raise AssertionError('Crash control did not reach transaction')
    before = c.state.to_dict()
    c.accept_observation(sample(c.state.environment_sequence + 1,0))
    result = {'pid':os.getpid(), 'individual_id':c.state.individual_id,
              'before_version':before['state_version'], 'after_version':c.state.state_version,
              'sources':c._source_store.audit()['sources'],
              'authoritative':c._store.latest_state().to_dict()==c.state.to_dict()}
    c.shutdown()
    print(json.dumps(result))


if __name__ == '__main__':
    main(*sys.argv[1:])
