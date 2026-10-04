"""TEST_ONLY numeric fixture; never presented as a Minecraft live run."""

import argparse
import json
from pathlib import Path

from individual.core import ACore
from individual.experiment_audit import audit
from individual.state import utc_now


class NumericFixtureBridge:
    def __init__(self):
        self.alive, self.pid, self.x, self.y = False, None, 0.0, 64.0
        self.events = []

    def launch(self):
        self.alive = True

    def call(self, method, args=None):
        if method == 'start':
            self.events.append({'kind': 'lifecycle', 'status': {'state': 'ready', 'connected': True, 'attempt': 1}})
            return {'fixture': True}
        if method == 'observe':
            # External dynamics only: a bounded coordinate, not a rule/goal given to A.
            result = {'timestamp': utc_now(), 'position': {'x': self.x, 'y': self.y, 'z': 0},
                      'health': 20, 'hunger': 20, 'inventory': [], 'encoding': {'protocol_version': 'numeric-fixture'}}
            self.y = 64.0
            return result
        if method == 'move':
            if args['direction'] == 'forward':
                self.x = min(0.5, self.x + 0.25)
            elif args['direction'] == 'jump':
                self.y = 64.4
            return {'fixture': True}
        raise ValueError(method)

    def drain_events(self):
        values, self.events = self.events, []
        return values

    def close(self):
        self.alive = False


def run_fixture(database, cycles=60):
    core = ACore(database, NumericFixtureBridge(), session_context={'environment_type': 'numeric_fixture'},
                 session_label='legacy numeric fixture', initialize_lifetime=True,
                 experiment_profile='legacy_policy_debug')
    try:
        core.start()
        core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 1})
        core.accept_observation(core._bridge.call('observe'))
        for _ in range(cycles):
            core.execute_discrete_action()
            core.accept_observation(core._bridge.call('observe'))
    finally:
        core.shutdown('numeric_fixture_completed')
    return audit(database, include_sample=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--cycles', type=int, default=60)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = run_fixture(args.db, args.cycles)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in ('actual_event_sample', 'feedback_generations')}, indent=2))


if __name__ == '__main__':
    main()
