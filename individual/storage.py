"""External storage administration: one directory per individual, never per session."""

import json
from contextlib import closing
from pathlib import Path
import sqlite3
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


def create_lifetime(storage_root=INDIVIDUALS, config=None, label='', replace_missing_selection=False):
    """Explicitly register a NEW A, retain the previous directory, and select the new A."""
    from .lifetime import CONFIG, initialize_lifetime, resolve_runtime_database
    config = Path(config) if config is not None else CONFIG
    storage_root = Path(storage_root).resolve()
    previous_lease = None
    previous = None
    previous_pin = None
    previous_missing = False
    if config.exists():
        previous_pin = config.read_bytes()
        selection = json.loads(previous_pin.decode('utf-8'))
        previous = (ROOT / selection['database']).resolve()
        previous_missing = not previous.exists()
        if previous_missing:
            if not replace_missing_selection:
                raise ValueError('Selected lifetime database is missing. To explicitly register a NEW A, use initialize --replace-missing-selection; ordinary startup never replaces A.')
            # A stale pointer is not a resumable individual. Preserve it for audit.
            # An existing lease still protects a carrier using that original path.
            if Path(str(previous) + '.lock').is_file():
                previous_lease = ExperimentLease(previous).acquire()
        else:
            previous = resolve_runtime_database(config=config)
            # A running Core holds this lease: replacing its pointer is forbidden.
            previous_lease = ExperimentLease(previous).acquire()
    try:
        staging = storage_root / f'.initializing-{uuid4()}'
        staging.mkdir(parents=True, exist_ok=False)
        result = initialize_lifetime(staging / 'individual.db')
        directory = _finish_directory(staging, storage_root, result['individual_id'])
        database = directory / 'individual.db'
        if previous_pin is not None:
            (directory / 'previous-selection.json').write_bytes(previous_pin)
        result.update(database=str(database), directory=str(directory), label=label,
                      created_at=utc_now(), previous_database=str(previous) if previous else None,
                      previous_history_preserved=not previous_missing, existing_history_untouched=True,
                      previous_database_missing=previous_missing,
                      previous_selection_backup='previous-selection.json' if previous_pin is not None else None,
                      registration_kind='explicit_new_individual', original_individual_resumed=False,
                      role='mainline')
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
        try:
            record = json.loads(manifest.read_text(encoding='utf-8'))
            if not isinstance(record, dict):
                continue
        except (ValueError, OSError):
            continue  # A damaged catalog entry must not block managing other A's.
        entries.append({**record, 'directory': str(directory)})
    write_json(storage_root.parent / 'index.json', {'updated_at': utc_now(), 'individuals': entries,
               'runtime_selection': 'individual/lifetime.json', 'grouping_key': 'individual_id'})


def lifetime_entry(directory, selection=None):
    """Read-only validated mainline catalog entry; never infer an identity."""
    from .inspect import verify
    directory = Path(directory).resolve()
    manifest = json.loads((directory / 'lifetime.json').read_text(encoding='utf-8'))
    if manifest['role'] != 'mainline' or manifest['database'] != 'individual.db':
        raise ValueError('Only mainline individual.db lifetimes can be selected')
    database = directory / 'individual.db'
    if not database.is_file() or directory.name != manifest['individual_id']:
        raise ValueError('Missing database or directory/manifest identity mismatch')
    wal = Path(str(database) + '-wal')
    flags = '?mode=ro' if wal.is_file() and wal.stat().st_size else '?mode=ro&immutable=1'
    with closing(sqlite3.connect(database.as_uri() + flags, uri=True)) as db:
        history = verify(database, connection=db)
    lifetime = history['A_lifetime_history']
    if lifetime['individual_id'] != manifest['individual_id'] or lifetime['role'] != 'mainline':
        raise ValueError('Database identity/role differs from lifetime manifest')
    selected = bool(selection and selection.get('individual_id') == manifest['individual_id']
                    and (ROOT / selection.get('database', '')).resolve() == database)
    return {**manifest, 'directory': str(directory), 'database': str(database),
            'created_at': manifest.get('created_at', lifetime['started_at']),
            'state_version': history['last_state_version'],
            'session_count': len(history['Experiment_session_history']), 'selected': selected}


def list_lifetimes(storage_root=INDIVIDUALS, config=None):
    """Scan manifests and verify histories. Index labels are catalog hints only."""
    from .lifetime import CONFIG
    config = Path(config) if config is not None else CONFIG
    root = Path(storage_root).resolve()
    try:
        selection = json.loads(config.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        selection = None
    try:
        cached = json.loads((root.parent / 'index.json').read_text(encoding='utf-8'))['individuals']
        labels = {x['individual_id']: x.get('label', '') for x in cached if isinstance(x, dict)}
    except (OSError, ValueError, KeyError, TypeError):
        labels = {}
    entries, rejected = [], []
    for directory in sorted(root.iterdir()) if root.is_dir() else ():
        if not directory.is_dir() or directory.name.startswith('.'):
            continue
        try:
            entry = lifetime_entry(directory, selection)
            entry['label'] = entry.get('label') or labels.get(entry['individual_id'], '')
            entries.append(entry)
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            rejected.append({'directory': str(directory), 'reason': str(error)})
    return entries, rejected


def select_existing_lifetime(directory, storage_root=INDIVIDUALS, config=None):
    """External pointer administration only. Both current and target must be idle."""
    from .lifetime import CONFIG
    config = Path(config) if config is not None else CONFIG
    root, directory = Path(storage_root).resolve(), Path(directory).resolve()
    if directory.parent != root:
        raise ValueError('Selected lifetime must be inside storage/individuals')
    entry = lifetime_entry(directory)
    leases = []
    try:
        leases.append(ExperimentLease(config).acquire())
        previous_bytes = config.read_bytes() if config.exists() else None
        previous = json.loads(previous_bytes.decode('utf-8')) if previous_bytes else None
        databases = {Path(entry['database'])}
        if previous:
            path = (ROOT / previous['database']).resolve()
            if path.exists() or Path(str(path) + '.lock').exists():
                databases.add(path)
        for path in sorted(databases, key=str):
            leases.append(ExperimentLease(path).acquire())
        entry = lifetime_entry(directory)
        if (config.read_bytes() if config.exists() else None) != previous_bytes:
            raise ValueError('Runtime selection changed concurrently; refusing switch')
        database = Path(entry['database'])
        try:
            location = database.relative_to(ROOT).as_posix()
        except ValueError:
            location = str(database)
        update_index(root)
        write_json(config, {'database': location, 'individual_id': entry['individual_id'], 'role': 'mainline'})
        return entry
    finally:
        for lease in reversed(leases):
            lease.release()
