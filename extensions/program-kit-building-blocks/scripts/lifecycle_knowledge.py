"""Additive, exact dependency lifecycle facts; never alter qualification history."""
from pathlib import Path
import json
import re

import hashlib


def selected(blocks, directory, identity, sources=None):
    index = blocks.load_json(directory / 'index.json')
    entry = index['profiles'][identity]
    # The selected qualification lock is dependency authority, not today's default.
    recipe_ref = entry.get('qualificationRecipe')
    supplement_index = directory / 'lifecycle-knowledge/index.json'
    if not recipe_ref or not supplement_index.is_file():
        return None
    recipe_path = blocks.repository_path(directory, recipe_ref['path'])
    recipe = blocks.qualification_recipe(directory, recipe_ref)
    lock_ref = recipe['nativeLock']
    # Recipe paths are repository-relative; installed registries retain that prefix.
    prefix = 'extensions/program-kit-building-blocks/references/dependency-profiles/'
    relative = lock_ref['path'].removeprefix(prefix)
    lock_path = blocks.profile_storage_path(directory, relative)
    # Native qualification recipes bind the maintained LF-normalized lock digest.
    # NuGet writes CRLF on Windows; content changes still invalidate this binding.
    storage = blocks.filesystem_root(directory / 'historical-package-facts.json')
    physical_lock = blocks.filesystem_root(lock_path)
    if physical_lock.is_file():
        lock_bytes = physical_lock.read_bytes()
        lock_sources = [lock_path]
    else:
        # Publication may store original qualification locks in the same bounded
        # fact container. The recipe still owns their LF-normalized authority.
        if storage.stat().st_size > 1_048_576:
            blocks.fail('PKB611', 'historical package storage index exceeds its bound')
        row = blocks.load_json(storage)['entries'][relative]
        lock_bytes = blocks.publisher_document_bytes(directory,
            {'path': relative, 'sha256': row['sha256']}, 16 * 1_048_576)
        lock_sources = [storage, directory / 'historical-package-facts.pack']
    if hashlib.sha256(lock_bytes.replace(b'\r\n', b'\n')).hexdigest() != lock_ref['sha256']:
        blocks.fail('PKB611', 'selected lifecycle dependency lock changed')
    lock = json.loads(lock_bytes)
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
    recipe_sources = ([recipe_path] if blocks.filesystem_root(recipe_path).is_file() else
                      [storage, directory / 'historical-package-facts.pack'])
    paths = [supplement_index, *recipe_sources, *lock_sources, manifest_path]
    for row in manifest['packages']:
        path = blocks.repository_path(directory, row['path'])
        if hashlib.sha256(blocks.publisher_document_bytes(directory, row, 16 * 1_048_576)).hexdigest() != row['sha256']:
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
        paths.extend([path] if blocks.filesystem_root(path).is_file() else
                     [storage, directory / 'historical-package-facts.pack'])
    if sources is not None:
        sources.update({str(p): blocks.raw_sha256(p) for p in paths})
    return manifest
