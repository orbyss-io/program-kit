"""Assemble application facts for human receivers; no provisioning or publishing."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

from handoff_contract import declaration, contained, read, digest, safe_name, DECLARATION, source_inputs
import release_bundle


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8')


def check_hashes(repository: Path, sources: dict) -> None:
    if not isinstance(sources, dict) or not sources:
        raise ValueError('PKH005 source-backed metadata/evidence requires nonempty source hashes')
    for name, expected in sources.items():
        if digest(contained(repository, name)) != expected:
            raise ValueError(f'PKH005 stale source input: {name}; regenerate from its owning producer')


def reject_secrets(payload: bytes, name: str) -> None:
    if payload.startswith(b'\xef\xbb\xbf'):
        payload = payload[3:]
    text = payload.decode('utf-8', errors='replace')
    if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|\bBearer\s+[A-Za-z0-9._~-]{8,}|https?://[^\s/:]+:[^\s/@]+@', text):
        raise ValueError(f'PKH006 credential material in {name}')
    if re.search(r'(?im)\b(?:password|clientsecret|api[_-]?key|access[_-]?token)\s*[:=]\s*[\x22\x27]?(?!\$\{|<|null\b|false\b|true\b)[A-Za-z0-9][^\s,;\x22\x27]+', text):
        raise ValueError(f'PKH006 credential assignment in {name}')
    if name.lower().endswith('.json'):
        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    # Metadata classification is a boolean, never a credential value.
                    sensitive = re.search(r'password|clientsecret|apikey|access.?token|privatekey|connectionstrings|credentials', key, re.I)
                    if sensitive and child not in (None, '', {}, []):
                        raise ValueError(f'PKH006 secret value in {name}: {key}')
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(json.loads(text))


def archive_members(payload: bytes, name: str) -> dict[str, bytes]:
    import io
    result = {}
    seen = set()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 1024 * 1024 * 1024:
            raise ValueError(f'PKH002 archive too large: {name}')
        for info in archive.infolist():
            member = safe_name(info.filename.rstrip('/') if info.is_dir() else info.filename)
            if member.casefold() in seen or stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1:
                raise ValueError(f'PKH002 duplicate, linked or encrypted archive entry: {name}/{member}')
            seen.add(member.casefold())
            if not info.is_dir():
                result[member] = archive.read(info)
    return result


def settings_metadata(repository: Path, path: Path) -> dict:
    value = read(path)
    required = {'schemaVersion', 'owner', 'scope', 'complete', 'sources', 'settings', 'semanticConstraints'}
    if set(value) != required or value['schemaVersion'] != 1 or type(value['complete']) is not bool:
        raise ValueError('PKH007 invalid settings metadata envelope')
    for key in ('owner', 'scope'):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f'PKH007 settings {key} required')
    check_hashes(repository, value['sources'])
    if not isinstance(value['settings'], list) or not isinstance(value['semanticConstraints'], list) or any(not isinstance(x, str) or not x for x in value['semanticConstraints']):
        raise ValueError('PKH007 settings and semanticConstraints must be arrays')
    seen = set()
    fields = {'path', 'type', 'required', 'secret', 'constraints', 'binding', 'precedence', 'reload', 'description'}
    for item in value['settings']:
        if not isinstance(item, dict) or not fields <= set(item) or set(item) - fields - {'default'}:
            raise ValueError('PKH007 invalid setting metadata fields')
        if (not isinstance(item['path'], str) or not item['path'] or item['path'] in seen
                or item['type'] not in {'string', 'integer', 'number', 'boolean', 'array', 'object'}
                or type(item['required']) is not bool or type(item['secret']) is not bool
                or item['reload'] not in {'restart', 'reload', 'immutable'}
                or not isinstance(item['constraints'], dict)
                or not isinstance(item['precedence'], list) or not item['precedence']
                or any(not isinstance(x, str) or not x.strip() for x in item['precedence'])
                or any(not isinstance(item[k], str) or not item[k].strip() for k in ('binding', 'description'))):
            raise ValueError('PKH007 invalid or conflicting setting metadata')
        seen.add(item['path'])
        if item['secret'] and ('default' in item or {'default','example','examples','const','enum'}.intersection(item['constraints'])):
            raise ValueError('PKH006 secret settings cannot export defaults or examples')
        if 'default' in item:
            default = item['default']
            types = {'string': str, 'integer': int, 'number': (int, float), 'boolean': bool, 'array': list, 'object': dict}
            if not isinstance(default, types[item['type']]) or (item['type'] in {'integer','number'} and isinstance(default, bool)):
                raise ValueError('PKH007 default differs from declared setting type')
    reject_secrets(path.read_bytes(), path.name)
    return value


def assemble(repository: Path, *, draft: bool = False) -> dict:
    repository = repository.resolve()
    selected = declaration(repository)
    missing = [f'{key}: {item["reason"]}' for key, item in selected['categories'].items() if item['status'] == 'missing']
    descriptor_path = contained(repository, selected['bundleDescriptor'])
    descriptor = read(descriptor_path)
    identity = descriptor['application']
    if (identity['id'] != selected['applicationId'] or identity['version'] != (repository / 'VERSION').read_text().strip()
            or identity['sourceCommit'] != release_bundle.source_commit(repository)):
        raise ValueError('PKH008 bundle application identity/version/source mismatch; describe the current release first')
    # Validate the current source/configuration/package closure before touching final output.
    closure_path = contained(repository, descriptor['runtimeClosure']['evidence'])
    stage = repository / 'artifacts/release-bundle'
    closure = release_bundle.runtime_closure.validate(repository, stage, closure_path, release_bundle.PROGRAM_KIT_VERSION)
    if closure.get('sourceInputs') != source_inputs(repository):
        raise ValueError('PKH005 stale/missing stage source bindings; rebuild and restage')
    if descriptor['runtimeClosure']['digest'] != closure['closureDigest']:
        raise ValueError('PKH005 stale bundle closure')
    expected_files = {x['file']: x['sha256'] for x in closure['configuration'] + closure['packages']}
    if {x['file']: x['sha256'] for x in descriptor['files']} != expected_files:
        raise ValueError('PKH005 bundle descriptor differs from current closure')
    if descriptor['hostImage']['reference'] != descriptor['hostImage']['repository']+'@'+descriptor['hostImage']['digest'] or descriptor['hostImage']['repository'] != 'ghcr.io/orbyss-io/foundation-host' or not re.fullmatch(r'sha256:[0-9a-f]{64}', descriptor['hostImage']['digest']):
        raise ValueError('PKH008 invalid published host identity')
    archive_path = descriptor_path.with_suffix('.zip')
    contained(repository, archive_path.relative_to(repository).as_posix())
    checksum_path = archive_path.with_suffix('.zip.sha256')
    checksum = contained(repository, checksum_path.relative_to(repository).as_posix()).read_text().split()
    if checksum != [digest(archive_path), archive_path.name]:
        raise ValueError('PKH005 tampered bundle checksum')
    members = archive_members(archive_path.read_bytes(), archive_path.name)
    if members.pop('application-bundle.json', None) != descriptor_path.read_bytes() or set(members) != set(expected_files):
        raise ValueError('PKH005 bundle archive/descriptor inventory mismatch')
    for name, payload in members.items():
        if hashlib.sha256(payload).hexdigest() != expected_files[name]:
            raise ValueError(f'PKH005 tampered bundle member: {name}')
        if name.endswith('.json'):
            reject_secrets(payload, name)
        if name.endswith('.nupkg'):
            for inner, data in archive_members(payload, name).items():
                if inner.endswith(('.json', '.md', '.yml', '.yaml', '.config', '.py', '.cs', '.ps1', '.sh', '.xml', '.txt')):
                    reject_secrets(data, inner)
    files = {}
    rows = []
    def add(path: Path, category: str) -> str:
        name = path.relative_to(repository).as_posix()
        contained(repository, name)
        if {'.specify', '.program-kit', '.git', '.agents', '.codex', 'node_modules', 'cache', 'obj', 'bin'}.intersection(Path(name).parts) or Path(name).name in {'.env', 'AGENTS.md'}:
            raise ValueError(f'PKH002 toolkit/cache/private input cannot be distributed: {name}')
        destination = 'inputs/' + name
        if any(x.casefold() == destination.casefold() and x != destination for x in files):
            raise ValueError('PKH002 case-conflicting receiver paths')
        payload = path.read_bytes()
        if path.suffix in {'.json', '.md', '.yml', '.yaml', '.config', '.txt', '.xml', '.ps1', '.sh', '.sql'}:
            reject_secrets(payload, name)
        if path.suffix in {'.zip', '.nupkg'}:
            archive_members(payload, name)
        if destination not in files:
            files[destination] = payload
            rows.append({'path': destination, 'source': name, 'category': category,
                         'sha256': hashlib.sha256(payload).hexdigest()})
        return destination
    bundle_ref = add(descriptor_path, 'application')
    add(archive_path, 'application'); add(checksum_path, 'application'); add(closure_path, 'integrity')
    add(contained(repository, DECLARATION), 'declaration')
    packages = {}
    required_features = set()
    for entry in closure['packages']:
        package = contained(stage, entry['file'])
        package_id, version = release_bundle.package_identity(package)
        package_members = archive_members(package.read_bytes(), package.name)
        descriptor_entry = next((name for name in ('orbyss-foundation/feature.json', 'program-kit/feature.json') if name in package_members), None)
        packages[package_id] = {'path': add(package, 'package'), 'version': version,
                              'featureDescriptor': descriptor_entry}
        required_features.update(feature['identity'] for feature in release_bundle.package_features(package)
                                 if feature.get('requiresContractCoverage') is True)
    registry_path = contained(repository, selected['openapiRegistry'])
    registry = read(registry_path)
    if registry.get('schemaVersion') != 1 or not isinstance(registry.get('contracts'), list):
        raise ValueError('PKH009 invalid OpenAPI registry')
    add(registry_path, 'interface-registry')
    contracts = {}
    if registry['contracts']:
        receipt_path = contained(repository, 'artifacts/program-kit/openapi/pipeline.json')
        receipt = read(receipt_path)
        if receipt.get('satisfied') is not True or receipt.get('registrySha256') != digest(registry_path) or receipt.get('sourceInputs') != source_inputs(repository):
            raise ValueError('PKH005 stale OpenAPI pipeline inputs; rerun the native pipeline')
        by_id = {x['identity']: x for x in receipt['contracts']}
        if len(by_id) != len(receipt['contracts']):
            raise ValueError('PKH009 duplicate pipeline contract identity')
        for name in registry['contracts']:
            path = contained(repository, name); contract = read(path); cid = contract['identity']
            if cid in contracts or cid not in by_id:
                raise ValueError('PKH009 conflicting or unresolved API contract')
            row = by_id[cid]
            for file, hash_key in [(path, 'contractSha256'), (contained(repository, contract['rawDocument']), 'rawDocumentSha256'),
                                   (contained(repository, contract['artifact']), 'artifactSha256'), (contained(repository, contract['baseline']), 'baselineSha256')]:
                if digest(file) != row[hash_key]:
                    raise ValueError(f'PKH005 stale API contract: {cid}/{hash_key}')
            for kind, output in [('generator', 'generatedTypes'), ('application', 'tsconfig')]:
                for field, hash_key in [('packageJson','packageJsonSha256'),('lockFile','lockFileSha256'),(output,output+'Sha256')]:
                    if digest(contained(repository, contract[kind][field])) != row[kind][hash_key]:
                        raise ValueError(f'PKH005 stale API {kind}: {cid}/{field}')
            exported = contained(repository, f'artifacts/program-kit/openapi/{cid}-export.json')
            if digest(exported) != row['exportEvidenceSha256']:
                raise ValueError('PKH005 stale exporter evidence')
            add(path, 'interface-declaration'); add(contained(repository, contract['baseline']), 'interface-baseline')
            contracts[cid] = {'path': add(contained(repository, contract['artifact']), 'interface'), 'shell': contract['shell'], 'features': contract['features']}
            shell_composition = release_bundle.shell_composition
            activated = shell_composition.activated_features(stage)
            if contract['shell'] not in activated or not set(contract['features']) <= activated[contract['shell']]:
                raise ValueError('PKH009 contract shell/features unresolved in delivered activation')
        if set(by_id) != set(contracts):
            raise ValueError('PKH009 pipeline contains unregistered contracts')
        add(receipt_path, 'integrity')
    for shell, active in release_bundle.shell_composition.activated_features(stage).items():
        covered = {feature for item in contracts.values() if item['shell'] == shell for feature in item['features']}
        absent = (required_features & active) - covered
        if absent:
            raise ValueError('PKH009 missing publisher-required API contract coverage: '+shell+'/'+','.join(sorted(absent)))
    bound_packages = set(); bound_contracts = set()
    for component in selected['components']:
        if not set(component['packages']) <= packages.keys() or not set(component['contracts']) <= contracts.keys():
            raise ValueError('PKH009 component references unresolved package/API identity')
        bound_packages.update(component['packages']); bound_contracts.update(component['contracts'])
    if bound_packages != set(packages) or bound_contracts != set(contracts):
        raise ValueError('PKH009 every delivered package and registered API needs explicit component bindings')
    owners = set(); settings_keys = set()
    for key, category in selected['categories'].items():
        for name in category['files']:
            path = contained(repository, name)
            if key == 'settings':
                metadata = settings_metadata(repository, path)
                if metadata['complete']:
                    owners.add((metadata['owner'], metadata['scope']))
                else:
                    missing.append('settings: incomplete metadata from '+metadata['owner'])
                for item in metadata['settings']:
                    setting_key = (metadata['scope'], item['path'])
                    if setting_key in settings_keys:
                        raise ValueError('PKH007 conflicting setting path/scope')
                    settings_keys.add(setting_key)
            if key == 'migrations':
                migration = read(path)
                if set(migration) != {'artifact', 'invocation', 'compatibility', 'owner'} or any(not isinstance(x, str) or not x.strip() for x in migration.values()):
                    raise ValueError('PKH010 migration requires actual artifact/invocation/compatibility/owner')
                add(contained(repository, migration['artifact']), 'migration-artifact')
            add(path, key)
    required = {(owner, scope) for owner, scopes in selected['requiredSettingsScopes'].items() for scope in scopes}
    missing += ['settings: missing owner/scope '+owner+'/'+scope for owner, scope in sorted(required - owners)]
    profile_schema = repository / 'eng/spa-pkce.schema.json'
    if profile_schema.is_file():
        add(profile_schema, 'profile-schema')  # Structural selected-profile contract, not framework coverage.
    if missing and not draft:
        raise ValueError('PKH011 receiver handoff incomplete: '+ '; '.join(missing))
    if (repository / 'eng/README.md').is_file():
        add(repository / 'eng/README.md', 'documentation')
    for name in ('application-handoff.schema.json', 'settings-metadata.schema.json',
                 'handoff-index.schema.json', 'application-bundle.schema.json'):
        payload = Path(__file__).with_name(name).read_bytes()
        destination = 'format/' + name
        files[destination] = payload
        rows.append({'path': destination, 'source': 'eng/'+name, 'category': 'format',
                     'sha256': hashlib.sha256(payload).hexdigest()})
    verifier = Path(__file__).with_name('verify_handoff.py').read_bytes()
    files['verify_handoff.py'] = verifier
    rows.append({'path': 'verify_handoff.py', 'source': 'eng/verify_handoff.py', 'category': 'verification', 'sha256': hashlib.sha256(verifier).hexdigest()})
    index = {'schemaVersion': 1, 'status': 'incomplete' if missing else 'ready', 'missing': sorted(set(missing)),
             'application': identity, 'hostImage': descriptor['hostImage'], 'bundle': bundle_ref,
             'components': selected['components'], 'packages': packages, 'contracts': contracts,
             'categories': selected['categories'], 'files': sorted(rows, key=lambda x: x['path'])}
    files['index.json'] = canonical(index)
    output = repository / 'artifacts/handoff'
    contained(repository, 'artifacts/handoff/index.json', exists=False)
    output.mkdir(parents=True, exist_ok=True)
    # Only two final files; validate everything before atomic per-file replacement.
    for name, data in [('index.json', files['index.json'])]:
        pending = output / (name+'.tmp'); pending.write_bytes(data); pending.replace(output/name)
    with tempfile.NamedTemporaryFile(dir=output, suffix='.zip', delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, (1980,1,1,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        temporary.replace(output/'application-handoff.zip')
    finally:
        temporary.unlink(missing_ok=True)
    (output/'application-handoff.zip.sha256').write_text(digest(output/'application-handoff.zip')+'  application-handoff.zip\n',encoding='utf-8')
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--draft', action='store_true', help='Emit explicitly incomplete inventory; never suitable for release.')
    args = parser.parse_args()
    try:
        index = assemble(Path(args.repository), draft=args.draft)
        print('Application handoff: '+index['status']+' (artifacts/handoff/application-handoff.zip)')
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
