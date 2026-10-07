"""Render engineering pins from selected dependencies or the qualified new-project default."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path


def resolver():
    # dotnet_sync is also a standalone adapter. Its sibling extensions are not
    # importable by module name in that process; load the maintained file directly.
    path = Path(__file__).resolve().parents[2] / 'program-kit-building-blocks/scripts/building_blocks.py'
    spec = importlib.util.spec_from_file_location('dependency_profile_blocks', path)
    if spec is None or spec.loader is None:
        raise ValueError('Installed building-block resolver is unavailable')
    blocks = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = blocks
    spec.loader.exec_module(blocks)
    return blocks


def engineering_default(root: Path) -> dict | None:
    if (root / 'docs/architecture/building-block-selection.json').is_file() or (root / '.program-kit/dependency-profile.json').is_file():
        return None
    managed = root / '.program-kit/managed.json'
    previous = json.loads(managed.read_text(encoding='utf-8')).get('newProjectDependencyProfile') if managed.is_file() else None
    if managed.is_file() and previous is None:
        return None  # Existing installations follow their existing reviewed upgrade path.
    blocks = resolver()
    directory = blocks.profile_registry()
    index = blocks.load_json(directory / 'index.json')
    identity = previous['profile'] if previous else index['default']
    catalog, selected = blocks.qualified_dependency_profile(directory, identity, blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
    record = {'profile': selected['id'], 'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog),
              'entrySha256': blocks.canonical_sha256(index['profiles'][identity])}
    if previous is not None and previous != record:
        if (previous.get('profile')==record['profile'] and previous.get('catalogResolutionSha256')==record['catalogResolutionSha256']
                and blocks.profile_entry_matches_hash(index['profiles'][identity],previous.get('entrySha256'))):
            return previous
        raise ValueError('Scaffolded dependency qualification changed; review its profile explicitly')
    return record


def retained_catalog(root: Path) -> dict | None:
    binding = root / '.program-kit/dependency-profile.json'
    if not binding.is_file():
        # Upgrade preflight is read-only and precedes profile capture. Verify the
        # existing Accepted selection against its installed catalog at that point.
        selection_path = root / 'docs/architecture/building-block-selection.json'
        catalog_path = root / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
        blocks = resolver()
        if selection_path.is_file():
            selection = json.loads(selection_path.read_text(encoding='utf-8'))
            if selection.get('status') in {'Draft', 'Accepted'}:
                if not catalog_path.is_file(): catalog_path = blocks.default_catalog(Path(blocks.__file__))
                catalog = blocks.load_json(catalog_path)
                blocks.validate_catalog(catalog)
                blocks.verify_catalog_binding(selection, catalog)
                return catalog
            raise ValueError('Dependency selection must be Draft or Accepted before rendering its pins')
        default = engineering_default(root)
        return blocks.new_project_catalog(default['profile']) if default else None
    record = json.loads(binding.read_text(encoding='utf-8'))
    selection = json.loads((root / 'docs/architecture/building-block-selection.json').read_text(encoding='utf-8'))
    if record.get('schemaVersion') != 2 or record.get('resolutionSha256') != selection['catalog'].get('resolutionSha256'):
        raise ValueError('Dependency profile differs from accepted selection; review its transition')
    path = (root / record['catalogPath']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record.get('catalogSha256'):
        raise ValueError('Retained dependency profile is missing, changed or outside the consumer')
    blocks = resolver()
    catalog = blocks.load_json(path)
    blocks.validate_catalog(catalog)
    blocks.verify_catalog_binding(selection, catalog)
    profile = blocks.repository_path(root, record['profilePath'])
    if blocks.raw_sha256(profile) != record['profileSha256'] or blocks.load_json(profile) != blocks.dependency_profile_value(catalog, record['id']):
        raise ValueError('Immutable exact dependency profile changed')
    blocks.verify_new_project_profile(root, catalog, [])
    return catalog


def render(root: Path, relative: str, content: bytes) -> bytes:
    if relative not in {'eng/.config/dotnet-tools.json', 'eng/ProgramKit.Packages.props', 'eng/building-blocks.catalog.json'}:
        return content
    catalog = retained_catalog(root)
    if catalog is None:
        return content
    if relative == 'eng/building-blocks.catalog.json':
        return (json.dumps(catalog, indent=2) + '\n').encode('utf-8')
    if relative.endswith('dotnet-tools.json'):
        value = json.loads(content)
        value['tools']['orbyss.foundation.openapi.exporter']['version'] = catalog['packages']['nuget:Orbyss.Foundation.OpenApi.Exporter']['version']
        return (json.dumps(value, indent=2) + '\n').encode('utf-8')
    pin = catalog['packages']['nuget:Orbyss.Foundation.Analyzers']['version']
    text, count = re.subn(r'(Include="Orbyss.Foundation.Analyzers" Version=")[^"]+("\s*/>)', lambda m: m[1] + pin + m[2], content.decode('utf-8'))
    if count != 1:
        raise ValueError('Managed analyzer pin must occur exactly once')
    builder = catalog['packages'].get('nuget:Orbyss.Foundation.Build')
    if builder is not None:
        text, count = re.subn(r'(Include="Orbyss.Foundation.Build" Version=")[^"]+("\s*/>)',
                             lambda match: match[1] + builder['version'] + match[2], text)
        if count != 1:
            raise ValueError('Managed builder pin must occur exactly once')
    # Runtime/shared contracts advance together. Retained consumers must keep the
    # ABI of their selected Host when the kit's new-project default advances.
    blocks=resolver()
    contracts=blocks.load_json(blocks.profile_registry()/'engineering-contracts.json')
    version=catalog['families']['foundation']['releaseVersion']
    binding=contracts.get('releases',{}).get(version.split('-')[0])
    if binding is None:
        raise ValueError('Kit is missing publisher shared-contract pins for selected Foundation '+version)
    for identity in ('CShells.Abstractions','CShells.AspNetCore.Abstractions'):
        pin=binding['pins'][identity]
        text,count=re.subn(r'(Include="'+re.escape(identity)+r'" Version=")[^"]+("\s*/>)',
                          lambda match:match[1]+pin+match[2],text)
        if count!=1: raise ValueError('Managed shared-contract pin must occur exactly once: '+identity)
    return text.encode('utf-8')
