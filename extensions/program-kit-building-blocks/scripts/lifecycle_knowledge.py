"""Additive, exact dependency lifecycle facts; never alter qualification history."""
from pathlib import Path
import json
import re


def selected(blocks, directory, identity, sources=None):
    index = blocks.load_json(directory / 'index.json')
    entry = index['profiles'][identity]
    # The selected qualification lock is dependency authority, not today's default.
    recipe_ref = entry.get('qualificationRecipe')
    supplement_index = directory / 'lifecycle-knowledge/index.json'
    if not recipe_ref or not supplement_index.is_file():
        return None
    recipe_path = blocks.repository_path(directory, recipe_ref['path'])
    if blocks.raw_sha256(recipe_path) != recipe_ref['sha256']:
        blocks.fail('PKB611', 'selected lifecycle qualification recipe changed')
    recipe = blocks.load_json(recipe_path)
    lock_ref = recipe['nativeLock']
    # Recipe paths are repository-relative; installed registries retain that prefix.
    prefix = 'extensions/program-kit-building-blocks/references/dependency-profiles/'
    relative = lock_ref['path'].removeprefix(prefix)
    lock_path = blocks.repository_path(directory, relative)
    if blocks.raw_sha256(lock_path) != lock_ref['sha256']:
        blocks.fail('PKB611', 'selected lifecycle dependency lock changed')
    lock = blocks.load_json(lock_path)
    versions = {row['resolved'] for target in lock['dependencies'].values()
                for name, row in target.items() if name == 'CShells.Abstractions'}
    if len(versions) != 1:
        return None
    version = next(iter(versions))
    catalog = blocks.load_json(supplement_index)
    reference = catalog['versions'].get(version)
    if reference is None:
        return None
    manifest_path = blocks.repository_path(directory, reference['path'])
    if blocks.raw_sha256(manifest_path) != reference['sha256']:
        blocks.fail('PKB611', 'selected lifecycle knowledge changed')
    manifest = blocks.load_json(manifest_path)
    if manifest.get('version') != version:
        blocks.fail('PKB611', 'lifecycle knowledge differs from selected dependency lock')
    paths = [supplement_index, recipe_path, lock_path, manifest_path]
    for row in manifest['packages']:
        path = blocks.repository_path(directory, row['path'])
        if blocks.raw_sha256(path) != row['sha256']:
            blocks.fail('PKB611', 'selected lifecycle package fact changed')
        fact = blocks.publisher_package_fact(directory, row)
        if fact.get('id') != row['id'] or fact.get('version') != version:
            blocks.fail('PKB611', 'lifecycle package identity differs')
        if not re.fullmatch('[0-9a-f]{40}', fact.get('repository', {}).get('commit', '')):
            blocks.fail('PKB611', 'lifecycle publisher commit is invalid')
        if row['id'] == 'CShells.Abstractions':
            hashes = {value['contentHash'] for target in lock['dependencies'].values()
                      for name, value in target.items() if name == row['id']}
            if hashes != {fact.get('archiveSha512')}:
                blocks.fail('PKB611', 'lifecycle fact archive differs from selected qualification lock')
        paths.append(path)
    if sources is not None:
        sources.update({str(p): blocks.raw_sha256(p) for p in paths})
    return manifest
