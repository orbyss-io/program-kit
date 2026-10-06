"""Consumer identity and contained reference helpers. No toolkit/runtime initialization."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

DECLARATION = 'eng/application-handoff.json'
CATEGORIES = {'documentation', 'runtime', 'settings', 'assets', 'migrations'}


def read(path: Path) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'PKH001 ambiguous duplicate JSON key: {key}')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f'PKH001 non-JSON numeric constant: {value}')
    value = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(value, dict):
        raise ValueError(f'PKH001 expected JSON object: {path}')
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_name(value: str) -> str:
    if (not isinstance(value, str) or not value or any(c in value for c in '\\:<>|?*')
            or any(ord(c) < 32 for c in value)):
        raise ValueError(f'PKH002 unsafe relative path: {value!r}')
    parts = value.split('/')
    if (any(p in {'', '.', '..'} or p.endswith(('.', ' ')) for p in parts)
            or any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.I) for p in parts)
            or PurePosixPath(value).is_absolute()):
        raise ValueError(f'PKH002 unsafe relative path: {value!r}')
    return value


def contained(root: Path, name: str, *, exists: bool = True) -> Path:
    safe_name(name)
    root = root.resolve()
    path = root / name
    current = path
    while current != root:
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError(f'PKH002 linked input: {name}')
        current = current.parent
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'PKH002 escaped input: {name}')
    if exists and not path.is_file():
        raise ValueError(f'PKH003 missing required input: {name}')
    return path


def declaration(root: Path) -> dict:
    path = root / DECLARATION
    if not path.is_file():
        raise ValueError('PKH004 stable identity is missing. Create eng/application-handoff.json; '
                         'for an existing application explicitly retain its last released descriptor ID. '
                         'Never derive a new release identity from a renamed checkout.')
    value = read(path)
    if set(value) != {'schemaVersion', 'applicationId', 'components', 'bundleDescriptor', 'openapiRegistry', 'categories', 'requiredSettingsScopes'} or value.get('schemaVersion') != 1:
        raise ValueError('PKH001 invalid application handoff declaration envelope')
    identity = value.get('applicationId')
    if not isinstance(identity, str) or not identity.strip() or identity != identity.strip() or any(ord(c) < 32 for c in identity) or any(c in identity for c in '/\\:'):
        raise ValueError('PKH004 explicitly select applicationId in eng/application-handoff.json; '
                         'retain the historical released ID when migrating')
    for key in ('bundleDescriptor', 'openapiRegistry'):
        safe_name(value[key])
    if set(value['categories']) != CATEGORIES:
        raise ValueError('PKH001 explicitly declare every applicable category (or explain not-applicable/missing)')
    for key, category in value['categories'].items():
        if (set(category) != {'status', 'reason', 'files'} or category['status'] not in {'included', 'not-applicable', 'missing'}
                or not isinstance(category['reason'], str) or not category['reason'].strip()
                or not isinstance(category['files'], list)
                or (category['status'] == 'included') != bool(category['files'])):
            raise ValueError(f'PKH001 invalid category: {key}')
        if key in {'documentation', 'runtime', 'settings'} and category['status'] == 'not-applicable':
            raise ValueError(f'PKH001 {key} is required for an application handoff')
        for name in category['files']:
            safe_name(name)
    scopes = value['requiredSettingsScopes']
    if (not isinstance(scopes, dict) or not scopes
            or any(not isinstance(owner, str) or not owner or not isinstance(items, list) or not items
                   or any(not isinstance(x, str) or not x for x in items) or len(set(items)) != len(items)
                   for owner, items in scopes.items())):
        raise ValueError('PKH001 requiredSettingsScopes must explicitly identify owner/scope coverage')
    components = value['components']
    if not isinstance(components, list) or not components:
        raise ValueError('PKH001 explicit component/artifact bindings are required')
    ids = set()
    for component in components:
        if (set(component) != {'id', 'packages', 'contracts'} or not isinstance(component['id'], str)
                or not component['id'] or component['id'] in ids):
            raise ValueError('PKH001 invalid or repeated component identity')
        ids.add(component['id'])
        for key in ('packages', 'contracts'):
            items = component[key]
            if not isinstance(items, list) or any(not isinstance(x, str) or not x for x in items) or len(set(items)) != len(items):
                raise ValueError('PKH001 invalid component references')
    return value


def application_identity(root: Path) -> str:
    path = root / DECLARATION
    if not path.is_file():
        raise ValueError('PKH004 stable identity missing: create eng/application-handoff.json with '
                         'an explicit applicationId, retaining the last historical descriptor ID; '
                         'old descriptors remain readable and must not be rewritten')
    value = read(path)
    identity = value.get('applicationId')
    if value.get('schemaVersion') != 1 or not isinstance(identity, str) or not identity.strip() or identity != identity.strip() or any(ord(c) < 32 for c in identity) or any(c in identity for c in '/\\:'):
        raise ValueError('PKH004 explicitly select applicationId; preserve the last released ID when migrating')
    return identity


def source_inputs(repository: Path) -> dict[str, str]:
    """Bind producer evidence to current native source, not agent state or generated caches."""
    generated = set()
    registry = repository / 'eng/openapi-contracts.json'
    if registry.is_file():
        for name in read(registry).get('contracts', []):
            contract = read(contained(repository, name))
            output = contract.get('generator', {}).get('generatedTypes')
            if output:
                generated.add(contained(repository, output, exists=False))
    candidates = [p for p in (repository / 'src').rglob('*') if p.is_file() and p not in generated
                  and not {'bin', 'obj', 'node_modules', 'dist'}.intersection(p.relative_to(repository).parts)]
    candidates += [repository / name for name in ('VERSION', 'Directory.Packages.props',
                    'Directory.Build.props', 'Directory.Build.targets', 'shells.json', 'hostsettings.json',
                    'nuplane.settings.json', 'eng/web-profile.shells.json', 'eng/.config/dotnet-tools.json')
                   if (repository / name).is_file()]
    return {p.relative_to(repository).as_posix(): digest(contained(repository, p.relative_to(repository).as_posix()))
            for p in sorted(candidates)}
