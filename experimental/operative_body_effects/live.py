"""Bounded real carrier check. No training, receipt injection or action arguments."""
import argparse
import json
from pathlib import Path
import time
from unittest.mock import patch

from individual.bridge import MinecraftBridge
from experimental.formall0_operative.validation import initial
from .channel import EffectCore, EffectConfig
from .engine import KEY


def run(database, port, config, report_path):
    if Path(database).exists() or Path(report_path).exists():
        raise ValueError('Live check requires new database and new evidence path')
    bridge = MinecraftBridge(config, port=port)
    core = EffectCore(database, bridge, initialize_lifetime=True,
                      config=EffectConfig(str(database), origin_state=initial()[0]))
    report = {'classification': 'NOT_TESTABLE', 'minecraft_run': False,
              'body_execution': False, 'database': str(Path(database).resolve()),
              'individual_id': core.state.individual_id, 'records': [],
              'window': {'observations': 8, 'seconds': 30}, 'synthetic_training': False,
              'imported_history': False, 'action_content_arguments': False}
    try:
        with patch('individual.core.select_uniform_action', side_effect=AssertionError('sampler forbidden')), \
             patch('individual.core.bind_parameters', side_effect=AssertionError('binder forbidden')):
            core.start()
            deadline = time.monotonic() + 30
            report['minecraft_run'] = True
            while len(report['records']) < 8 and time.monotonic() < deadline:
                raw = bridge.call('observe', timeout=min(10, max(.1, deadline-time.monotonic())))
                if raw.get('typedExecutionReceipts'):
                    raise ValueError('No injected training receipt in this live window')
                core.accept_observation(raw)
                state = core.state.to_dict()
                report['records'].append({'raw_observation': raw, 'state': state})
                report['body_execution'] |= bool(state['internal_state']['l0_state'][KEY]['attempts'])
                time.sleep(.25)
            report['classification'] = ('PARTIAL' if report['body_execution'] else 'NOT_READY')
            report['reason'] = ('Inspect real receipt and subsequent input; no automatic loop claim'
                                if report['body_execution'] else 'No internally formed current native activation')
    except Exception as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        report['final_state'] = core.state.to_dict()
        try:
            core.shutdown('TEST_ONLY_bounded_effect_carrier_close')
        except Exception as error:
            report['shutdown_error'] = str(error)
        with Path(report_path).open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--config', default='minecraft/config.json')
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    result = run(Path(args.database), args.port, args.config, Path(args.report))
    print(json.dumps({'classification': result['classification'],
                      'observations': len(result['records']),
                      'body_execution': result['body_execution'], 'error': result.get('error')}))
