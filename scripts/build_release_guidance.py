"""Build reviewed, checksum-bound release and migration assets."""
import hashlib
import json
from pathlib import Path


def build(root, destination, version):
    root, destination = Path(root), Path(destination)
    data = json.loads((root / 'releases/history.json').read_text(encoding='utf-8'))
    destination.mkdir(parents=True, exist_ok=True)
    for entry in data['entries']:
        name = entry['guide']
        if Path(name).name != name or not name.endswith('.md'):
            raise ValueError('Release guide must be a Markdown basename')
        source = (root / 'releases' / name).read_bytes().replace(b'\r\n', b'\n')
        (destination / name).write_bytes(source)
        entry['sha256'] = hashlib.sha256(source).hexdigest()
    (destination / 'migration-index.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    import sys
    sys.path.insert(0, str(root / 'extensions/program-kit-governance/scripts'))
    from release_guidance import load_index
    load_index(destination, version)
    entry = next(entry for entry in data['entries'] if entry['version'] == version)
    (destination / 'RELEASE-NOTES.md').write_bytes((destination / entry['guide']).read_bytes())
    (destination / 'MIGRATIONS.md').write_text('\n\n'.join((destination / entry['guide']).read_text(encoding='utf-8')
                                                         for entry in data['entries']), encoding='utf-8')
    return destination
