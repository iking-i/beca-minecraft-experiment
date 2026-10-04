"""External storage administration: one directory per individual, never per session."""

import json
from pathlib import Path
from uuid import uuid4

from .identity import ExperimentLease
from .state import utc_now

ROOT = Path(__file__).resolve().parents[1]
INDIVIDUALS = ROOT / 'storage/individuals'


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{uuid4()}.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def _finish_directory(staging, storage_root, identity):
    # Only relocate the just-created, closed database. Existing lifetimes are never moved here.
    destination = storage_root / identity
    if staging.resolve().parent != storage_root or destination.resolve().parent != storage_root:
        raise ValueError('Individual directory must remain inside the storage root')
    if destination.exists():
        raise FileExistsError(destination)
    staging.rename(destination)
    return destination


def create_lifetime(storage_root=INDIVIDUALS, config=None, label=''):
    """Explicitly register a NEW A, retain the previous directory, and select the new A."""
    from .lifetime import CONFIG, initialize_lifetime, resolve_runtime_database
    config = Path(config) if config is not None else CONFIG
    storage_root = Path(storage_root).resolve()
    previous_lease = None
    previous = None
    if config.exists():
        previous = resolve_runtime_database(config=config)
        # A running Core holds this lease: replacing its pointer is forbidden.
        previous_lease = ExperimentLease(previous).acquire()
    try:
        staging = storage_root / f'.initializing-{uuid4()}'
        staging.mkdir(parents=True, exist_ok=False)
        result = initialize_lifetime(staging / 'individual.db')
        directory = _finish_directory(staging, storage_root, result['individual_id'])
        database = directory / 'individual.db'
        result.update(database=str(database), directory=str(directory), label=label,
                      created_at=utc_now(), previous_database=str(previous) if previous else None,
                      previous_history_preserved=True, role='mainline')
        write_json(directory / 'lifetime-initialization-report.json', result)
        write_json(directory / 'lifetime.json', {
            'individual_id': result['individual_id'], 'database': 'individual.db',
            'role': 'mainline', 'label': label, 'created_at': result['created_at']})
        try:
            location = database.relative_to(ROOT).as_posix()
        except ValueError:
            location = str(database)
        write_json(config, {'database': location, 'individual_id': result['individual_id'], 'role': 'mainline'})
        update_index(storage_root)
        return result
    finally:
        if previous_lease:
            previous_lease.release()


def create_branch(source, snapshot_id, storage_root=INDIVIDUALS):
    """A snapshot branch gets its own directory; it never replaces the mainline pointer."""
    from .lifetime import fork_snapshot
    storage_root = Path(storage_root).resolve()
    staging = storage_root / f'.initializing-{uuid4()}'
    staging.mkdir(parents=True, exist_ok=False)
    result = fork_snapshot(source, snapshot_id, staging / 'individual.db')
    directory = _finish_directory(staging, storage_root, result['branch_individual_id'])
    result['branch_database'] = str(directory / 'individual.db')
    write_json(directory / 'snapshot-branch-report.json', result)
    write_json(directory / 'lifetime.json', {
        'individual_id': result['branch_individual_id'], 'database': 'individual.db',
        'role': 'snapshot_branch', 'origin': result})
    update_index(storage_root)
    return result


def save_report(database, kind, report, output=None):
    """Default reports stay with their lifetime; repeated audits retain earlier exports."""
    if output is None:
        stamp = utc_now().replace(':', '-').replace('+', '_')
        output = Path(database).resolve().parent / 'reports' / f'{kind}-{stamp}-{uuid4().hex[:8]}.json'
    write_json(output, report)
    return Path(output).resolve()


def update_index(storage_root=INDIVIDUALS):
    """Human-readable catalog only; runtime identity remains pinned by lifetime.json."""
    storage_root = Path(storage_root).resolve()
    entries = []
    for directory in sorted(storage_root.iterdir()):
        manifest = directory / 'lifetime.json'
        if not directory.is_dir() or not manifest.is_file() or directory.name.startswith('.'):
            continue
        record = json.loads(manifest.read_text(encoding='utf-8'))
        entries.append({**record, 'directory': str(directory)})
    write_json(storage_root.parent / 'index.json', {'updated_at': utc_now(), 'individuals': entries,
               'runtime_selection': 'individual/lifetime.json', 'grouping_key': 'individual_id'})
