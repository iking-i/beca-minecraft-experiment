"""Short TEST_ONLY numeric validation; no Minecraft connection, no mainline switch."""

from pathlib import Path
from uuid import uuid4

from individual.core import ACore
from individual.experiment_audit import audit
from individual.formal_l0 import FormalLimits
from individual.lifetime import initialize_lifetime
from individual.storage import INDIVIDUALS, _finish_directory, save_report, update_index, write_json
from debug.run_fixture import NumericFixtureBridge


def main():
    staging = INDIVIDUALS / f'.validating-{uuid4()}'
    staging.mkdir(parents=True, exist_ok=False)
    registration = initialize_lifetime(staging / 'individual.db')
    directory = _finish_directory(staging, INDIVIDUALS.resolve(), registration['individual_id'])
    database = directory / 'individual.db'
    bridge = NumericFixtureBridge()
    core = ACore(database, bridge, session_context={'environment_type': 'numeric_fixture', 'test_only': True},
                 session_label='formal L0 short validation', physical_caps=FormalLimits(units=1, relations=2, history=2, evidence_window=2))
    try:
        # Real Core/interpreter/SQLite execution with simulated environmental input.
        # This is neither a real Minecraft result nor a newly launched subject claim.
        core.start()
        core.accept_bridge_status({'state': 'ready', 'connected': True, 'attempt': 1})
        for index in range(12):
            bridge.x = [0, 1, 1, 0][index % 4]
            core.accept_observation(bridge.call('observe'))
        core.execute_discrete_action()  # Exercise actual external sampler/provenance, not a TEST_ONLY action.
        core.accept_observation(bridge.call('observe'))
    finally:
        core.shutdown('test_only_numeric_validation')
    result = audit(database, include_sample=True)
    result['validation_context'] = {'test_only': True, 'real_minecraft': False,
                                    'mainline_identity_changed': False, 'observations': 13}
    report = save_report(database, 'formal-l0-validation', result)
    write_json(directory / 'lifetime.json', {'individual_id': registration['individual_id'],
        'database': database.name, 'role': 'test_fixture', 'label': 'formal-l0-numeric-validation',
        'real_minecraft': False, 'mainline_selected': False})
    update_index()
    print(f'Report: {report}')
    print(f'Classifications: {result["classifications"]}')
    print(f'Full stage goal observed: {result["formal_stage_goal_observed"]}')
    print(f'V0-A/V0-B baseline observed: {result["baseline_goal_observed"]}')
    print(f'Database: {database}')


if __name__ == '__main__':
    main()
