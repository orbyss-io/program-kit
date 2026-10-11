"""Capture additive lifecycle facts from exact qualification archives, with no installs."""
from pathlib import Path
import hashlib
import base64
import json
import re
import zipfile
import xml.etree.ElementTree as ET


def capture(registry, cache, lock):
    versions = {row['resolved'] for target in lock['dependencies'].values()
                for name, row in target.items() if name == 'CShells.Abstractions'}
    if len(versions) != 1:
        raise ValueError('Lifecycle capture needs one exact CShells.Abstractions qualification lock')
    version = next(iter(versions))
    directory = registry / 'lifecycle-knowledge' / version
    rows = []
    for identity in ('CShells.Abstractions', 'CShells'):
        archive_path = cache / identity.lower() / version / (identity.lower()+'.'+version+'.nupkg')
        if identity == 'CShells' and not archive_path.is_file():
            existing = directory / 'index.json'
            if existing.is_file():
                rows += [row for row in json.loads(existing.read_text())['packages'] if row['id'] == identity]
            continue  # Host-owned runtime facts are optional, never qualification claims.
        archive_bytes = archive_path.read_bytes()
        hashes = {row['contentHash'] for target in lock['dependencies'].values()
                  for name, row in target.items() if name == identity}
        archive_hash = base64.b64encode(hashlib.sha512(archive_bytes).digest()).decode()
        if hashes and hashes != {archive_hash}:
            raise ValueError('Lifecycle archive bytes differ from qualification lock: ' + identity)
        if identity == 'CShells.Abstractions' and not hashes:
            raise ValueError('Missing exact abstraction lock hash')
        with zipfile.ZipFile(archive_path) as archive:
            spec = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.nuspec'))))
            fields = {n.tag.rsplit('}', 1)[-1]: n.text for n in spec.iter()}
            repo = next(n for n in spec.iter() if n.tag.rsplit('}', 1)[-1] == 'repository')
            if fields['id'] != identity or fields['version'] != version or not re.fullmatch('[0-9a-f]{40}', repo.get('commit', '')):
                raise ValueError('Lifecycle publisher package differs from selected lock')
            facts = {}
            for item in archive.infolist():
                if item.filename.lower() == 'readme.md' or item.filename.startswith('lib/net10.0/') and item.filename.endswith('.xml'):
                    if item.file_size > 2*1024*1024: raise ValueError('Publisher lifecycle fact exceeds two MiB')
                    facts[item.filename] = archive.read(item).decode('utf-8')
            if not facts: raise ValueError('Lifecycle publisher facts are missing')
            value = {'id': identity, 'version': version, 'license': fields.get('license'),
                     'repository': repo.attrib, 'archiveSha256': hashlib.sha256(archive_bytes).hexdigest(),
                     'archiveSha512': archive_hash,
                     'authority': 'qualification-lock' if hashes else 'same-version-publisher-runtime-facts; host runtime acceptance remains separate',
                     'facts': facts}
        path = directory / (identity + '.json')
        data = (json.dumps(value, indent=2)+'\n').encode()
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Never overwrite previously captured lifecycle knowledge')
        directory.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        rows.append({'id': identity, 'version': version, 'path': path.relative_to(registry).as_posix(),
                     'sha256': hashlib.sha256(data).hexdigest()})
    manifest = directory / 'index.json'
    data = (json.dumps({'schemaVersion': 1, 'version': version, 'packages': rows}, indent=2)+'\n').encode()
    if manifest.exists() and manifest.read_bytes() != data: raise ValueError('Lifecycle manifest is immutable')
    manifest.write_bytes(data)
    index_path = registry / 'lifecycle-knowledge/index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {'schemaVersion': 1, 'versions': {}}
    index['versions'][version] = {'path': manifest.relative_to(registry).as_posix(), 'sha256': hashlib.sha256(data).hexdigest()}
    index_path.write_text(json.dumps(index, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--lock', type=Path, required=True)
    args = parser.parse_args()
    print(capture(args.registry, args.cache, json.loads(args.lock.read_text())))
