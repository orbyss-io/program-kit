"""Qualify the actual installed typed operation through emitted native tooling."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tarfile
import urllib.request
import uuid
import time

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'
sys.path[:0] = [str(ENG), str(ROOT / 'extensions/program-kit-governance/scripts')]
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture
import oasdiff_cli


def export_client(directory):
    """Cold actual label metadata/client proof; no Host staging or runtime/provider substitute."""
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
    from dependency_profile import resolver
    import typed_operation
    from validate_numeric_schema import generate_typescript
    blocks = resolver(); catalog = blocks.new_project_catalog()
    template = ENG.parent
    shutil.copyfile(template / 'global.json', directory / 'global.json')
    shutil.copyfile(template / '.editorconfig', directory / '.editorconfig')
    (directory / 'NuGet.config').write_text('<configuration><packageSources><clear/>'
        '<add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
    (directory / 'Directory.Build.props').write_text('<Project><PropertyGroup>'
        '<TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable>'
        '<GenerateDocumentationFile>true</GenerateDocumentationFile><TreatWarningsAsErrors>true</TreatWarningsAsErrors>'
        '<FoundationSourceReadability>true</FoundationSourceReadability><NuGetAudit>false</NuGetAudit>'
        '<RestorePackagesWithLockFile>true</RestorePackagesWithLockFile></PropertyGroup><ItemGroup>'
        '<PackageReference Include="Orbyss.Foundation.Analyzers" Version="0.3.7" PrivateAssets="all"/>'
        '</ItemGroup></Project>')
    (directory / 'Directory.Build.targets').write_text('<Project/>')
    owners = {name: f'{name}/{name}.csproj' for name in ('core', 'runtime', 'api', 'provider', 'test')}
    owners.update(frontend='client', generatedTypes='client/types.ts')
    output = typed_operation.render(owners, ROOT / 'extensions')
    for path, content in output.items():
        if path.startswith(('core/', 'api/')):
            target = directory / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
    api = directory / 'api'; core = directory / 'core'
    shutil.copyfile(ROOT / 'tests/fixtures/typed-operation-contract/LabelFeature.cs', api / 'LabelFeature.cs')
    inputs = {p.relative_to(api).as_posix(): hashlib.sha256(p.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode()).hexdigest()
              for p in api.rglob('*.cs')}
    core_inputs = {p.relative_to(core).as_posix(): hashlib.sha256(p.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode()).hexdigest()
                   for p in core.rglob('*.cs')}
    identity = 'Label.Contract.Api'; version = '1.0.0-fixture.1'
    features = ['Label.Contract', 'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi']
    descriptor = {'schemaVersion': 2, 'packageId': identity, 'features': [{
        'identity': features[0], 'featureDependencies': features[1:], 'runtimeDependencies': [],
        'routes': ['/api/sample-label'], 'dormant': False, 'composeForOpenApi': True,
        'requiresContractCoverage': True}], 'sourceSha256': inputs}
    (api / 'feature.json').write_text(json.dumps(descriptor))
    settings = json.loads((ROOT / 'extensions/program-kit-dotnet/references/examples/typed-operation/settings.source.template.json').read_bytes())
    settings['packageId'] = identity; settings['sourceSha256'] = inputs
    settings['contracts'][0]['appliesTo']['features'] = [features[0]]
    (api / 'settings.source.json').write_text(json.dumps(settings))
    packages = {name: catalog['packages']['nuget:' + name]['version'] for name in (
        'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails',
        'Orbyss.Foundation.Web.OpenApi', 'Orbyss.Foundation.Build')}
    packages.update(blocks.effective_dependency_context(ROOT)['sharedAbi']['pins'])
    references = ''.join('<PackageReference Include="' + name + '" Version="' + pin + '"'
        + (' PrivateAssets="all"' if name.startswith('CShells.') or name.endswith('.Build') else '') + '/>'
        for name, pin in packages.items())
    (core / 'core.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        '<PackageId>Label.Contract.Core</PackageId><AssemblyName>Label.Contract.Core</AssemblyName><Version>' + version + '</Version></PropertyGroup></Project>')
    (api / 'api.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        '<PackageId>' + identity + '</PackageId><AssemblyName>' + identity + '</AssemblyName><Version>' + version + '</Version>'
        '<FoundationFeatureDescriptorSource>feature.json</FoundationFeatureDescriptorSource>'
        '<FoundationSettingsMetadataSource>settings.source.json</FoundationSettingsMetadataSource>'
        '</PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App"/>'
        '<ProjectReference Include="../core/core.csproj"/>' + references + '</ItemGroup></Project>')
    commands = []

    def run(label, arguments, cwd=directory):
        observed = foundation_fixture.captured(list(map(str, arguments)), cwd, directory / label, timeout=180)
        commands.append({'name': label, 'command': list(map(str, arguments)), 'cwd': str(cwd), **observed})
        (directory / 'cold-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if observed['exitCode'] or not observed['cleanupComplete'] or not observed['logsDrained']:
            raise ValueError('Actual cold label contract failed: ' + str(directory / label))

    closure = directory / 'closure'; closure.mkdir()
    for owner in ('core', 'api'):
        project = directory / owners[owner]
        run(owner + '-restore', ['dotnet', 'restore', project, '--use-lock-file', '--force-evaluate'])
        run(owner + '-locked', ['dotnet', 'restore', project, '--locked-mode'])
        run(owner + '-pack', ['dotnet', 'pack', project, '--configuration', 'Release', '--no-restore', '-o', closure, '-m:1'])
    assets = json.loads((api / 'obj/project.assets.json').read_bytes())
    for key, library in assets['libraries'].items():
        if library['type'] != 'package': continue
        name, pin = key.rsplit('/', 1)
        archive = Path(library['path']) / (name.lower() + '.' + pin.lower() + '.nupkg')
        path = next(Path(folder) / archive for folder in assets['packageFolders'] if (Path(folder) / archive).is_file())
        if not (closure / path.name).exists(): shutil.copyfile(path, closure / path.name)
    tool = directory / 'official-exporter'; (tool / '.config').mkdir(parents=True)
    shutil.copyfile(directory / 'NuGet.config', tool / 'NuGet.config')
    exporter = catalog['packages']['nuget:Orbyss.Foundation.OpenApi.Exporter']['version']
    (tool / '.config/dotnet-tools.json').write_text(json.dumps({'version': 1, 'isRoot': True, 'tools': {
        'orbyss.foundation.openapi.exporter': {'version': exporter, 'commands': ['orbyss-foundation-openapi-export']}}}))
    run('official-restore', ['dotnet', 'tool', 'restore', '--configfile', 'NuGet.config'], tool)
    (tool / 'shells.json').write_text(json.dumps({'CShells': {'Shells': {'probe': {'Features': {f: True for f in features},
        'Configuration': {'WebRouting': {'Path': ''}, 'Sample': {'Api': {'Prefix': 'configured-'}},
            'Foundation': {'Json': {'Profiles': {
                'sample-label-request': {'Preset': 'strict-request', 'MaxBytes': 1024},
                'sample-label-response': {'Preset': 'tolerant-response', 'MaxBytes': 2048}}}}}}}}}))
    (tool / 'hostsettings.json').write_text('{}')
    (tool / 'contract.json').write_text(json.dumps({'schemaVersion': 1, 'identity': 'label-contract', 'documentName': 'v1',
        'shell': 'probe', 'features': features, 'producer': {'kind': 'Orbyss.Foundation.OpenApi.Exporter', 'version': exporter}}))
    document = tool / 'document.json'
    run('official-export', ['dotnet', 'tool', 'run', 'orbyss-foundation-openapi-export', '--',
        '--repository', tool, '--packages', closure, '--shells', tool / 'shells.json',
        '--hostsettings', tool / 'hostsettings.json', '--contract', tool / 'contract.json',
        '--output', document, '--evidence', tool / 'export.json'], tool)
    actual = json.loads(document.read_bytes()); proof = json.loads((tool / 'export.json').read_bytes())
    assert actual['paths']['/api/sample-label']['get']['operationId'] == 'ReadSampleLabel'
    assert actual['paths']['/api/sample-label']['post']['operationId'] == 'WriteSampleLabel'
    assert set(proof['composedFeatures']) == set(features)
    assert all(proof['sideEffects'][key] is False for key in ('listenerStarted', 'consumerHostedServicesStarted', 'shellInitializersRun'))
    client = generate_typescript(directory, document, adapter=output['client/src/client.ts'])
    return {'status': 'passed', 'scope': 'Actual moved Core/API through selected native producer/exporter and real generated label types + compiled emitted client; thin fictional native wrapper only.',
        'actualStableLabelOperations': True, 'actualGeneratedTypesAndClient': True, 'commands': commands,
        'sourceSha256': inputs, 'coreSourceSha256': core_inputs,
        'documentSha256': hashlib.sha256(document.read_bytes()).hexdigest(), 'client': client, 'exporter': exporter,
        'runtimeExercised': False, 'providerExercised': False, 'httpExercised': False,
        'hostStagingExercised': False, 'fullRuntimeGap': 'Separate mixed-root/framework-pruning staging PKR014 remains unresolved.'}


def official_oasdiff(directory, version):
    """Explicit CI project-tool preparation, never a device runtime installation."""
    system = {'Windows': 'windows', 'Linux': 'linux'}.get(platform.system())
    architecture = {'AMD64': 'amd64', 'x86_64': 'amd64', 'aarch64': 'arm64', 'ARM64': 'arm64'}.get(platform.machine())
    if system is None or architecture is None: raise ValueError('Pinned comparison tool needs a qualified Windows/Linux architecture')
    name = 'oasdiff_' + version + '_' + system + '_' + architecture + '.tar.gz'
    url = 'https://api.github.com/repos/oasdiff/oasdiff/releases/tags/v' + version
    headers = {'User-Agent': 'Program-Kit-deterministic-project-tool'}
    if os.environ.get('GITHUB_TOKEN'): headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        raw = response.read(4 * 1_048_576 + 1)
    if len(raw) > 4 * 1_048_576: raise ValueError('Official comparison release metadata exceeds its bound')
    release = json.loads(raw)
    if release['tag_name'] != 'v' + version or release.get('draft') or release.get('prerelease'):
        raise ValueError('Comparison release does not match its exact stable pin')
    (directory / 'official-release.json').write_bytes(raw)
    for identity in ('checksums.txt', name):
        matches = [a for a in release['assets'] if a['name'] == identity]
        if len(matches) != 1: raise ValueError('Exact official comparison asset is missing or ambiguous')
        asset = matches[0]
        expected_prefix = 'https://github.com/oasdiff/oasdiff/releases/download/v' + version + '/'
        if not asset['browser_download_url'].startswith(expected_prefix): raise ValueError('Comparison asset has an unexpected release origin')
        with urllib.request.urlopen(asset['browser_download_url'], timeout=60) as response, (directory / identity).open('xb') as output:
            total = 0; digest = hashlib.sha256()
            while chunk := response.read(1_048_576):
                total += len(chunk)
                if total > 64 * 1_048_576: raise ValueError('Official comparison asset exceeds its bound')
                digest.update(chunk); output.write(chunk)
        if asset.get('digest') != 'sha256:' + digest.hexdigest(): raise ValueError('Official comparison asset digest differs')
    archive = directory / name
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest + '  ' + name not in (directory / 'checksums.txt').read_text(encoding='utf-8'):
        raise ValueError('Official comparison release checksum differs')
    binary = 'oasdiff.exe' if system == 'windows' else 'oasdiff'
    target = directory / binary
    with tarfile.open(archive, 'r:gz') as payload:
        matches = [m for m in payload.getmembers() if m.isfile() and m.name == binary]
        if len(matches) != 1 or matches[0].size > 64 * 1_048_576: raise ValueError('Official binary member is missing, ambiguous or oversized')
        with payload.extractfile(matches[0]) as stream: target.write_bytes(stream.read())
    if system != 'windows': target.chmod(0o755)
    oasdiff_cli.require(target, ROOT, version)
    (directory / 'verified-tool.json').write_text(json.dumps({'version': version, 'release': release['html_url'],
        'releaseId': release['id'], 'archiveSha256': digest, 'binarySha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'deviceInstallationPerformed': False}, indent=2) + '\n', encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engines', default='chromium,firefox,webkit')
    parser.add_argument('--oasdiff', type=Path, help='Existing reviewed exact project analysis binary')
    parser.add_argument('--prepare-oasdiff', action='store_true', help='Explicit official exact pinned project-tool preparation')
    parser.add_argument('--prepare-only', action='store_true', help='Tool preparation only; establishes no application execution')
    parser.add_argument('--export-client-only', action='store_true', help='Cold actual moved label producer/generated-client contract only; no Host/provider/browser acceptance')
    args = parser.parse_args()
    if args.export_client_only and (args.prepare_only or args.oasdiff or args.prepare_oasdiff):
        parser.error('--export-client-only excludes comparison/tool preparation modes')
    if not args.export_client_only and bool(args.oasdiff) == args.prepare_oasdiff: parser.error('Select one existing --oasdiff or explicit --prepare-oasdiff')
    directory = ROOT / 'artifacts/tests/typed-operation' / uuid.uuid4().hex[:8]; directory.mkdir(parents=True)
    result = {'schemaVersion': 1, 'status': 'running', 'scope': __doc__, 'productAcceptanceEstablished': False}
    if args.export_client_only:
        result.update(scope='Cold actual label metadata/generated-client contract only; no full Host/provider/browser qualification.',
                      runtimeExercised=False, providerExercised=False, httpExercised=False, hostStagingExercised=False)
    started = time.monotonic()
    try:
        if args.export_client_only:
            result.update(export_client(directory)); return
        version = (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/.oasdiff-version').read_text().strip()
        binary = official_oasdiff(directory, version) if args.prepare_oasdiff else args.oasdiff.resolve(strict=True)
        oasdiff_cli.require(binary, ROOT, version)
        result['comparisonTool'] = {'version': version, 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
        if args.prepare_only:
            result.update(status='prepared', operationExecuted=False); return
        arguments = [sys.executable, str(ROOT / 'tests/validate_composition_start.py'), '--execute', '--single-host',
            '--tooling', '--oasdiff', str(binary), '--engines', args.engines]
        observed = foundation_fixture.captured(arguments, ROOT, directory / 'execution', timeout=1800)
        if observed['exitCode'] or not observed['cleanupComplete'] or not observed['logsDrained']:
            raise ValueError('Actual installed typed flow failed; inspect ' + str(directory))
        output = (directory / 'execution/stdout.log').read_text(encoding='utf-8')
        actual = json.loads(output.strip().splitlines()[-1])
        required = ('runtimeExercised', 'toolingExercised', 'actualTypedRequestResponse', 'actualGeneratedTypesAndClient',
            'actualProviderPortResolution', 'actualNondefaultScalarOptions', 'independentDurableWriteObservation',
            'actualHostRestartRetainsEffect', 'actualPackedSettingsMetadata', 'actualNativeGeneratedControls')
        if actual.get('status') != 'passed' or any(actual.get(key) is not True for key in required):
            raise ValueError('Actual required typed-operation obligations missing or unsuccessful')
        consumer = (ROOT / actual['consumer']).resolve()
        if not consumer.is_relative_to(ROOT / 'artifacts/t'): raise ValueError('Typed flow returned an unowned consumer')
        resolved = json.loads((consumer / 'eng/foundation-composition.resolved.json').read_bytes())
        result.update(status='passed', actual=actual, selectedPackages=resolved['packages'], hostImage=resolved['hostImage'])
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error)); raise
    finally:
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        label = 'Cold actual label contract proof' if args.export_client_only else 'Actual installed typed-operation proof'
        print(label + ': ' + str(directory / 'results.json'))


if __name__ == '__main__': main()
