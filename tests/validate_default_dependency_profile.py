"""Qualify public dependency metadata and exporter admission with generic consumers.

This check owns the integration boundary, not component acceptance. Every registered
activation is admitted with its publisher-declared dependency closure. Publisher
features marked composeForOpenApi=false are checked as metadata, not executed.
The existing runtime and browser validators retain their separate acceptance gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import uuid
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import building_blocks as blocks
import profile_catalogs
import release_bundle

PROBE = 'ProgramKitQualificationProbe'
TOOL = 'Orbyss.Foundation.OpenApi.Exporter'
BUILD = 'Orbyss.Foundation.Build'
PUBLIC_SOURCE = 'https://api.nuget.org/v3/index.json'
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def retarget_engineering_packages(path: Path, selected: dict, named: bool) -> str:
    """Select exact disposable engineering pins without changing shipped templates."""
    tree = ET.parse(path)
    build_version = None
    for identity in ('Orbyss.Foundation.Analyzers', BUILD):
        declarations = [node for node in tree.iter('PackageVersion') if node.get('Include') == identity]
        if len(declarations) != 1:
            raise ValueError('Engineering tooling pin is missing or ambiguous: ' + identity)
        version = selected['artifacts'].get('nuget:' + identity)
        if version is None and (identity != BUILD or named):
            raise ValueError('Named qualification requires an exact registered tooling pin: ' + identity)
        if version is not None:
            declarations[0].set('Version', version)
        if identity == BUILD:
            build_version = declarations[0].get('Version')
    ET.indent(tree)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return build_version


def public_tool_configuration(path: Path) -> None:
    """Restore the exporter from one explicit public source in an owned cache."""
    configuration = ET.Element('configuration')
    sources = ET.SubElement(configuration, 'packageSources')
    ET.SubElement(sources, 'clear')
    ET.SubElement(sources, 'add', key='nuget.org', value=PUBLIC_SOURCE, protocolVersion='3')
    mapping = ET.SubElement(configuration, 'packageSourceMapping')
    ET.SubElement(mapping, 'clear')
    ET.SubElement(ET.SubElement(mapping, 'packageSource', key='nuget.org'), 'package', pattern='*')
    ET.indent(configuration)
    ET.ElementTree(configuration).write(path, encoding='utf-8', xml_declaration=True)


def require_resolved_tool(assets: Path, cache: Path, identity: str, version: str) -> None:
    """Observe the actual native restore graph before allowing Build to execute."""
    value = blocks.load_json(assets)
    libraries = [(key, item) for key, item in value.get('libraries', {}).items()
                 if key.rsplit('/', 1)[0].casefold() == identity.casefold()]
    if (len(libraries) != 1 or libraries[0][0].casefold() != (identity + '/' + version).casefold()
            or libraries[0][1].get('type') != 'package'
            or {Path(path).resolve() for path in value.get('packageFolders', {})} != {cache.resolve()}):
        raise ValueError('Actual resolved tooling version or owned package cache differs: ' + identity)


def official_tool_binary(cache: Path, identity: str, version: str, official: Path) -> dict:
    """Bind restored tooling bytes to the public immutable archive, including SDK source omission."""
    packages = list(cache.rglob(identity.lower() + '.' + version.lower() + '.nupkg'))
    if not packages or len({blocks.raw_sha256(path) for path in packages}) != 1:
        raise ValueError('Official tooling archive is missing or ambiguous: ' + identity)
    package = packages[0]
    with zipfile.ZipFile(package) as archive:
        specs = [item for item in archive.infolist() if item.filename.endswith('.nuspec')]
        if len(specs) != 1 or specs[0].file_size > 1_048_576:
            raise ValueError('Official tooling requires one bounded package identity: ' + identity)
        metadata = ET.fromstring(archive.read(specs[0]))
        fields = {node.tag.rsplit('}', 1)[-1]: node.text for node in metadata.iter()}
        if (fields.get('id'), fields.get('version')) != (identity, version):
            raise ValueError('Official tooling identity/version differs: ' + identity)
    native_path = package.parent / '.nupkg.metadata'
    if not native_path.is_file() or native_path.stat().st_size > 1_048_576:
        raise ValueError('Official tooling native provenance is missing or exceeds its bound: ' + identity)
    native = blocks.load_json(native_path)
    if native.get('source') not in (None, PUBLIC_SOURCE):
        raise ValueError('Official tooling resolved from a different source: ' + identity)
    official.mkdir(parents=True, exist_ok=True)
    filename = identity.lower() + '.' + version.lower() + '.nupkg'
    archive_url = 'https://api.nuget.org/v3-flatcontainer/' + identity.lower() + '/' + version.lower() + '/' + filename
    downloaded = official / filename
    with urllib.request.urlopen(archive_url, timeout=60) as response, downloaded.open('wb') as destination:
        size = 0
        while chunk := response.read(1_048_576):
            size += len(chunk)
            if size > 67_108_864:
                raise ValueError('Official tooling archive exceeds 64 MiB download limit: ' + identity)
            destination.write(chunk)
    digest = blocks.raw_sha256(package)
    if digest != blocks.raw_sha256(downloaded):
        raise ValueError('Restored tooling bytes differ from the official immutable public archive: ' + identity)
    return {'id': identity, 'version': version, 'sha256': digest, 'source': PUBLIC_SOURCE,
            'nativeSource': native.get('source'), 'archiveUrl': archive_url,
            'nativeProvenanceSha256': blocks.raw_sha256(native_path)}


def selected_runtime_packages(catalog: dict, named: bool) -> dict:
    """Named qualification restores inert Core/provider packages as well as feature adapters."""
    return {key: package for key, package in catalog['packages'].items()
            if package['ecosystem'] == 'nuget' and package['packageId'] != BUILD
            and (package.get('activations') or named and package['materialization']['kind'] == 'nuget-project')}


def require_selected_runtime_closure(selected: dict, artifacts: dict, closure: Path) -> None:
    """Do not qualify a named full profile if its new inert contracts/provider archives were omitted."""
    for package in selected.values():
        identity, version = package['packageId'], package['version']
        binding = artifacts.get(identity, {})
        filename = (identity + '.' + version + '.nupkg').casefold()
        archives = [path for path in closure.glob('*.nupkg') if path.name.casefold() == filename]
        if (len(archives) != 1 or binding.get('version') != version
                or binding.get('sha256') != blocks.raw_sha256(archives[0])):
            raise ValueError('Named runtime closure is missing or differs from selected package: ' + identity)


def generate_native_probe(selected: dict, catalog: dict, work: Path, named: bool) -> tuple[Path, dict, str]:
    """Share byte-identical native inputs between ordinary lock preparation and qualification."""
    # Use the maintained engineering imports and public private-build package.
    for relative in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props',
                     'global.json', 'NuGet.config', 'eng/ProgramKit.Build.props',
                     'eng/ProgramKit.Build.targets', 'eng/ProgramKit.Packages.props'):
        destination = work / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATE / relative, destination)
    central = work / 'Directory.Packages.props'
    runtime = selected_runtime_packages(catalog, named)
    versions = '\n'.join(f'<PackageVersion Include="{escape(p["packageId"])}" Version="{escape(p["version"])}" />'
                         for p in runtime.values())
    central.write_text(central.read_text().replace('</Project>', '<ItemGroup>\n' + versions +
        '\n<PackageVersion Include="Microsoft.AspNetCore.OpenApi" Version="10.0.11" />\n</ItemGroup></Project>'), encoding='utf-8')
    packages = work / 'eng/ProgramKit.Packages.props'
    build_version = retarget_engineering_packages(packages, selected, named)
    feature = work / 'Feature/ProgramKit.Qualification.csproj'
    feature.parent.mkdir()
    references = '\n'.join(f'<PackageReference Include="{escape(p["packageId"])}" PrivateAssets="all" />' for p in runtime.values())
    feature.write_text(f'''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>
<IsPackable>true</IsPackable><Version>1.0.0</Version><PackageId>ProgramKit.Qualification</PackageId>
<AssemblyName>ProgramKit.Qualification</AssemblyName><FoundationFeatureIdentity>{PROBE}</FoundationFeatureIdentity>
<FoundationFeatureRoutes>/probe</FoundationFeatureRoutes>
</PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App" />
<PackageReference Include="CShells.Abstractions" PrivateAssets="all" />
<PackageReference Include="CShells.AspNetCore.Abstractions" PrivateAssets="all" />
<PackageReference Include="Microsoft.AspNetCore.OpenApi" />
{references}</ItemGroup></Project>''', encoding='utf-8')
    (feature.parent / 'Probe.cs').write_text(f'''using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
namespace ProgramKit.Qualification;
/// <summary>Generic exporter integration probe.</summary>
[ShellFeature("{PROBE}")]
public sealed class Probe : IWebShellFeature {{
    /// <summary>Register the document provider.</summary>
    public void ConfigureServices(IServiceCollection services) => services.AddOpenApi("v1");
    /// <summary>Register a consumer endpoint.</summary>
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapGet("/probe", () => "qualified");
}}
''', encoding='utf-8')
    return feature, runtime, build_version


def prepare_lock(profile_path: Path, catalog_path: Path, output: Path, work: Path) -> dict:
    """Observe one fresh ordinary restore; this cannot qualify, seal or select a profile."""
    output, work = output.resolve(), work.resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError('New native lock must stay inside the qualification repository') from error
    if (output.exists() or output.is_symlink() or output.suffix != '.json'
            or output.is_relative_to((ROOT / 'tests/fixtures').resolve()) or output.is_relative_to(work)):
        raise ValueError('Native lock preparation requires a new JSON output outside historical fixtures and its work directory')
    selected = blocks.load_json(profile_path)
    catalog = blocks.materialize_dependency_profile(blocks.load_json(catalog_path), selected)
    inputs = {'profileSha256': blocks.raw_sha256(profile_path), 'catalogSha256': blocks.raw_sha256(catalog_path)}
    work.mkdir(parents=True)
    print('Native lock preparation evidence: ' + str(work), flush=True)
    feature, runtime, build_version = generate_native_probe(selected, catalog, work, True)
    probe_inputs = {path.relative_to(work).as_posix(): blocks.raw_sha256(path)
                    for path in sorted(work.rglob('*')) if path.is_file()}
    environment = dict(os.environ, NUGET_PACKAGES=str(work / 'cache'), DOTNET_CLI_HOME=str(work / 'dotnet-home'),
                       DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0')
    command = ['dotnet', 'restore', str(feature), '--force-evaluate', '--no-http-cache']
    observed = subprocess.run(command, cwd=work, env=environment, capture_output=True,
                              encoding='utf-8', errors='replace', timeout=300)
    log = work / 'ordinary-restore.log'
    log.write_text(observed.stdout + observed.stderr, encoding='utf-8', newline='\n')
    if observed.returncode != 0:
        raise ValueError('Ordinary native lock preparation restore failed; preserved log: ' + str(log))
    lock_path = feature.parent / 'packages.lock.json'
    lock = blocks.load_json(lock_path)
    resolved = {}
    for framework in lock.get('dependencies', {}).values():
        for identity, package in framework.items():
            if package.get('type') in {'Direct', 'Transitive'}:
                resolved.setdefault(identity.casefold(), set()).add(package.get('resolved'))
    required = {package['packageId']: package['version'] for package in runtime.values()}
    required.update({BUILD: build_version, 'Orbyss.Foundation.Analyzers': selected['artifacts']['nuget:Orbyss.Foundation.Analyzers']})
    if any(resolved.get(identity.casefold()) != {version} for identity, version in required.items()):
        raise ValueError('Observed ordinary native lock omitted or changed an exact selected runtime/engineering pin')
    if inputs != {'profileSha256': blocks.raw_sha256(profile_path), 'catalogSha256': blocks.raw_sha256(catalog_path)}:
        raise ValueError('Explicit profile/catalog inputs changed during native lock preparation')
    content = lock_path.read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as destination:
        destination.write(content)
    result = {'schemaVersion': 1, 'status': 'prepared-native-lock', 'qualificationPerformed': False,
              'publicAvailabilityEstablished': False, 'profile': {'id': selected['id'], 'path': str(profile_path.resolve()),
                                                               'sha256': inputs['profileSha256']},
              'catalog': {'path': str(catalog_path.resolve()), 'sha256': inputs['catalogSha256']},
              'nativeLock': {'path': str(output), 'sha256': blocks.raw_sha256(output)},
              'executorSha256': profile_catalogs.source_sha256(Path(__file__)), 'probeInputs': probe_inputs,
              'runtimePackages': required, 'restore': {'command': command, 'exitCode': observed.returncode,
                                                     'evidenceSha256': blocks.raw_sha256(log)}}
    write(work / 'preparation.json', result)
    return result


def qualify(profile_path: Path, work: Path, *, catalog_path: Path | None = None,
            native_lock: Path | None = None, qualification_recipe: Path | None = None) -> dict:
    selected = blocks.load_json(profile_path)
    explicit = any(value is not None for value in (catalog_path, native_lock, qualification_recipe))
    if explicit:
        inputs = profile_catalogs.qualification_inputs(profile_path, catalog_path, native_lock,
                                                       qualification_recipe, Path(__file__), ROOT)
        catalog = inputs['catalog']
        native_lock = inputs['nativeLock']
    else:
        catalog = blocks.materialize_dependency_profile(blocks.load_json(blocks.default_catalog(Path(blocks.__file__))), selected)
        native_lock = ROOT / 'tests/fixtures/default-dependency-profile/packages.lock.json'
    work.mkdir(parents=True)
    print('Generic dependency qualification evidence: ' + str(work), flush=True)
    environment = dict(os.environ, NUGET_PACKAGES=str(work / 'cache'), DOTNET_CLI_HOME=str(work / 'dotnet-home'),
                       DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',
                       MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0')
    steps = []

    def run(identity, arguments, cwd=work, expected=0, env=None):
        result = subprocess.run(arguments, cwd=cwd, env=environment if env is None else env, capture_output=True,
                                encoding='utf-8', errors='replace', timeout=300)
        log = work / (identity + '.log')
        log.write_text(result.stdout + result.stderr, encoding='utf-8', newline='\n')
        if result.returncode != expected:
            raise ValueError(f'{identity}: expected {expected}, got {result.returncode}; {log}\n{result.stdout}{result.stderr}')
        return {'id': identity, 'exitCode': result.returncode, 'evidenceSha256': blocks.raw_sha256(log)}

    feature, runtime, build_version = generate_native_probe(selected, catalog, work, explicit)
    shutil.copyfile(native_lock, feature.parent / 'packages.lock.json')
    steps.append(run('locked-restore', ['dotnet', 'restore', str(feature), '--locked-mode']))
    official_tools = {}
    if explicit:
        require_resolved_tool(feature.parent / 'obj/project.assets.json', work / 'cache', BUILD, build_version)
        official_tools[BUILD] = official_tool_binary(work / 'cache', BUILD, build_version, work / 'official-archives')
    closure = work / 'closure'
    steps.append(run('consumer-build-pack', ['dotnet', 'pack', str(feature), '--no-restore', '-c', 'Release', '-o', str(closure)]))
    descriptors, artifacts = {}, {}
    lock = blocks.load_json(feature.parent / 'packages.lock.json')
    for dependencies in lock['dependencies'].values():
        for identity, package in dependencies.items():
            if package.get('type') not in {'Direct', 'Transitive'}:
                continue
            version = package['resolved']
            source = work / 'cache' / identity.lower() / version / f'{identity.lower()}.{version}.nupkg'
            if not source.is_file():
                raise ValueError('Resolved native package is missing: ' + identity)
            if not release_bundle.is_runtime_package(source):
                continue
            destination = closure / source.name
            shutil.copyfile(source, destination)
            artifacts[identity] = {'version': version, 'sha256': blocks.raw_sha256(source)}
            for descriptor in release_bundle.package_features(source):
                if descriptor['identity'] in descriptors:
                    raise ValueError('Ambiguous publisher feature: ' + descriptor['identity'])
                descriptors[descriptor['identity']] = descriptor
    if explicit:
        require_selected_runtime_closure(runtime, artifacts, closure)
    probe = closure / 'ProgramKit.Qualification.1.0.0.nupkg'
    with zipfile.ZipFile(probe) as archive:
        assert 'program-kit/feature.json' not in archive.namelist()
        descriptors[PROBE] = json.loads(archive.read('orbyss-foundation/feature.json'))
    allowed = sorted({activation['featureIdentity'] for package in catalog['packages'].values()
                      for activation in package.get('activations', [])})
    if not set(allowed) <= set(descriptors):
        raise ValueError('Publisher descriptors missing: ' + ', '.join(sorted(set(allowed) - set(descriptors))))
    metadata = work / 'publisher-metadata.json'
    write(metadata, {'artifacts': artifacts, 'descriptors': descriptors})
    steps.append({'id': 'publisher-descriptors', 'exitCode': 0, 'evidenceSha256': blocks.raw_sha256(metadata)})
    tooling_directory = work / 'official-exporter' if explicit else work
    tooling = tooling_directory / '.config/dotnet-tools.json'
    write(tooling, {'version': 1, 'isRoot': True, 'tools': {TOOL.lower(): {
        'version': selected['artifacts']['nuget:' + TOOL], 'commands': ['orbyss-foundation-openapi-export']}}})
    tool_environment = {**environment, 'NUGET_PACKAGES': str(work / 'tool-cache')} if explicit else environment
    tool_configuration = tooling_directory / 'NuGet.config'
    if explicit:
        public_tool_configuration(tool_configuration)
    steps.append(run('public-exporter-restore', ['dotnet', 'tool', 'restore', '--configfile', str(tool_configuration)],
                     cwd=tooling_directory, env=tool_environment))
    if explicit:
        official_tools[TOOL] = official_tool_binary(work / 'tool-cache', TOOL, selected['artifacts']['nuget:' + TOOL],
                                                   work / 'official-archives')
        write(work / 'official-tools.json', official_tools)
        for identity, binding in official_tools.items():
            artifacts[identity] = {'version': binding['version'], 'sha256': binding['sha256']}
    write(work / 'hostsettings.json', {})
    web = ['Orbyss.Foundation.WebDefaults', 'Orbyss.Foundation.Web.OpenApi', 'Orbyss.Foundation.Web.ProblemDetails']
    scenarios = {
        'minimal-web': web,
        'spa-assurance': web + ['Orbyss.Foundation.Authentication.SpaPkce', 'Orbyss.Foundation.Authentication.Assurance'],
        'bff-assurance': web + ['Orbyss.Foundation.Authentication.BffCookie', 'Orbyss.Foundation.Authentication.Assurance'],
        'forms-localization': web + ['Orbyss.Forms.JsonForms', 'Orbyss.Forms.Localization',
            'Orbyss.Forms.Web.Runtime', 'Orbyss.Forms.Web.Management', 'Orbyss.Forms.Web.Submissions',
            'Orbyss.Forms.Storage.InMemory', 'Orbyss.Localization.Web.Runtime',
            'Orbyss.Localization.Web.Management', 'Orbyss.Localization.Storage.InMemory']}
    exports, compositions = [], []
    cases = [('activation', identity, [identity]) for identity in allowed]
    cases += [('composition', identity, values) for identity, values in sorted(scenarios.items())]
    for number, (kind, identity, initial) in enumerate(cases):
        active = set(initial) | {PROBE}
        pending = list(active)
        while pending:
            for dependency in descriptors[pending.pop()]['featureDependencies']:
                if dependency not in descriptors:
                    raise ValueError('Undescribed publisher dependency: ' + dependency)
                if dependency not in active:
                    active.add(dependency)
                    pending.append(dependency)
        write(work / 'shells.json', {'CShells': {'Shells': {'probe': {
            'Features': {value: True for value in sorted(active)}, 'Configuration': {'WebRouting': {'Path': 'test'}}}}}})
        contract = {'schemaVersion': 1, 'identity': 'generic-profile-probe', 'documentName': 'v1', 'shell': 'probe',
                    'producer': {'kind': TOOL, 'version': selected['artifacts']['nuget:' + TOOL]}, 'features': sorted(active)}
        write(work / 'contract.json', contract)
        arguments = ['dotnet', 'tool', 'run', 'orbyss-foundation-openapi-export', '--', '--repository', str(work),
                     '--packages', str(closure), '--shells', str(work / 'shells.json'), '--hostsettings', str(work / 'hostsettings.json'),
                     '--contract', str(work / 'contract.json'), '--output', str(work / 'document.json'), '--evidence', str(work / 'export.json')]
        run('activation-' + str(number), arguments, cwd=tooling_directory, env=tool_environment)
        document = blocks.load_json(work / 'document.json')
        assert '/test/probe' in document['paths']
        evidence = blocks.load_json(work / 'export.json')
        assert evidence['producer'] == contract['producer']
        assert evidence['rawDocument']['sha256'] == blocks.raw_sha256(work / 'document.json')
        row = {kind: identity, 'closure': sorted(active), 'evidenceSha256': blocks.raw_sha256(work / 'export.json')}
        (exports if kind == 'activation' else compositions).append(row)
    write(work / 'activation-matrix.json', {'activations': exports, 'compositions': compositions})
    steps.append({'id': 'activation-export-matrix', 'exitCode': 0, 'evidenceSha256': blocks.raw_sha256(work / 'activation-matrix.json')})
    contract['producer']['version'] = '0.0.0-version-mismatch'
    write(work / 'contract.json', contract)
    (work / 'document.json').unlink()
    (work / 'export.json').unlink()
    rejected = run('producer-version-rejection', arguments, cwd=tooling_directory, expected=2, env=tool_environment)
    assert 'PKO200' in (work / 'producer-version-rejection.log').read_text()
    assert not (work / 'document.json').exists() and not (work / 'export.json').exists()
    rejected['exitCode'] = 0  # The check succeeded by observing the required rejection.
    rejected['observedExitCode'] = 2
    steps.append(rejected)
    result = {'schemaVersion': 2, 'status': 'generic-integration-passed',
              'catalog': {'sha256': selected['catalogResolutionSha256']},
              'source': {'kind': 'generic-publisher-integration',
                         'recipeSha256': hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
                         'lockSha256': hashlib.sha256(native_lock.read_bytes().replace(b'\r\n', b'\n')).hexdigest()},
              'scope': {'claim': 'publisher-metadata-and-exporter-admission', 'allowedActivations': allowed},
              'steps': steps, 'artifacts': artifacts, 'activationMatrix': exports, 'compositionMatrix': compositions}
    if explicit:
        result['source']['qualificationRecipeSha256'] = inputs['qualificationRecipeSha256']
        result['source']['officialTools'] = official_tools
        result['source']['officialToolsSha256'] = blocks.raw_sha256(work / 'official-tools.json')
    write(work / 'qualification.json', result)
    print(f'Public profile {selected["id"]}: {len(allowed)} activation closures and {len(compositions)} representative combinations exported; wrong producer rejected.', flush=True)
    return result


def default_qualification_inputs() -> tuple[Path, Path | None, Path | None, Path | None]:
    """Keep legacy defaults; dispatch named inputs only after complete public qualification."""
    directory = blocks.profile_registry()
    index = blocks.load_json(directory / 'index.json')
    identity = index['default']
    entry = index['profiles'][identity]
    profile = blocks.repository_path(directory, entry['path'])
    if 'catalogSnapshot' not in entry and 'qualificationRecipe' not in entry:
        return profile, None, None, None
    if 'catalogSnapshot' not in entry or 'qualificationRecipe' not in entry:
        blocks.fail('PKB611', 'named default qualification requires both catalog snapshot and recipe bindings')
    # This includes immutable availability, browser, activation and exact published Host evidence.
    # A draft/unqualified entry must never turn an implicit default run into candidate admission.
    blocks.qualified_dependency_profile(directory, identity, blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
    recipe_path = blocks.repository_path(directory, entry['qualificationRecipe']['path'])
    recipe = blocks.load_json(recipe_path)
    catalog = blocks.repository_path(ROOT, blocks.normalize_path(recipe['catalogSnapshot']['path'], 'default recipe catalog'))
    native_lock = blocks.repository_path(ROOT, blocks.normalize_path(recipe['nativeLock']['path'], 'default recipe lock'))
    profile_catalogs.qualification_inputs(profile, catalog, native_lock, recipe_path, Path(__file__), ROOT)
    return profile, catalog, native_lock, recipe_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, help='Exact candidate profile; otherwise validate the registered default.')
    parser.add_argument('--catalog', type=Path, help='Explicit target catalog for paired named qualification or ordinary lock preparation.')
    parser.add_argument('--native-lock', type=Path)
    parser.add_argument('--qualification-recipe', type=Path)
    parser.add_argument('--prepare-lock', type=Path, help='Prepare a new observed lock from explicit profile/catalog; never performs qualification.')
    args = parser.parse_args()
    if args.prepare_lock is not None:
        if args.profile is None or args.catalog is None or args.native_lock is not None or args.qualification_recipe is not None:
            parser.error('Lock preparation requires explicit profile and catalog, without a native lock or qualification recipe')
        result = prepare_lock(args.profile.resolve(), args.catalog.resolve(), args.prepare_lock,
                              ROOT / 'artifacts/native-lock-preparation' / uuid.uuid4().hex[:8])
        print(json.dumps(result, indent=2))
        return 0
    if any(value is not None for value in (args.catalog, args.native_lock, args.qualification_recipe)) and not all(
            value is not None for value in (args.profile, args.catalog, args.native_lock, args.qualification_recipe)):
        parser.error('Named qualification requires all explicit profile, catalog, native lock and recipe inputs')
    if args.profile is None:
        args.profile, args.catalog, args.native_lock, args.qualification_recipe = default_qualification_inputs()
    qualify(args.profile.resolve(), ROOT / 'artifacts/default-profile-qualification' / uuid.uuid4().hex[:8],
            catalog_path=args.catalog, native_lock=args.native_lock, qualification_recipe=args.qualification_recipe)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
