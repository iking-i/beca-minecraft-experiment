"""Explicit authorized offline replay of one preserved real observation."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from individual.internal_state import InternalState
from experimental.formall0_continuous.runner import FakeBridge
from experimental.formall0_operative.validation import initial
from .real.channel import RealEffectCore
from .effects.channel import EffectConfig
from .reference.references import KEY, fact_ref, resolve, observation_ref
from experimental.native_body_operands.engine import typed_inputs


def run(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    sample = Path('experimental/operative_body_real/evidence/attempt-3/REPORT.json')
    raw = json.loads(sample.read_text(encoding='utf-8'))['records'][0]['raw_observation']
    path = directory / 'individual.db'
    core = RealEffectCore(path, FakeBridge(), initialize_lifetime=True,
        config=EffectConfig(str(path), origin_state=initial()[0]))
    report = {'source': str(sample), 'source_sha256': hashlib.sha256(sample.read_bytes()).hexdigest(),
              'offline_replay': True, 'minecraft_run': False, 'perform_requests': 0,
              'database': str(path.resolve()), 'raw_input': deepcopy(raw),
              'before': core.state.to_dict()}
    try:
        core.accept_observation(raw)
        report['after'] = core.state.to_dict()
        internal = InternalState.from_dict(core.state.internal_state)
        pool = internal.l0_state[KEY]
        source = pool['current_source']
        checked = []
        for channel, value in source['numeric_channels'].items():
            ref = fact_ref(internal, source['frame_id'], channel)
            assert resolve(internal, ref)['value'] == value
            checked.append(ref)
        atoms = {r: n for r, n in typed_inputs(source).items()
                 if n['type'] in ('ObservedValue', 'ObservedReference')}
        for key, value in atoms.items():
            assert resolve(internal, observation_ref(internal, key)) == value
        report.update(classification='PASS', checked_channel_refs=checked,
                      numeric_channels=len(source['numeric_channels']),
                      observed_values=sum(n['type'] == 'ObservedValue' for n in atoms.values()),
                      object_references=len(source['references']), catalog_count=len(pool['catalog']['declarations']),
                      internal_units=len(internal.units), content_nodes=len(pool['nodes']), unit_cap=64,
                      source_unchanged=raw == report['raw_input'],
                      authoritative_state=core._store.latest_state().to_dict() == core.state.to_dict())
    finally:
        core.shutdown('offline_saved_sample_close')
        report['shutdown'] = core.state.to_dict()
        (directory / 'REPORT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    result = run(args.directory)
    print(json.dumps({k: result[k] for k in ('classification', 'numeric_channels', 'observed_values',
        'object_references', 'catalog_count', 'internal_units', 'content_nodes', 'offline_replay', 'minecraft_run')}))
