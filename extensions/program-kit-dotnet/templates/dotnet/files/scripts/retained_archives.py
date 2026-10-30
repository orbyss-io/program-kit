"""Original reset-bound archive bytes and bounded active-input inactivity admission."""
from __future__ import annotations

import fnmatch
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from retained_inputs import canonical, contained, file_hash, read_json, require

EXCLUDED = {'.git', '.specify', 'config/program-kit', 'artifacts', 'bin', 'obj', 'node_modules', '__pycache__'}
XML_SUFFIXES = {'.csproj', '.fsproj', '.vbproj', '.proj', '.props', '.targets', '.slnx'}
PATH_ITEMS = {'Compile', 'Content', 'None', 'EmbeddedResource', 'AdditionalFiles', 'Analyzer', 'ProjectReference', 'Import', 'Folder', 'Project'}


def active_inputs(root):
    """Conservative static scope; unsupported expressions are gaps, never success."""
    for directory, children, files in os.walk(root, followlinks=False):
        children[:] = [name for name in children if name not in EXCLUDED
                       and (Path(directory) != root or name not in {'docs', 'specs', 'web', 'contracts'})]
        for name in children:
            contained(root, (Path(directory)/name).relative_to(root).as_posix())
        for name in files:
            path = Path(directory)/name
            if path.suffix.lower() in XML_SUFFIXES or path.suffix.lower() == '.sln':
                yield path
            elif name == 'architecture.json' and Path(directory) == root/'eng' or name.startswith('appsettings') and name.endswith('.json'):
                yield path


def inactivity(root, retired):
    roots = [canonical(path).rstrip('/') for path in retired]
    observed, visited = {}, set()
    def overlaps(value):
        value = value.replace('\\', '/').casefold()
        return any(relative.casefold() in value for relative in roots)
    def inspect(path):
        relative = path.relative_to(root).as_posix()
        contained(root, relative)
        if relative in visited:
            return
        visited.add(relative); observed[relative] = file_hash(path)
        require(len(visited) <= 4096, 'active input inspection exceeds its finite file budget')
        text = path.read_text(encoding='utf-8-sig')
        require(not overlaps(text), 'retired archive/owner referenced by active input: ' + relative)
        if path.suffix.lower() == '.json':
            value, _ = read_json(path)
            if path.name == 'architecture.json':
                for row in value.get('runtimeComposition', {}).get('projects', []):
                    target = contained(root, row['path'])
                    if target.is_file():
                        inspect(target)
            require(file_hash(path) == observed[relative], 'active input changed during inactivity inspection')
            return
        if path.suffix.lower() == '.sln':
            for reference in re.findall(r'^Project\([^\n]+?=\s*"[^"]+",\s*"([^"]+)"', text, re.M):
                target = (path.parent/reference.replace('\\', '/')).resolve()
                require(target.is_relative_to(root), 'external solution project needs an evaluated adapter')
                if target.suffix.lower() in XML_SUFFIXES and target.is_file():
                    inspect(target)
            require(file_hash(path) == observed[relative], 'active input changed during inactivity inspection')
            return
        document = ET.fromstring(text)
        for node in document.iter():
            tag = node.tag.rsplit('}', 1)[-1]
            if tag == 'NuGetLockFilePath':
                value = node.text or ''
                require(value and not any(marker in value for marker in ('$(', '@(', '%(', '*', '?')),
                        'inactivity coverage gap: dynamic lock owner needs an evaluated adapter: ' + relative)
                directories = {candidate.parent for candidate in active_inputs(root)
                               if candidate.suffix.lower() in {'.csproj', '.fsproj', '.vbproj'}}
                for directory in directories:
                    target = (directory/value.replace('\\', '/')).resolve()
                    require(not any(target == root/retired for retired in roots),
                            'retired lock reactivated by current native owner: ' + relative)
            if tag == 'Exec':
                require(False, 'inactivity coverage gap: active Exec needs an explicit evaluated input adapter: ' + relative)
            for key in ('Include', 'Update', 'Project', 'Path'):
                value = node.get(key)
                if value is None or tag not in PATH_ITEMS and key != 'Project' or key == 'Path' and tag != 'Project':
                    continue
                value = value.replace('$(MSBuildThisFileDirectory)', path.parent.as_posix() + '/')
                value = value.replace('$(MSBuildProjectDirectory)', path.parent.as_posix())
                value = value.replace('$(SolutionDir)', root.as_posix() + '/')
                require(not any(marker in value for marker in ('$(', '@(', '%(', '$[', '%')),
                        'inactivity coverage gap: dynamic active input needs an evaluated adapter: ' + relative)
                for item in value.replace('\\', '/').split(';'):
                    require(bool(item), 'inactivity coverage gap: empty active path in ' + relative)
                    target = Path(item) if Path(item).is_absolute() else path.parent/item
                    # Resolve the literal prefix before glob matching. A broad parent
                    # include can reach retired roots without spelling their names.
                    absolute = str(target.resolve()).replace('\\', '/')
                    require(target.resolve().is_relative_to(root), 'inactivity coverage gap: external active path in ' + relative)
                    for retired_root in roots:
                        retired_path = (root/retired_root).as_posix()
                        probe = retired_path + '/probe.cs'
                        prefix = re.split(r'[?*[]', absolute, maxsplit=1)[0].rstrip('/')
                        require(absolute.casefold() != retired_path.casefold()
                                and not fnmatch.fnmatchcase(probe.casefold(), absolute.casefold())
                                and not retired_path.casefold().startswith(prefix.casefold() + '/')
                                and not absolute.casefold().startswith(retired_path.casefold() + '/'),
                                'retired archive/owner reachable from active input: ' + relative)
                    if tag in {'Import', 'ProjectReference', 'Project'}:
                        import glob
                        from itertools import islice
                        matches = list(islice(glob.iglob(str(target), recursive=True), 4097))
                        require(len(matches) <= 4096, 'active import expansion exceeds its finite budget')
                        for imported in matches:
                            candidate = Path(imported).resolve()
                            require(candidate.is_relative_to(root), 'external active import needs an evaluated adapter')
                            inspect(candidate)
        require(file_hash(path) == observed[relative], 'active input changed during inactivity inspection')
    for path in active_inputs(root):
        inspect(path)
    return observed


def verify(root, rows, records):
    result, inputs, retired = [], {}, []
    require(isinstance(rows, list) and len(rows) <= 256, 'archive ownership must be a bounded array')
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'record'} and row['record'] in records,
                'archive must bind its original executed reset record')
        authority, original = records[row['record']]
        require(original.get('status') == 'abandoned' and isinstance(original.get('abandoned'), dict) and 0 < len(original['abandoned']) <= 4096,
                'archive needs original abandoned payload inventory')
        relative = canonical(original.get('archive'))
        require(relative.startswith('.program-kit/abandoned-features/') and relative not in retired,
                'archive root must be unique and derive from the original supported reset')
        directory = contained(root, relative)
        inventory_path = contained(root, relative + '/inventory.json')
        inventory, inventory_hash = read_json(inventory_path, original.get('archiveInventorySha256'))
        require(isinstance(inventory.get('files'), list), 'archive inventory has no original selected file set')
        files = {}
        for item in inventory['files']:
            require(isinstance(item, dict) and isinstance(item.get('sha256'), str), 'invalid archive inventory row')
            name = canonical(item.get('path'))
            require(name not in files, 'duplicate archive inventory path')
            files[name] = item['sha256']
        require(files == original['abandoned'] and inventory.get('preserved') == original.get('preserved'),
                'archive inventory differs from original supported reset record')
        expected = {'inventory.json', *files}
        actual = set()
        for path in directory.rglob('*'):
            contained(root, path.relative_to(root).as_posix())
            if path.is_file():
                name = path.relative_to(directory).as_posix(); actual.add(name)
                if name != 'inventory.json':
                    require(name in files and file_hash(path) == files[name], 'archive payload differs from original reset: ' + name)
                    inputs[relative + '/' + name] = files[name]
        require(actual == expected and len({name.casefold() for name in actual}) == len(actual),
                'archive has missing, extra or aliased payload files')
        inputs[relative + '/inventory.json'] = inventory_hash
        retired.append(relative)
        result.append({'root': relative, 'record': row['record'], 'files': len(files),
                       'inventoryAnchor': 'original-sha256' if original.get('archiveInventorySha256') else 'original-payload-and-preserved-map',
                       'freshProductAcceptance': False})
    if retired:
        inputs.update(inactivity(root, retired))
    return result, inputs
