"""Review or preserve additive immutable catalog inputs; never edit the selecting index."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import building_blocks as blocks


def source_sha256(path: Path) -> str:
    """Retain the existing executor/native-lock LF-normalized evidence convention."""
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def qualification_inputs(profile_path: Path, catalog_path: Path, native_lock: Path,
                         recipe_path: Path, executor_path: Path, root: Path) -> dict:
    """Bind all explicit candidate inputs before restore or qualification sealing."""
    if any(value is None for value in (profile_path, catalog_path, native_lock, recipe_path, executor_path, root)):
        blocks.fail('PKB611', 'named qualification requires paired profile, catalog, native lock, recipe and executor inputs')
    recipe = blocks.load_json(recipe_path)
    if (set(recipe) != {'schemaVersion', 'id', 'profile', 'families', 'catalogSnapshot', 'nativeLock', 'executor'}
            or recipe.get('schemaVersion') != 1):
        blocks.fail('PKB611', 'named qualification recipe fields differ')
    blocks.require_id(recipe['id'], 'qualification recipe identity')

    def reference(value: dict, supplied: Path, label: str, *, normalized=False, profile=False) -> Path:
        value = blocks.require_object(value, label)
        if set(value) != ({'path', 'sha256', 'id'} if profile else {'path', 'sha256'}):
            blocks.fail('PKB611', f'named qualification {label} binding differs')
        bound = blocks.repository_path(root, blocks.normalize_path(value['path'], label + '.path'))
        expected = blocks.require_sha(value['sha256'], label + '.sha256')
        if (bound != supplied.resolve() or not bound.is_file()
                or (source_sha256(bound) if normalized else blocks.raw_sha256(bound)) != expected):
            blocks.fail('PKB611', f'named qualification {label} path or hash differs')
        return bound

    reference(recipe['profile'], profile_path, 'profile', profile=True)
    reference(recipe['nativeLock'], native_lock, 'native lock', normalized=True)
    reference(recipe['executor'], executor_path, 'executor', normalized=True)
    binding = blocks.require_object(recipe['catalogSnapshot'], 'recipe.catalogSnapshot')
    if set(binding) != {'path', 'sha256', 'base'}:
        blocks.fail('PKB611', 'named qualification catalog must bind an immutable base and target')
    reference({key: binding[key] for key in ('path', 'sha256')}, catalog_path, 'catalog')
    selected = blocks.load_json(profile_path)
    if selected.get('id') != recipe['profile']['id'] or selected.get('families') != recipe['families']:
        blocks.fail('PKB611', 'named qualification exact profile identity or family/tool versions differ')
    catalog = blocks.dependency_profile_catalog(root, {'catalogSnapshot': binding}, blocks.load_json(catalog_path))
    catalog = blocks.materialize_dependency_profile(catalog, selected)
    return {'catalog': catalog, 'nativeLock': native_lock.resolve(),
            'recipeSha256': source_sha256(executor_path), 'lockSha256': source_sha256(native_lock),
            'qualificationRecipeSha256': blocks.raw_sha256(recipe_path)}


def review(base_path: Path, target_path: Path) -> dict:
    base, target = blocks.load_json(base_path), blocks.load_json(target_path)
    blocks.validate_additive_profile_catalog(base, target)
    return {**blocks.dependency_profile_changes(base, target),
            'baseCompositionSha256': blocks.canonical_sha256(blocks.composition_projection(base)),
            'targetCompositionSha256': blocks.canonical_sha256(blocks.composition_projection(target)),
            'addedCapabilities': sorted(set(target['capabilities']) - set(base['capabilities'])),
            'addedCompositions': sorted(set(target['compositions']) - set(base['compositions']))}


def prepare(base_path: Path, target_path: Path, directory: Path, identity: str) -> dict:
    """Copy immutable source bytes and return the index's optional snapshot binding.

    This makes no qualification/publication claim and writes no profile, receipt,
    index or default. The ordinary maintained qualification gates remain required.
    """
    blocks.require_id(identity, 'catalog snapshot identity')
    sources = {'base': base_path.read_bytes(), 'target': target_path.read_bytes()}
    # Validate the exact bytes to be copied, rather than rereading paths between validation and binding.
    blocks.validate_additive_profile_catalog(
        blocks.require_object(json.loads(sources['base']), 'base catalog'),
        blocks.require_object(json.loads(sources['target']), 'target catalog'))
    references = {}
    pending = {}
    for label, content in sources.items():
        digest = hashlib.sha256(content).hexdigest()
        relative = f'catalogs/{identity}/{label}-{digest}.json'
        destination = blocks.repository_path(directory, relative)
        if destination.exists() and (not destination.is_file() or destination.read_bytes() != content):
            blocks.fail('PKB611', 'immutable catalog snapshot changed; preserve it and select new inputs')
        references[label] = {'path': relative, 'sha256': digest}
        pending[destination] = content
    # Check both destinations before creating either; never overwrite historical evidence.
    for destination, content in pending.items():
        if not destination.exists():
            blocks.atomic_write_bytes(destination, content, 'profile-catalog-snapshot')
    return {**references['target'], 'base': references['base']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['review', 'prepare'])
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--identity')
    args = parser.parse_args()
    if args.command == 'prepare' and (args.directory is None or args.identity is None):
        parser.error('prepare requires an explicit directory and snapshot identity')
    try:
        value = (prepare(args.base, args.target, args.directory, args.identity)
                 if args.command == 'prepare' else review(args.base, args.target))
        print(blocks.pretty_json(value), end='')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
