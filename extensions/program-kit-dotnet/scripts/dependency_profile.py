"""Render engineering pins from selected dependencies or the qualified new-project default."""
from __future__ import annotations
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
    effective = blocks.effective_dependency_context(root)
    return previous if previous is not None else {
        'profile': effective['profile'], 'catalogResolutionSha256': effective['resolutionSha256'],
        'entrySha256': effective['profileEntrySha256']}


def retained_catalog(root: Path) -> dict | None:
    blocks = resolver()
    effective = blocks.effective_dependency_context(root)
    if effective['authority'] == 'legacy-installation': return None
    return effective['catalog']


def render(root: Path, relative: str, content: bytes) -> bytes:
    if relative not in {'eng/.config/dotnet-tools.json', 'eng/ProgramKit.Packages.props', 'eng/building-blocks.catalog.json'}:
        return content
    effective = resolver().effective_dependency_context(root)
    if effective['authority'] == 'legacy-installation': return content
    catalog = effective['catalog']
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
    binding = effective['sharedAbi']
    for identity in ('CShells.Abstractions','CShells.AspNetCore.Abstractions'):
        pin=binding['pins'][identity]
        text,count=re.subn(r'(Include="'+re.escape(identity)+r'" Version=")[^"]+("\s*/>)',
                          lambda match:match[1]+pin+match[2],text)
        if count!=1: raise ValueError('Managed shared-contract pin must occur exactly once: '+identity)
    return text.encode('utf-8')
