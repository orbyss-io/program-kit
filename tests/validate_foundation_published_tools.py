"""Qualify official public Build/exporter binaries against an explicitly selected runtime.

This is component compatibility evidence, never profile promotion or public Host acceptance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/foundation-consumer-contracts/published-tools/v1'
TOOL = 'Orbyss.Foundation.OpenApi.Exporter'
TOOL_VERSION = '0.2.4'
BUILD = 'Orbyss.Foundation.Build'
BUILD_VERSION = '0.1.0'
COMMAND = 'orbyss-foundation-openapi-export'
FEATURE = 'PublishedTools.Contract'
FIXTURE_VERSION = '1.0.0-fixture.1'
PUBLIC_SOURCE = 'https://api.nuget.org/v3/index.json'
RUNTIME_PACKAGES = ('Orbyss.Foundation.Collections.Core', 'Orbyss.Foundation.Json.AspNetCore',
                    'Orbyss.Foundation.Web.OpenApi')
FEATURES = sorted((FEATURE, 'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi'))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError('PKT801 official Foundation tools: ' + message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def metadata(package: Path) -> tuple[str, str]:
    with zipfile.ZipFile(package) as archive:
        nuspecs = [item for item in archive.infolist() if item.filename.endswith('.nuspec')]
        require(len(nuspecs) == 1 and nuspecs[0].file_size <= 1024 * 1024, 'Package requires one bounded nuspec.')
        value = ET.fromstring(archive.read(nuspecs[0]))
    return value.find('./{*}metadata/{*}id').text, value.find('./{*}metadata/{*}version').text


def selection(mode: str | None, version: str | None, packages: Path | None) -> None:
    require(mode in ('private', 'public'), 'Select --runtime-source private or public explicitly.')
    require(version is not None and re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?', version) is not None,
            'Select one exact --runtime-version; there is no runtime default.')
    require((mode == 'private' and packages is not None) or (mode == 'public' and packages is None),
            'Private runtime needs --packages; public runtime cannot accept a private feed.')
    if packages is not None:
        require(packages.is_dir(), 'The explicit private runtime feed is unreadable.')
        for identity in RUNTIME_PACKAGES:
            found = [path for path in packages.glob('*.nupkg') if metadata(path) == (identity, version)]
            require(len(found) == 1, 'The exact private runtime package is missing or ambiguous: ' + identity)


def public_config(path: Path) -> None:
    value = ET.Element('configuration')
    sources = ET.SubElement(value, 'packageSources')
    ET.SubElement(sources, 'clear')
    ET.SubElement(sources, 'add', key='nuget.org', value=PUBLIC_SOURCE, protocolVersion='3')
    mapping = ET.SubElement(value, 'packageSourceMapping')
    ET.SubElement(mapping, 'clear')
    ET.SubElement(ET.SubElement(mapping, 'packageSource', key='nuget.org'), 'package', pattern='*')
    ET.indent(value)
    ET.ElementTree(value).write(path, encoding='utf-8', xml_declaration=True)


def runtime_config(original: Path, destination: Path, runtime_feed: Path | None, fixture_feed: Path) -> None:
    supplied = ET.parse(original).getroot()
    sources = supplied.find('packageSources')
    require(sources is not None, 'Explicit runtime dependency configuration must declare sources.')
    selected = {node.get('key'): node.get('value') for node in sources.findall('add')}
    require(selected.get('nuget.org') == PUBLIC_SOURCE, 'The official public tooling source must remain nuget.org.')
    # Rebuild just sources/mapping; registry credentials are never copied to evidence.
    value = ET.Element('configuration')
    target_sources = ET.SubElement(value, 'packageSources')
    ET.SubElement(target_sources, 'clear')
    for key, source in selected.items():
        require(source and source.startswith('https://'), 'External dependency sources must be explicit HTTPS registries.')
        ET.SubElement(target_sources, 'add', key=key, value=source)
    mapping = ET.SubElement(value, 'packageSourceMapping')
    ET.SubElement(mapping, 'clear')
    for key in selected:
        node = ET.SubElement(mapping, 'packageSource', key=key)
        old = supplied.find("packageSourceMapping/packageSource[@key='" + key + "']")
        patterns = {item.get('pattern') for item in old.findall('package')} if old is not None else set()
        if key == 'nuget.org':
            patterns.update(('*', BUILD))
        for pattern in sorted(patterns):
            ET.SubElement(node, 'package', pattern=pattern)
    for key, feed, patterns in (
        ('runtime-candidate', runtime_feed, ('Orbyss.Foundation.*',)),
        ('owned-fixture', fixture_feed, ('PublishedTools.Contract.*',))):
        if feed is None:
            continue
        ET.SubElement(target_sources, 'add', key=key, value=str(feed))
        node = ET.SubElement(mapping, 'packageSource', key=key)
        for pattern in patterns:
            ET.SubElement(node, 'package', pattern=pattern)
    ET.indent(value)
    ET.ElementTree(value).write(destination, encoding='utf-8', xml_declaration=True)


def run(command: list[str], cwd: Path, log: Path, environment: dict, expected: int = 0) -> str:
    result = subprocess.run(command, cwd=cwd, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf-8', errors='replace', timeout=300)
    log.write_text(json.dumps(command) + '\n' + result.stdout, encoding='utf-8')
    require(result.returncode == expected, f'Expected exit {expected}, got {result.returncode}; preserved log: {log}')
    return result.stdout


def public_binary(cache: Path, identity: str, version: str, official_archives: Path) -> dict:
    packages = list(cache.rglob(identity.lower() + '.' + version + '.nupkg'))
    require(packages and len({sha256(path) for path in packages}) == 1, 'Official package bytes are missing or ambiguous: ' + identity)
    package = packages[0]
    require(metadata(package) == (identity, version), 'Official package identity/version differs.')
    provenance = json.loads((package.parent / '.nupkg.metadata').read_text(encoding='utf-8'))
    require(provenance.get('source') in (None, PUBLIC_SOURCE), 'Tool bytes originated from a different registry.')
    # Local-tool restore metadata omits its source in SDK202. Independently bind
    # the restored bytes to the official immutable flat-container archive instead
    # of inferring publication from its filename or a local version string.
    official_archives.mkdir(exist_ok=True)
    filename = identity.lower() + '.' + version + '.nupkg'
    archive_url = 'https://api.nuget.org/v3-flatcontainer/' + identity.lower() + '/' + version + '/' + filename
    downloaded = official_archives / filename
    with urllib.request.urlopen(archive_url, timeout=60) as response, downloaded.open('wb') as destination:
        length = 0
        while chunk := response.read(1024 * 1024):
            length += len(chunk)
            require(length <= 64 * 1024 * 1024, 'Official tooling archive exceeded the finite download limit.')
            destination.write(chunk)
    require(sha256(downloaded) == sha256(package), 'Restored tool bytes differ from the official public immutable archive.')
    return {'id': identity, 'version': version, 'sha256': sha256(package), 'source': PUBLIC_SOURCE,
            'archiveUrl': archive_url, 'nativeProvenanceSha256': sha256(package.parent / '.nupkg.metadata')}


def source_descriptor(source: Path) -> dict:
    directory = source / 'Api'
    descriptor = json.loads((directory / 'feature.json').read_text(encoding='utf-8'))
    descriptor['sourceSha256'] = {path.relative_to(directory).as_posix(): hashlib.sha256(
        path.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode()).hexdigest()
        for path in sorted(directory.glob('*.cs'))}
    write(directory / 'feature.json', descriptor)
    return descriptor


def verify_document(document: dict, evidence: dict, directory: Path, closure: Path) -> None:
    require(evidence.get('producer') == {'kind': TOOL, 'version': TOOL_VERSION}, 'Export producer differs from the official restored tool.')
    require(evidence.get('rawDocument', {}).get('sha256') == sha256(directory / 'document.json'), 'Export document hash differs.')
    require(evidence.get('composedFeatures') == FEATURES and evidence.get('contractFeatures') == FEATURES,
            'Export did not compose the exact feature closure.')
    require({row['file']: row['sha256'] for row in evidence.get('packages', [])}
            == {path.name: sha256(path) for path in closure.glob('*.nupkg')}, 'Exporter package evidence omitted or changed staged inputs.')
    for key, name in (('shellsSha256', 'shells.json'), ('hostsettingsSha256', 'hostsettings.json'), ('contractSha256', 'contract.json')):
        require(evidence.get('inputs', {}).get(key) == sha256(directory / name), 'Exporter configuration/contract evidence differs.')
    side_effects = evidence.get('sideEffects', {})
    require(all(side_effects.get(key) is False for key in ('listenerStarted', 'consumerHostedServicesStarted', 'shellInitializersRun')),
            'Metadata export started application execution.')
    operation = document.get('paths', {}).get('/probe/sample', {}).get('post', {})
    contracts = operation.get('x-foundation-json-contracts', [])
    require(len(contracts) == 2, 'Actual official export omitted typed JSON metadata.')
    require({(value['direction'], value['profile'], value['preset'], value['maximumBytes']) for value in contracts}
            == {('request', 'strict-request', 'strict-request', 4096),
                ('response', 'success-response', 'tolerant-response', 8192)}, 'Exported JSON contracts drifted.')
    require('requestBody' in operation and '200' in operation.get('responses', {}), 'Typed wire contract metadata is missing.')
    schemas = document.get('components', {}).get('schemas', {})
    def resolve(value: dict) -> dict:
        seen = set()
        while '$ref' in value:
            reference = value['$ref']
            require(reference.startswith('#/components/schemas/') and reference not in seen,
                    'Array schema reference is external or cyclic.')
            seen.add(reference)
            value = schemas[reference.rsplit('/', 1)[-1]]
        return value
    require(any(resolve(value.get('properties', {}).get('values', {})).get('type') == 'array' for value in schemas.values()),
            'ValueSequence wire schema was exported as an object instead of an array.')


def self_test() -> None:
    for mode, version, packages in ((None, '0.3.0', None), ('public', None, None), ('public', '0.3.*', None),
                                    ('public', '0.3.0', ROOT), ('private', '0.3.0', None)):
        try:
            selection(mode, version, packages)
        except ValueError:
            pass
        else:
            raise AssertionError('An ambiguous runtime selection was accepted.')
    selection('public', '0.3.0', None)
    require('<Project />' in (FIXTURE / 'Directory.Build.targets').read_text(), 'Fixture inherited production build targets.')
    require(not any('foundation-contracts-source' in path.read_text(encoding='utf-8') for path in FIXTURE.rglob('*.csproj')),
            'Fixture references Foundation source instead of public packages.')
    print('Official tools preparation guards passed; no runtime compatibility or public availability is claimed.')


def qualify(args) -> Path:
    selection(args.runtime_source, args.runtime_version, args.packages)
    require(args.nuget_config and args.nuget_config.is_file(), 'An explicit dependency NuGet configuration is required.')
    if Path(args.dotnet).is_file():
        args.dotnet = str(Path(args.dotnet).resolve())
    work = ROOT / 'artifacts/foundation-published-tools' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8])
    work.mkdir(parents=True)
    print('Official published tools compatibility evidence: ' + str(work), flush=True)
    source = work / 'source'
    shutil.copytree(FIXTURE, source, ignore=shutil.ignore_patterns('obj', 'bin', '__pycache__'))
    write(source / 'global.json', {'sdk': {'version': '10.0.202', 'rollForward': 'disable', 'allowPrerelease': False}})
    selected_descriptor = source_descriptor(source)
    closure = work / 'closure'
    closure.mkdir()
    candidate = work / 'candidate-feed' if args.runtime_source == 'private' else None
    if candidate is not None:
        shutil.copytree(args.packages, candidate)
    runtime_config(args.nuget_config, source / 'NuGet.config', candidate, closure)
    tool_directory = work / 'official-exporter'
    tool_directory.mkdir()
    public_config(tool_directory / 'NuGet.config')
    write(tool_directory / '.config/dotnet-tools.json', {'version': 1, 'isRoot': True, 'tools': {TOOL.lower(): {
        'version': TOOL_VERSION, 'commands': [COMMAND]}}})
    environment = dict(os.environ, NUGET_PACKAGES=str(work / 'runtime-cache'), DOTNET_CLI_HOME=str(work / 'dotnet-home'),
                       DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0')
    if Path(args.dotnet).is_file():
        environment['DOTNET_ROOT'] = str(Path(args.dotnet).parent)
        environment['PATH'] = str(Path(args.dotnet).parent) + os.pathsep + environment.get('PATH', '')
    sdk = run([args.dotnet, '--version'], source, work / 'sdk.log', environment).strip()
    require(sdk == '10.0.202', 'This recipe requires the exact pinned SDK202, not substituted evidence.')
    properties = ['-p:FoundationRuntimeVersion=' + args.runtime_version]
    solution = source / 'PublishedTools.slnx'
    restore = [args.dotnet, 'restore', str(solution), '--configfile', str(source / 'NuGet.config'), '--no-http-cache', *properties]
    run([*restore, '--force-evaluate'], source, work / 'restore.log', environment)
    run([*restore, '--locked-mode'], source, work / 'locked-restore.log', environment)
    run([args.dotnet, 'build', str(solution), '-c', 'Release', '--no-restore', *properties], source, work / 'build.log', environment)
    build_binary = public_binary(work / 'runtime-cache', BUILD, BUILD_VERSION, work / 'official-archives')
    for project in ('Core/PublishedTools.Contract.Core.csproj', 'Api/PublishedTools.Contract.Api.csproj'):
        run([args.dotnet, 'pack', str(source / project), '-c', 'Release', '--no-build', '--no-restore', '--output', str(closure), *properties],
            source, work / (Path(project).parent.name + '-pack.log'), environment)
    core_package = closure / ('PublishedTools.Contract.Core.' + FIXTURE_VERSION + '.nupkg')
    api_package = closure / ('PublishedTools.Contract.Api.' + FIXTURE_VERSION + '.nupkg')
    with zipfile.ZipFile(core_package) as archive:
        require('orbyss-foundation/feature.json' not in archive.namelist(), 'Contract-only Core was advertised as an activated feature.')
    with zipfile.ZipFile(api_package) as archive:
        packed_descriptor = json.loads(archive.read('orbyss-foundation/feature.json'))
        require(packed_descriptor['schemaVersion'] == 2 and packed_descriptor['sourceSha256'] == selected_descriptor['sourceSha256']
                and packed_descriptor['features'] == selected_descriptor['features'], 'Official Build changed or omitted admitted source/feature metadata.')
        require(any(value['packageId'] == 'CShells.AspNetCore.Abstractions' for value in packed_descriptor['hostProvidedDependencies']),
                'Official Build omitted private native runtime metadata.')
        packed_assembly = {'file': 'lib/net10.0/PublishedTools.Contract.Api.dll',
                           'sha256': hashlib.sha256(archive.read('lib/net10.0/PublishedTools.Contract.Api.dll')).hexdigest()}
    # Observe actual published Build rejection of an unreviewed but compilable wire change.
    wire = source / 'Api/SampleRequest.cs'
    original = wire.read_text(encoding='utf-8')
    wire.write_text(original.replace('SampleRequest(string Text)', 'SampleRequest(string Text, int UnreviewedValue = 0)'), encoding='utf-8')
    output = run([args.dotnet, 'pack', str(source / 'Api/PublishedTools.Contract.Api.csproj'), '-c', 'Release', '--no-build', '--no-restore',
                  '--output', str(work / 'rejected-pack'), *properties], source, work / 'unreviewed-source-rejection.log', environment, expected=1)
    require('Publisher metadata source binding changed: SampleRequest.cs' in output, 'Official Build did not reject the changed wire contract specifically.')
    wire.write_text(original, encoding='utf-8')
    dependency_project = source / 'RuntimeClosure.csproj'
    dependency_project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally>'
        '<RestoreEnablePackagePruning>false</RestoreEnablePackagePruning></PropertyGroup><ItemGroup>'
        '<PackageReference Include="PublishedTools.Contract.Api" Version="[' + FIXTURE_VERSION + ']" />'
        '</ItemGroup></Project>', encoding='utf-8')
    dependency_restore = [args.dotnet, 'restore', str(dependency_project), '--configfile', str(source / 'NuGet.config'), '--no-http-cache', *properties]
    run(dependency_restore, source, work / 'runtime-closure-restore.log', environment)
    run([*dependency_restore, '--locked-mode'], source, work / 'runtime-closure-locked-restore.log', environment)
    assets = json.loads((source / 'obj/project.assets.json').read_text(encoding='utf-8'))
    package_roots = [Path(path) for path in assets['packageFolders']]
    retained = {path.name.casefold(): path for path in closure.glob('*.nupkg')}
    public_runtime_binaries = []
    for identity, library in assets['libraries'].items():
        require(library['type'] == 'package', 'Deployment closure bypasses packaged consumption through source references.')
        name, version = identity.rsplit('/', 1)
        relative = Path(library['path']) / (name.lower() + '.' + version.lower() + '.nupkg')
        package = next((root / relative for root in package_roots if (root / relative).is_file()), None)
        require(package is not None, 'A restored package archive is missing: ' + identity)
        destination = retained.get(package.name.casefold(), closure / package.name)
        if destination.exists():
            require(sha256(destination) == sha256(package), 'A staged package identity has conflicting bytes.')
        else:
            shutil.copy2(package, destination)
            retained[package.name.casefold()] = destination
        if args.runtime_source == 'public' and name.startswith('Orbyss.Foundation.') and name != BUILD:
            provenance = json.loads((package.parent / '.nupkg.metadata').read_text(encoding='utf-8'))
            require(provenance.get('source') == PUBLIC_SOURCE,
                    'Public runtime resolved from another registry instead of official nuget.org: ' + name)
            public_runtime_binaries.append(public_binary(work / 'runtime-cache', name, version, work / 'official-archives'))
    for identity in RUNTIME_PACKAGES:
        require(any(metadata(path) == (identity, args.runtime_version) for path in closure.glob('*.nupkg')),
                'Restored closure changed the selected runtime version.')
    tool_environment = {**environment, 'NUGET_PACKAGES': str(work / 'official-tool-cache')}
    run([args.dotnet, 'tool', 'restore', '--configfile', str(tool_directory / 'NuGet.config')], tool_directory,
        work / 'official-exporter-restore.log', tool_environment)
    exporter_binary = public_binary(work / 'official-tool-cache', TOOL, TOOL_VERSION, work / 'official-archives')
    write(tool_directory / 'shells.json', {'CShells': {'Shells': {'probe': {'Features': {value: True for value in FEATURES},
        'Configuration': {'WebRouting': {'Path': 'probe'}, 'Foundation': {'Json': {'Profiles': {
            'strict-request': {'Preset': 'strict-request', 'MaxBytes': 1024, 'MaxDepth': 32},
            'success-response': {'Preset': 'tolerant-response', 'MaxBytes': 2048, 'MaxDepth': 32,
                                 'Extensions': ['value-sequence-v1']}}}}}}}}})
    write(tool_directory / 'hostsettings.json', {})
    contract = {'schemaVersion': 1, 'identity': 'published-tools-contracts-v1', 'documentName': 'v1', 'shell': 'probe',
                'producer': {'kind': TOOL, 'version': TOOL_VERSION}, 'features': FEATURES}
    write(tool_directory / 'contract.json', contract)
    arguments = [args.dotnet, 'tool', 'run', COMMAND, '--', '--repository', str(tool_directory), '--packages', str(closure),
                 '--shells', str(tool_directory / 'shells.json'), '--hostsettings', str(tool_directory / 'hostsettings.json'),
                 '--contract', str(tool_directory / 'contract.json')]
    output = run([*arguments, '--output', str(tool_directory / 'document.json'), '--evidence', str(tool_directory / 'export.json')],
                 tool_directory, work / 'official-export.log', tool_environment)
    require('PUBLISHED_TOOL_STORAGE_CONSTRUCTED' not in output and 'PUBLISHED_TOOL_APPLICATION_INITIALIZER_RAN' not in output,
            'Cold export resolved application/storage execution.')
    verify_document(json.loads((tool_directory / 'document.json').read_text()), json.loads((tool_directory / 'export.json').read_text()),
                    tool_directory, closure)
    wrong_contract = {**contract, 'producer': {'kind': TOOL, 'version': '0.0.0-version-mismatch'}}
    write(tool_directory / 'mismatch.contract.json', wrong_contract)
    wrong_arguments = [*arguments[:-1], str(tool_directory / 'mismatch.contract.json')]
    rejected = (tool_directory / 'rejected.json', tool_directory / 'rejected.evidence.json')
    output = run([*wrong_arguments, '--output', str(rejected[0]), '--evidence', str(rejected[1])], tool_directory,
                 work / 'producer-version-rejection.log', tool_environment, expected=2)
    require('PKO200 contract requires exporter 0.0.0-version-mismatch, but this tool is 0.2.4.' in output
            and not any(path.exists() for path in rejected), 'Mismatched official tool producer wrote output or failed without its diagnostic.')
    availability = []
    if args.runtime_source == 'public':
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
        from public_availability import verify_nuget
        availability = [verify_nuget({'packageId': identity, 'version': args.runtime_version}) for identity in RUNTIME_PACKAGES]
    write(work / 'result.json', {'schemaVersion': 1, 'status': 'official-tools-compatible', 'runtimeSource': args.runtime_source,
        'runtimeVersion': args.runtime_version, 'runtimePublished': args.runtime_source == 'public',
        'profileQualified': False, 'defaultPromotionPerformed': False, 'settingsMetadataCompanionQualified': False,
        'scope': 'Official Build source/feature metadata emission and rejection; official exporter typed-contract cold composition and producer admission.',
        'officialTools': [build_binary, exporter_binary], 'publicRuntimeAvailability': availability,
        'publicRuntimeBinaries': public_runtime_binaries,
        'packedApiAssembly': packed_assembly, 'stagedPackages': {path.name: sha256(path) for path in sorted(closure.glob('*.nupkg'))},
        'fixture': {path.relative_to(FIXTURE).as_posix(): sha256(path) for path in sorted(FIXTURE.rglob('*'))
                    if path.is_file() and not {'bin', 'obj'} & set(path.parts)},
        'recipeSha256': sha256(Path(__file__)), 'sdk': sdk,
        'checks': {'officialBuild': True, 'unreviewedSourceRejected': True, 'contractCoreNotActivated': True,
                   'typedJsonMetadataExported': True, 'valueSequenceArraySchema': True, 'coldComposition': True,
                   'producerMismatchRejected': True}, 'paidWorkersStarted': False})
    print('Official Build0.1.0/exporter0.2.4 compatible with selected ' + args.runtime_source + ' runtime ' + args.runtime_version + ': ' + str(work))
    return work


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--runtime-source', choices=('private', 'public'))
    parser.add_argument('--runtime-version')
    parser.add_argument('--packages', type=Path)
    parser.add_argument('--nuget-config', type=Path)
    parser.add_argument('--dotnet', default='dotnet')
    args = parser.parse_args()
    self_test()
    if not args.self_test:
        qualify(args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
