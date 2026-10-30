"""Retired lock ownership derives from original reset owners, never project absence."""
from pathlib import Path
import xml.etree.ElementTree as ET

from retained_inputs import canonical, contained, file_hash, require
from retained_archives import inactivity


def verify(root, rows, records):
    require(isinstance(rows, list) and len(rows) <= 256, 'retiredLocks must be a bounded array')
    result, inputs, owners, seen = {}, {}, [], set()
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'path', 'record', 'owners'}
                and row['record'] in records and isinstance(row['owners'], list) and 0 < len(row['owners']) <= 256,
                'retired lock needs an original record and complete original owners')
        relative = canonical(row['path'])
        require(relative.casefold() not in seen, 'duplicate/aliased retired lock')
        seen.add(relative.casefold())
        authority, original = records[row['record']]
        require(relative in original['preserved'] and isinstance(original.get('abandoned'), dict),
                'retired lock is not preserved by its original owner reset')
        digest = original['preserved'][relative]
        require(file_hash(contained(root, relative)) == digest, 'retired lock bytes changed: ' + relative)
        require(len(set(row['owners'])) == len(row['owners']), 'duplicate retired lock owner')
        original_owners = {name for name in original['abandoned']
                           if Path(name).suffix.lower() in {'.csproj', '.fsproj', '.vbproj'}
                           and Path(name).parent == Path(relative).parent}
        if Path(relative).name == 'packages.lock.json':
            require(set(row['owners']) == original_owners,
                    'retired conventional lock needs every original same-directory project owner')
        for owner in row['owners']:
            owner = canonical(owner)
            require(Path(owner).suffix.lower() in {'.csproj', '.fsproj', '.vbproj'} and owner in original['abandoned'],
                    'retired lock owner lacks original supported project retirement')
            require(not contained(root, owner).exists(), 'retired lock owner reactivated: ' + owner)
            if Path(relative).name != 'packages.lock.json' or Path(owner).parent != Path(relative).parent:
                # A custom path must be demonstrable in original project bytes.
                # Imported/dynamic historical layouts need an original evaluated
                # ownership receipt; absence never grants retirement authority.
                require(original.get('archive'), 'custom retired lock needs original archived owner bytes')
                archived = contained(root, canonical(original['archive']) + '/' + owner)
                require(file_hash(archived) == original['abandoned'][owner], 'original custom lock owner changed')
                project = ET.fromstring(archived.read_text(encoding='utf-8-sig'))
                values = [node.text or '' for node in project.iter() if node.tag.rsplit('}', 1)[-1] == 'NuGetLockFilePath']
                require(len(values) == 1 and not any(char in values[0] for char in '$@%*?'),
                        'custom retired lock needs original literal/evaluated native owner evidence')
                lock = (root/owner).parent/values[0].replace('\\', '/')
                require(lock.resolve() == contained(root, relative), 'custom retired lock does not match original native owner')
            owners.append(owner)
        # A conventional lock may have multiple active owners sharing its directory.
        # Missing one old .csproj is insufficient to classify it as retired.
        if Path(relative).name == 'packages.lock.json':
            directory = contained(root, relative).parent
            active = [path for path in directory.iterdir() if path.suffix.lower() in {'.csproj', '.fsproj', '.vbproj'}]
            require(not active, 'retired lock has an active same-directory owner; use native restore ownership: ' + relative)
        result[relative] = {'sha256': digest, 'record': row['record'], 'owners': sorted(row['owners']),
                            'recordSha256': authority['sha256'], 'freshProductAcceptance': False}
        inputs[relative] = digest
    if owners:
        inputs.update(inactivity(root, [*owners, *result]))
    return result, inputs
