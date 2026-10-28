"""Reproduce predecessor storage for compatibility tests; never used by new releases."""
from pathlib import Path
import hashlib
import json
import shutil
from build_release import load_json, sha256


def pack_historical_package_facts(staging: Path) -> Path:
    """Copy a compact publication tree; retain every original staging file intact."""
    registry_relative = Path('extensions/program-kit-building-blocks/references/dependency-profiles')
    registry = staging / registry_relative
    index = load_json(registry / 'index.json')
    facts = {}
    def retain(item):
        path = (registry / item['path']).resolve()
        if not path.is_relative_to(registry.resolve()) or path.suffix not in {'.json', '.pack'}:
            raise ValueError('Historical publisher fact container escapes its registry')
        raw = path.read_bytes()
        if len(raw) > 64 * 1_048_576 or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Historical publisher fact container differs from its immutable authority')
        if item['path'] in facts and facts[item['path']] != raw:
            raise ValueError('Historical publisher fact container is ambiguous')
        facts[item['path']] = raw
    for entry in index['profiles'].values():
        recipe_ref = entry.get('qualificationRecipe')
        if recipe_ref:
            recipe_path = (registry / recipe_ref['path']).resolve()
            if not recipe_path.is_relative_to(registry.resolve()) or sha256(recipe_path) != recipe_ref['sha256']:
                raise ValueError('Historical qualification recipe differs from its original authority')
            recipe = load_json(recipe_path)
            retain(recipe_ref)
            prefix = registry_relative.as_posix() + '/'
            if not recipe['nativeLock']['path'].startswith(prefix):
                raise ValueError('Historical qualification lock escapes its registry')
            relative = recipe['nativeLock']['path'].removeprefix(prefix)
            lock = (registry / relative).resolve()
            if not lock.is_relative_to(registry.resolve()):
                raise ValueError('Historical qualification lock escapes its registry')
            raw = lock.read_bytes()
            if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != recipe['nativeLock']['sha256']:
                raise ValueError('Historical qualification lock differs from its original authority')
            retain({'path': relative, 'sha256': hashlib.sha256(raw).hexdigest()})
        if not entry.get('knowledge'):
            continue
        manifest = load_json(registry / entry['knowledge']['path'])
        for item in manifest.get('packages', []):
            if 'byteOffset' not in item:
                retain(item)
        for key in ('sourcePack', 'packagePack'):
            if manifest.get(key):
                retain(manifest[key])
    lifecycle = registry / 'lifecycle-knowledge/index.json'
    if lifecycle.is_file():
        for reference in load_json(lifecycle)['versions'].values():
            manifest_path = (registry / reference['path']).resolve()
            if not manifest_path.is_relative_to(registry.resolve()) or sha256(manifest_path) != reference['sha256']:
                raise ValueError('Historical lifecycle manifest differs from its original authority')
            manifest = load_json(manifest_path)
            for item in manifest['packages']:
                retain(item)
    if not facts:
        return staging
    publication = staging / '.program-kit-publication'
    if publication.exists():
        raise ValueError('Choose a fresh disposable publication tree')
    # Enumerate before creating the child. Copying never removes or modifies an
    # original profile, manifest, source container, or fact in the input tree.
    original_files = [path for path in staging.rglob('*') if path.is_file()]
    publication.mkdir()
    omitted = {registry_relative / relative for relative in facts}
    for source in original_files:
        relative = source.relative_to(staging)
        if relative not in omitted:
            target = publication / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    packed, entries = bytearray(), {}
    for relative, raw in sorted(facts.items()):
        entries[relative] = {'byteOffset': len(packed), 'byteLength': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        packed.extend(raw)
    target_registry = publication / registry_relative
    (target_registry / 'historical-package-facts.pack').write_bytes(packed)
    (target_registry / 'historical-package-facts.json').write_text(
        json.dumps({'schemaVersion': 1, 'entries': entries}, indent=2) + '\n', encoding='utf-8', newline='\n')
    return publication
