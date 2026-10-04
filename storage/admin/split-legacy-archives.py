"""One-time archive classification. Keep the source until every new member verifies."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

from individual.storage import write_json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'storage/archive/old-runs-20261004-114659.zip'
ADMIN = ROOT / 'storage/admin'


def digest_stream(stream):
    digest = hashlib.sha256()
    while chunk := stream.read(4 * 1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def main():
    with SOURCE.open('rb') as stream:
        source_hash = digest_stream(stream)
    cleanup = json.loads((ADMIN / 'cleanup-report-2026-10-04.json').read_text(encoding='utf-8'))
    if source_hash.lower() != cleanup['archive_sha256'].lower():
        raise ValueError('Original archive digest differs from the verified cleanup record')
    results = []
    with zipfile.ZipFile(SOURCE) as source:
        records = json.loads(source.read('cleanup-manifest.json'))['files']
        for label in ('run-001', 'run-002', 'run-003'):
            with source.open(f'storage/{label}.db') as stream:
                prefix = stream.read(262144)
            identities = set(re.findall(rb'A-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', prefix))
            if len(identities) != 1:
                raise ValueError(f'Archive identity ambiguous: {label}')
            identity = identities.pop().decode('ascii')
            directory = ROOT / 'storage/individuals' / identity
            if directory.resolve().parent != (ROOT / 'storage/individuals').resolve():
                raise ValueError('Invalid destination directory')
            archive = directory / 'archive' / f'{label}.zip'
            archive.parent.mkdir(parents=True, exist_ok=True)
            selected = [r for r in records if Path(r['entry']).name.startswith(label + '.')]
            if len(selected) != 5:
                raise ValueError('Expected database, WAL, SHM, lease and supervisor record together')
            manifest = {'individual_id': identity, 'label': label, 'source_archive': str(SOURCE),
                        'source_archive_sha256': source_hash,
                        'identity_lookup': 'unique UUID in original database prefix', 'files': selected}
            print(f'Classifying {label}: {identity}', flush=True)
            with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as target:
                for record in selected:
                    digest = hashlib.sha256()
                    total = 0
                    with source.open(record['entry']) as old, target.open(Path(record['entry']).name, 'w', force_zip64=True) as new:
                        while chunk := old.read(4 * 1024 * 1024):
                            new.write(chunk)
                            digest.update(chunk)
                            total += len(chunk)
                    if digest.hexdigest().lower() != record['sha256'].lower() or total != record['bytes']:
                        raise ValueError('Original archived member failed verification')
                target.writestr('archive-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            with zipfile.ZipFile(archive) as verified:
                for record in selected:
                    with verified.open(Path(record['entry']).name) as member:
                        if digest_stream(member).lower() != record['sha256'].lower():
                            raise ValueError('New archived member failed verification')
            manifest.update(archive=str(archive), archive_verified=True)
            write_json(directory / 'lifetime.json', {'individual_id': identity, 'label': label,
                       'role': 'archived_legacy_independent_experiment', 'archive': f'archive/{label}.zip'})
            write_json(directory / 'reports/archive-classification.json', manifest)
            results.append({'individual_id': identity, 'label': label, 'directory': str(directory),
                            'archive': str(archive), 'members_verified': 5})
            print(f'Verified all five members: {label}', flush=True)
    write_json(ADMIN / 'archive-classification-report.json', {
        'source_archive': str(SOURCE), 'source_archive_sha256': source_hash,
        'all_members_verified': True, 'source_retained_until_explicit_cleanup': True, 'individuals': results})


if __name__ == '__main__':
    main()
