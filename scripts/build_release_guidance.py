"""Build reviewed, checksum-bound release and migration assets."""
import hashlib
import json
from pathlib import Path


def validate_recipes(root, changes):
    registry = json.loads((root / 'extensions/program-kit-governance/references/consumer-migration-recipes.json').read_text(encoding='utf-8'))
    if registry.get('schemaVersion') != 1 or not isinstance(registry.get('recipes'), list):
        raise ValueError('Unsupported consumer migration recipe registry')
    recipes = {}
    for recipe in registry['recipes']:
        if recipe.get('id') in recipes or recipe.get('version') != 1:
            raise ValueError('Duplicate or unsupported migration recipe')
        for field in ('id', 'applicability', 'preservedBehavior', 'allowedScope', 'recoveryLimits'):
            if not isinstance(recipe.get(field), str) or not recipe[field].strip():
                raise ValueError('Migration recipe requires ' + field)
        for field in ('ordering', 'verification'):
            if not isinstance(recipe.get(field), list) or not recipe[field] or not all(isinstance(v, str) and v.strip() for v in recipe[field]):
                raise ValueError('Migration recipe requires ' + field)
        recipes[recipe['id']] = recipe
    if any(change.get('method') not in recipes for change in changes):
        raise ValueError('Consumer semantic metadata references an unmaintained migration method')


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
    semantic = root / 'releases/consumer-changes.json'
    if semantic.is_file():
        payload = semantic.read_bytes().replace(b'\r\n', b'\n')
        validate_recipes(root, json.loads(payload)['changes'])
        filename = f'consumer-changes-{version}.json'
        (destination / filename).write_bytes(payload)
        data['consumerChanges'] = {'file': filename, 'sha256': hashlib.sha256(payload).hexdigest()}
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
