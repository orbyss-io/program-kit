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
import uuid
import zipfile
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import building_blocks as blocks
import release_bundle

PROBE = 'ProgramKitQualificationProbe'
TOOL = 'Orbyss.Foundation.OpenApi.Exporter'
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def qualify(profile_path: Path, work: Path) -> dict:
    selected = blocks.load_json(profile_path)
    catalog = blocks.materialize_dependency_profile(blocks.load_json(blocks.default_catalog(Path(blocks.__file__))), selected)
    work.mkdir(parents=True)
    print('Generic dependency qualification evidence: ' + str(work), flush=True)
    environment = dict(os.environ, NUGET_PACKAGES=str(work / 'cache'),
                       MSBUILDDISABLENODEREUSE='1', DOTNET_CLI_USE_MSBUILD_SERVER='0')
    steps = []

    def run(identity, arguments, cwd=work, expected=0):
        result = subprocess.run(arguments, cwd=cwd, env=environment, capture_output=True,
                                encoding='utf-8', errors='replace', timeout=300)
        log = work / (identity + '.log')
        log.write_text(result.stdout + result.stderr, encoding='utf-8', newline='\n')
        if result.returncode != expected:
            raise ValueError(f'{identity}: expected {expected}, got {result.returncode}; {log}\n{result.stdout}{result.stderr}')
        return {'id': identity, 'exitCode': result.returncode, 'evidenceSha256': blocks.raw_sha256(log)}

    # Use the maintained engineering imports and public private-build package.
    for relative in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props',
                     'global.json', 'NuGet.config', 'eng/ProgramKit.Build.props',
                     'eng/ProgramKit.Build.targets', 'eng/ProgramKit.Packages.props'):
        destination = work / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATE / relative, destination)
    central = work / 'Directory.Packages.props'
    runtime = {key: package for key, package in catalog['packages'].items()
               if package['ecosystem'] == 'nuget' and package.get('activations')}
    versions = '\n'.join(f'<PackageVersion Include="{escape(p["packageId"])}" Version="{escape(p["version"])}" />'
                         for p in runtime.values())
    central.write_text(central.read_text().replace('</Project>', '<ItemGroup>\n' + versions +
        '\n<PackageVersion Include="Microsoft.AspNetCore.OpenApi" Version="10.0.11" />\n</ItemGroup></Project>'), encoding='utf-8')
    packages = work / 'eng/ProgramKit.Packages.props'
    packages.write_text(packages.read_text().replace('Include="Orbyss.Foundation.Analyzers" Version="0.2.2"',
        f'Include="Orbyss.Foundation.Analyzers" Version="{selected["artifacts"]["nuget:Orbyss.Foundation.Analyzers"]}"'), encoding='utf-8')
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
    native_lock = ROOT / 'tests/fixtures/default-dependency-profile/packages.lock.json'
    shutil.copyfile(native_lock, feature.parent / 'packages.lock.json')
    steps.append(run('locked-restore', ['dotnet', 'restore', str(feature), '--locked-mode']))
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
    tooling = work / '.config/dotnet-tools.json'
    write(tooling, {'version': 1, 'isRoot': True, 'tools': {TOOL.lower(): {
        'version': selected['artifacts']['nuget:' + TOOL], 'commands': ['orbyss-foundation-openapi-export']}}})
    steps.append(run('public-exporter-restore', ['dotnet', 'tool', 'restore', '--configfile', str(work / 'NuGet.config')]))
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
        run('activation-' + str(number), arguments)
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
    rejected = run('producer-version-rejection', arguments, expected=2)
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
    write(work / 'qualification.json', result)
    print(f'Public profile {selected["id"]}: {len(allowed)} activation closures and {len(compositions)} representative combinations exported; wrong producer rejected.', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, help='Exact candidate profile; otherwise validate the registered default.')
    args = parser.parse_args()
    if args.profile is None:
        directory = blocks.profile_registry()
        index = blocks.load_json(directory / 'index.json')
        args.profile = blocks.repository_path(directory, index['profiles'][index['default']]['path'])
    qualify(args.profile.resolve(), ROOT / 'artifacts/default-profile-qualification' / uuid.uuid4().hex[:8])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
