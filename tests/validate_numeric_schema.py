"""Investigate truthful numeric schemas without changing parser or compatibility authority."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import hashlib
import time
import argparse

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


def run(evidence, name, command, cwd=None, expected=0, environment=None):
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd or evidence, env=environment, capture_output=True, text=True, timeout=300)
    (evidence / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode != expected: raise AssertionError('Numeric parity probe failed: ' + str(evidence / (name + '.log')))
    return {'command': command, 'seconds': round(time.perf_counter() - started, 3)}


def official_export(evidence, catalog, blocks):
    source = evidence / 'api'; source.mkdir()
    fixtures = [path for path in (ROOT / 'tests/fixtures/composition-numeric').glob('*.cs') if path.name != 'Program.cs']
    for fixture in fixtures:
        shutil.copyfile(fixture, source / fixture.name)
    descriptor = {'schemaVersion': 2, 'packageId': 'Numeric.Contract.Api', 'features': [{
        'identity': 'Numeric.Contract', 'featureDependencies': ['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi', 'Numeric.EffectOnly'],
        'runtimeDependencies': [], 'routes': ['/numeric'], 'dormant': False, 'composeForOpenApi': True, 'requiresContractCoverage': True}, {
        'identity': 'Numeric.NullableContract', 'featureDependencies': ['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi', 'Numeric.EffectOnly'],
        'runtimeDependencies': [], 'routes': ['/nullable-numeric'], 'dormant': False, 'composeForOpenApi': True, 'requiresContractCoverage': True}, {
        'identity': 'Numeric.IntentionallyMalformed', 'featureDependencies': ['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi', 'Numeric.EffectOnly'],
        'runtimeDependencies': [], 'routes': ['/intentionally-malformed-numeric'], 'dormant': False, 'composeForOpenApi': True, 'requiresContractCoverage': True}, {
        'identity': 'Numeric.EffectOnly', 'featureDependencies': [], 'runtimeDependencies': [], 'routes': [],
        'dormant': False, 'composeForOpenApi': False, 'requiresContractCoverage': False}],
        'sourceSha256': {fixture.name: hashlib.sha256(fixture.read_text().replace('\r\n', '\n').encode()).hexdigest() for fixture in fixtures}}
    (source / 'feature.json').write_text(json.dumps(descriptor))
    packages = {name: catalog['packages']['nuget:' + name]['version'] for name in (
        'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi', 'Orbyss.Foundation.Build')}
    packages.update(blocks.effective_dependency_context(ROOT)['sharedAbi']['pins'])
    references = ''.join('<PackageReference Include="' + name + '" Version="' + version + '"'
                         + (' PrivateAssets="all"' if name.startswith('CShells.') or name.endswith('.Build') else '') + ' />'
                         for name, version in packages.items())
    (source / 'Numeric.Contract.Api.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        '<TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable>'
        '<ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally><RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>'
        '<PackageId>Numeric.Contract.Api</PackageId><Version>1.0.0-fixture.2</Version>'
        '<FoundationFeatureDescriptorSource>feature.json</FoundationFeatureDescriptorSource></PropertyGroup>'
        '<ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App" />' + references + '</ItemGroup></Project>')
    closure = evidence / 'closure'; closure.mkdir()
    run(evidence, 'native-renew', ['dotnet', 'restore', 'Numeric.Contract.Api.csproj', '--use-lock-file', '--force-evaluate'], source)
    run(evidence, 'native-locked', ['dotnet', 'restore', 'Numeric.Contract.Api.csproj', '--locked-mode'], source)
    run(evidence, 'native-pack', ['dotnet', 'pack', 'Numeric.Contract.Api.csproj', '-c', 'Release', '--no-restore', '-o', str(closure)], source)
    assets = json.loads((source / 'obj/project.assets.json').read_text())
    for identity, library in assets['libraries'].items():
        if library['type'] != 'package': continue
        name, version = identity.rsplit('/', 1)
        archive = Path(library['path']) / (name.lower() + '.' + version.lower() + '.nupkg')
        path = next(Path(folder) / archive for folder in assets['packageFolders'] if (Path(folder) / archive).is_file())
        if not (closure / path.name).exists(): shutil.copyfile(path, closure / path.name)
    # Producer restores the exact selected official tool; no publisher sources or fake storage inputs.
    tool = evidence / 'official-exporter'; (tool / '.config').mkdir(parents=True)
    shutil.copyfile(evidence / 'NuGet.config', tool / 'NuGet.config')
    exporter_version = catalog['packages']['nuget:Orbyss.Foundation.OpenApi.Exporter']['version']
    (tool / '.config/dotnet-tools.json').write_text(json.dumps({'version': 1, 'isRoot': True, 'tools': {
        'orbyss.foundation.openapi.exporter': {'version': exporter_version, 'commands': ['orbyss-foundation-openapi-export']}}}))
    run(evidence, 'official-restore', ['dotnet', 'tool', 'restore', '--configfile', 'NuGet.config'], tool)
    features = ['Numeric.Contract', 'Numeric.EffectOnly', 'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.OpenApi']
    (tool / 'shells.json').write_text(json.dumps({'CShells': {'Shells': {'probe': {'Features': {f: True for f in features},
        'Configuration': {'WebRouting': {'Path': 'probe'}, 'Foundation': {'Json': {'Profiles': {
            'strict-request': {'Preset': 'strict-request', 'MaxBytes': 1024, 'MaxDepth': 32},
            'success-response': {'Preset': 'tolerant-response', 'MaxBytes': 2048, 'MaxDepth': 32}}}}}}}}}))
    (tool / 'hostsettings.json').write_text('{}')
    (tool / 'contract.json').write_text(json.dumps({'schemaVersion': 1, 'identity': 'numeric-parity-v2', 'documentName': 'v1',
        'shell': 'probe', 'features': features, 'producer': {'kind': 'Orbyss.Foundation.OpenApi.Exporter', 'version': exporter_version}}))
    timing = run(evidence, 'official-export', ['dotnet', 'tool', 'run', 'orbyss-foundation-openapi-export', '--',
        '--repository', str(tool), '--packages', str(closure), '--shells', str(tool / 'shells.json'),
        '--hostsettings', str(tool / 'hostsettings.json'), '--contract', str(tool / 'contract.json'),
        '--output', str(tool / 'document.json'), '--evidence', str(tool / 'export.json')], tool)
    document = json.loads((tool / 'document.json').read_text())
    proof = json.loads((tool / 'export.json').read_text())
    assert proof['producer']['version'] == exporter_version
    assert set(proof['composedFeatures']) == set(features) - {'Numeric.EffectOnly'}
    assert proof['contractFeatures'] == features
    assert 'NUMERIC_EFFECT_ONLY_CONFIGURE_SERVICES_RAN' not in (evidence / 'official-export.log').read_text()
    assert all(proof['sideEffects'][key] is False for key in ('listenerStarted', 'consumerHostedServicesStarted', 'shellInitializersRun'))
    sys.path.insert(0, str(TEMPLATE / 'scripts'))
    import openapi_capabilities
    admitted = openapi_capabilities.require(document, openapi_capabilities.selected(ROOT), 'producer')
    (evidence / 'capability-admission.json').write_text(json.dumps(admitted, indent=2))
    # Preserve exact old-profile behavior, while qualifying the published numeric
    # repair with the actual unmodified raw document rather than a consumer workaround.
    nullable_features = ['Numeric.NullableContract', *features[1:]]
    shell = json.loads((tool / 'shells.json').read_text())
    shell['CShells']['Shells']['probe']['Features'] = {f: True for f in nullable_features}
    (tool / 'nullable-shells.json').write_text(json.dumps(shell))
    config = json.loads((tool / 'contract.json').read_text()); config['features'] = nullable_features
    (tool / 'nullable-contract.json').write_text(json.dumps(config))
    run(evidence, 'nullable-official-export', ['dotnet', 'tool', 'run', 'orbyss-foundation-openapi-export', '--',
        '--repository', str(tool), '--packages', str(closure), '--shells', str(tool / 'nullable-shells.json'),
        '--hostsettings', str(tool / 'hostsettings.json'), '--contract', str(tool / 'nullable-contract.json'),
        '--output', str(tool / 'nullable-document.json'), '--evidence', str(tool / 'nullable-export.json')], tool)
    nullable_path = tool / 'nullable-document.json'
    nullable_bytes = nullable_path.read_bytes()
    nullable = verify_nullable_producer(json.loads(nullable_bytes), catalog, openapi_capabilities)
    (evidence / 'nullable-admission.json').write_text(json.dumps(nullable, indent=2))
    nullable_proof = json.loads((tool / 'nullable-export.json').read_text())
    assert nullable_proof['producer']['version'] == exporter_version
    assert set(nullable_proof['composedFeatures']) == set(nullable_features) - {'Numeric.EffectOnly'}
    assert all(nullable_proof['sideEffects'][key] is False for key in ('listenerStarted', 'consumerHostedServicesStarted', 'shellInitializersRun'))
    assert 'NUMERIC_EFFECT_ONLY_CONFIGURE_SERVICES_RAN' not in (evidence / 'nullable-official-export.log').read_text()

    # This separate native producer is intentionally wrong. Its transformer adds
    # the contradiction; never modify the genuine document to manufacture a negative.
    malformed_features = ['Numeric.IntentionallyMalformed', *features[1:]]
    shell['CShells']['Shells']['probe']['Features'] = {f: True for f in malformed_features}
    (tool / 'intentionally-malformed-shells.json').write_text(json.dumps(shell))
    config['features'] = malformed_features
    (tool / 'intentionally-malformed-contract.json').write_text(json.dumps(config))
    run(evidence, 'intentionally-malformed-official-export', ['dotnet', 'tool', 'run', 'orbyss-foundation-openapi-export', '--',
        '--repository', str(tool), '--packages', str(closure), '--shells', str(tool / 'intentionally-malformed-shells.json'),
        '--hostsettings', str(tool / 'hostsettings.json'), '--contract', str(tool / 'intentionally-malformed-contract.json'),
        '--output', str(tool / 'intentionally-malformed-document.json'), '--evidence', str(tool / 'intentionally-malformed-export.json')], tool)
    malformed = json.loads((tool / 'intentionally-malformed-document.json').read_text())
    assert nullable_numeric_types(malformed) == {'integer', 'null', 'string'}
    rejected = openapi_capabilities.validate(malformed, openapi_capabilities.selected(ROOT), 'producer')
    assert not rejected['admitted'] and rejected['findings']
    assert all('optionalCount' in finding and finding.startswith('PKO222 ') for finding in rejected['findings']), rejected['findings']
    (evidence / 'intentionally-malformed-rejected.json').write_text(json.dumps(rejected, indent=2))
    assert nullable_path.read_bytes() == nullable_bytes, 'The actual nullable producer document was changed by negative qualification'
    # Controlled negative metadata snapshot proves the trap is executable, while
    # preserving the admitted closure and exact descriptor bytes unchanged.
    negative_closure = evidence / 'effect-only-negative-closure'
    shutil.copytree(closure, negative_closure)
    positive_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in closure.glob('*.nupkg')}
    descriptor_path = source / 'feature.json'; original_descriptor = descriptor_path.read_bytes()
    descriptor['features'][-1]['composeForOpenApi'] = True
    try:
        descriptor_path.write_text(json.dumps(descriptor))
        run(evidence, 'effect-only-negative-pack', ['dotnet', 'pack', 'Numeric.Contract.Api.csproj', '-c', 'Release',
            '--no-build', '--no-restore', '-o', str(negative_closure)], source)
        run(evidence, 'effect-only-negative-export', ['dotnet', 'tool', 'run', 'orbyss-foundation-openapi-export', '--',
            '--repository', str(tool), '--packages', str(negative_closure), '--shells', str(tool / 'shells.json'),
            '--hostsettings', str(tool / 'hostsettings.json'), '--contract', str(tool / 'contract.json'),
            '--output', str(tool / 'effect-only-rejected-document.json'), '--evidence', str(tool / 'effect-only-rejected-export.json')], tool, expected=2)
        assert 'NUMERIC_EFFECT_ONLY_CONFIGURE_SERVICES_RAN' in (evidence / 'effect-only-negative-export.log').read_text()
        assert not (tool / 'effect-only-rejected-document.json').exists() and not (tool / 'effect-only-rejected-export.json').exists()
    finally:
        descriptor_path.write_bytes(original_descriptor)
    assert positive_hashes == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in closure.glob('*.nupkg')}
    (evidence / 'effect-only-proof.json').write_text(json.dumps({'effectOnlyFeature': 'Numeric.EffectOnly',
        'selectedInShellAndContract': True, 'declaredApiDependency': True, 'composeForOpenApi': False,
        'registrationExcludedByActualExporter': True, 'controlledTrueRegistrationRejected': True,
        'failureBeforeDocumentOrEvidence': True, 'connectionInputsSupplied': False,
        'positiveClosureUnchanged': positive_hashes}, indent=2))
    return tool / 'document.json', timing


def nullable_numeric_types(document):
    """Inspect the actual unique nullable DTO, independently from capability admission."""
    models = [value for value in document['components']['schemas'].values()
              if 'optionalCount' in value.get('properties', {})]
    assert len(models) == 1, 'Expected one actual nullable numeric schema owner'
    model = models[0]
    assert 'optionalCount' in model.get('required', []), 'Nullable constructor input lost requiredness'
    kinds = model['properties']['optionalCount']['type']
    return {kinds} if isinstance(kinds, str) else set(kinds)


def verify_nullable_producer(document, catalog, admission):
    """Require the exact selected release's genuine raw behavior; no document correction."""
    version = catalog['packages']['nuget:Orbyss.Foundation.Json.AspNetCore']['version']
    parts = version.split('.')
    assert len(parts) == 3 and all(part.isdigit() for part in parts), 'Qualify the selected non-stable numeric implementation explicitly'
    repaired = tuple(map(int, parts)) >= (0, 3, 8)
    kinds = nullable_numeric_types(document)
    result = admission.validate(document, admission.selected(ROOT), 'producer')
    if repaired:
        assert kinds == {'integer', 'null'}, 'Published numeric correction did not reach the actual raw nullable schema'
        assert result['admitted'], result['findings']
    else:
        assert kinds == {'integer', 'null', 'string'}, 'Historical selected producer behavior changed; investigate exact package provenance'
        assert not result['admitted'] and any('optionalCount' in finding and finding.startswith('PKO222 ') for finding in result['findings'])
    return {**result, 'foundationJsonAspNetCore': version,
            'disposition': 'published-numeric-repair-admitted' if repaired else 'historical-nullable-mismatch-blocked',
            'rawNumericKinds': sorted(kinds), 'consumerSchemaWorkaroundApplied': False}


def generate_typescript(evidence, document, *, adapter=None, nullable=False):
    document_name = 'nullable-document.json' if nullable else 'document.json'
    client_name = 'nullable-client' if nullable else 'client'
    compiler_name = 'nullable-compiler' if nullable else 'compiler'
    label_prefix = 'nullable-' if nullable else ''
    expected_document = evidence / 'official-exporter' / document_name
    if document.resolve() != expected_document.resolve():
        raise ValueError('Generate only from the exact retained official exporter document')
    generator = evidence / client_name; generator.mkdir(exist_ok=True)
    defaults = json.loads((TEMPLATE / 'scripts/openapi-defaults.json').read_text())['typescriptGenerator']
    typescript = json.loads((TEMPLATE.parent / 'web-profiles/common/tools/program-kit/web/package.json').read_text())['devDependencies']['typescript']
    (generator / 'package.json').write_text(json.dumps({'name': 'numeric-parity', 'version': '1.0.0', 'private': True,
        'scripts': {'generate': 'openapi-typescript ../official-exporter/' + document_name + ' -o types.ts'},
        'devDependencies': {defaults['package']: defaults['version']}}))
    if adapter is not None:
        (generator / 'src').mkdir()
        (generator / 'src/client.ts').write_bytes(adapter)
    # Use maintained exact shared-tool selection, cache and TLS admission.
    # This disposable fixture must not inherit CMD's overlong-PATH failure or
    # infer npm's installation layout from the discovered launcher.
    for name in ('global.json', '.nvmrc', '.npm-version'):
        shutil.copyfile(TEMPLATE / name, evidence / name)
    sys.path.insert(0, str(TEMPLATE / 'scripts'))
    from device_toolchain import require_python
    shared_python = require_python(evidence)
    environment = os.environ.copy()
    inherited_path_characters = len(environment.get('PATH', ''))
    if os.name == 'nt':
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
        from windows_workflow_path import prepare_path
        environment['PATH'] = prepare_path(environment.get('PATH', ''), str(shared_python))
    run(evidence, label_prefix + 'client-toolchain', [str(shared_python), str(TEMPLATE / 'scripts/toolchain.py'),
        '--repository', str(evidence)], environment=environment)
    from foundation_qualification import npm_command
    npm, environment = npm_command(evidence, [])
    if os.name == 'nt':
        environment['PATH'] = prepare_path(environment.get('PATH', ''), str(shared_python))
    for name, arguments in (
        ('client-lock', ['install', '--package-lock-only', '--ignore-scripts', '--strict-peer-deps', '--engine-strict']),
        ('client-ci', ['ci', '--ignore-scripts', '--strict-peer-deps', '--engine-strict']),
        ('client-generate', ['run', 'generate'])):
        run(evidence, label_prefix + name, [*npm, *arguments], generator, environment=environment)
    # Keep the consumer compiler isolated from generator peers, exactly as the
    # emitted pipeline does: openapi-typescript currently requires TypeScript5,
    # while supported application code uses its independently pinned compiler.
    compiler = evidence / compiler_name; compiler.mkdir(exist_ok=True)
    compiler_dependencies = {'typescript': typescript}
    if adapter is not None:
        application_package = json.loads((TEMPLATE.parent / 'hosted-pages/web/package.json').read_bytes())
        compiler_dependencies = application_package['devDependencies']
        typescript = compiler_dependencies['typescript']
    (compiler / 'package.json').write_text(json.dumps({'name': 'generated-client-compiler',
      'version': '1.0.0', 'private': True, 'devDependencies': compiler_dependencies}))
    compile_arguments = ['../' + client_name + '/types.ts']
    if adapter is not None:
        profile = json.loads((TEMPLATE.parent / 'hosted-pages/web/tsconfig.json').read_bytes())
        profile['include'] = ['../' + client_name + '/types.ts', '../' + client_name + '/src/client.ts']
        (compiler / 'tsconfig.json').write_text(json.dumps(profile))
        compile_arguments = ['--project', 'tsconfig.json']
    for name, arguments in (
        ('compiler-lock', ['install', '--package-lock-only', '--ignore-scripts', '--strict-peer-deps', '--engine-strict']),
        ('compiler-ci', ['ci', '--ignore-scripts', '--strict-peer-deps', '--engine-strict']),
        ('client-compile', ['exec', '--', 'tsc', '--noEmit', '--strict', '--skipLibCheck',
            *compile_arguments])):
        run(evidence, label_prefix + name, [*npm, *arguments], compiler, environment=environment)
    return {'generator': defaults, 'compiler': typescript, 'toolchainEvidence': str(evidence / 'artifacts/program-kit/toolchain.json'),
            'inheritedPathCharacters': inherited_path_characters,
            'npmPathCharacters': len(environment.get('PATH', '')),
            'lockSha256': hashlib.sha256((generator / 'package-lock.json').read_bytes()).hexdigest(),
            'typesSha256': hashlib.sha256((generator / 'types.ts').read_bytes()).hexdigest(),
            **({'compiledActualAdapterSha256': hashlib.sha256(adapter).hexdigest()} if adapter is not None else {})}


def generated_client(evidence, document):
    result = generate_typescript(evidence, document)
    generator = evidence / 'client'
    types = (generator / 'types.ts').read_text()
    for property in ('amount', 'count', 'revision'):
        import re
        lines = re.findall(r'\b' + property + r'\??: ([^;]+);', types)
        assert lines and all('number' in line and 'string' not in line for line in lines), (property, lines)
    assert 'amounts: number[]' in types
    nullable = json.loads((evidence / 'nullable-admission.json').read_text())
    if nullable['admitted']:
        nullable_document = evidence / 'official-exporter/nullable-document.json'
        nullable_bytes = nullable_document.read_bytes()
        nullable_client = generate_typescript(evidence, nullable_document, nullable=True)
        nullable_types = (evidence / 'nullable-client/types.ts').read_text()
        properties = re.findall(r'\boptionalCount(\??): ([^;]+);', nullable_types)
        assert properties and all(not optional and 'number' in value and 'null' in value and 'string' not in value
                                  for optional, value in properties), properties
        assert nullable_document.read_bytes() == nullable_bytes, 'Client generation changed the genuine raw nullable document'
        result['nullable'] = nullable_client
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-client', action='store_true',
        help='Only the real offline exporter, generated TypeScript and compiler; no runtime host, browser or database')
    args = parser.parse_args()
    evidence = ROOT / 'artifacts/tests/numeric-schema' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
    from dependency_profile import resolver
    blocks = resolver()
    catalog = blocks.new_project_catalog()
    if args.export_client:
        started = time.monotonic()
        shutil.copyfile(TEMPLATE / 'global.json', evidence / 'global.json')
        (evidence / 'NuGet.config').write_text('<configuration><packageSources><clear />'
            '<add key="nuget.org" value="https://api.nuget.org/v3/index.json" /></packageSources></configuration>')
        document, timing = official_export(evidence, catalog, blocks)
        client = generated_client(evidence, document)
        (evidence / 'result.json').write_text(json.dumps({'status': 'passed',
            'scope': 'Offline selected exporter and compiled generated TypeScript; no application runtime, database, browser or HTTP request claim.',
            'elapsedSeconds': round(time.monotonic() - started, 3),
            'officialExport': timing, 'generatedClient': client,
            'nullableProducer': json.loads((evidence / 'nullable-admission.json').read_text()),
            'intentionallyMalformedNumericRejected': True}, indent=2))
        print('Offline exporter/client passed: ' + str(evidence))
        return
    shared = blocks.effective_dependency_context(ROOT)['sharedAbi']['pins']
    version = catalog['packages']['nuget:Orbyss.Foundation.Json']['version']
    shutil.copyfile(TEMPLATE / 'global.json', evidence / 'global.json')
    shutil.copyfile(ROOT / 'tests/fixtures/composition-numeric/Program.cs', evidence / 'Program.cs')
    shutil.copyfile(ROOT / 'tests/fixtures/composition-numeric/NumericFeature.cs', evidence / 'NumericFeature.cs')
    (evidence / 'Probe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
        '<TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType><ImplicitUsings>enable</ImplicitUsings>'
        '<InterceptorsNamespaces>$(InterceptorsNamespaces);Microsoft.AspNetCore.OpenApi.Generated</InterceptorsNamespaces>'
        '<ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally><Nullable>enable</Nullable></PropertyGroup><ItemGroup>'
        '<PackageReference Include="Orbyss.Foundation.Json" Version="' + version + '" />'
        '<PackageReference Include="Orbyss.Foundation.Web.OpenApi" Version="' + catalog['packages']['nuget:Orbyss.Foundation.Web.OpenApi']['version'] + '" />'
        '<PackageReference Include="Orbyss.Foundation.Json.AspNetCore" Version="' + version + '" />'
        '<PackageReference Include="Orbyss.Foundation.Web.ProblemDetails" Version="' + version + '" />'
        '<PackageReference Include="CShells.Abstractions" Version="' + shared['CShells.Abstractions'] + '" />'
        '<PackageReference Include="CShells.AspNetCore.Abstractions" Version="' + shared['CShells.AspNetCore.Abstractions'] + '" /></ItemGroup></Project>')
    (evidence / 'NuGet.config').write_text('<configuration><packageSources><clear />'
        '<add key="nuget.org" value="https://api.nuget.org/v3/index.json" /></packageSources></configuration>')
    for name, command in [('renew', ['dotnet', 'restore', 'Probe.csproj', '--use-lock-file', '--force-evaluate']),
                          ('locked', ['dotnet', 'restore', 'Probe.csproj', '--locked-mode']),
                          ('run', ['dotnet', 'run', '--project', 'Probe.csproj', '--no-restore'])]:
        run(evidence, name, command)
    schemas = {key: json.loads((evidence / filename).read_text()) for key, filename in
               [('aspnet', 'aspnet-default.schema.json'), ('profile', 'foundation-profile.schema.json'), ('scoped', 'scoped-dto.schema.json')]}
    for field, numeric in [('amount', 'number'), ('count', 'integer')]:
        assert set(schemas['aspnet']['properties'][field]['type']) == {numeric, 'string'}
        assert schemas['profile']['properties'][field]['type'] == numeric
        assert schemas['scoped']['properties'][field]['type'] == numeric
    assert 'STRICT_NUMERIC_PROFILE_OK' in (evidence / 'run.log').read_text()
    produced = json.loads((evidence / 'producer.openapi.json').read_text())['components']['schemas']
    for field, numeric in [('amount', 'number'), ('count', 'integer')]:
        assert set(produced['NumericRequest']['properties'][field]['type']) == {numeric, 'string'}
        assert produced['StrictNumericRequest']['properties'][field]['type'] == numeric
    allowed = {'type', 'title', 'status', 'code', 'correlationId', 'traceId', 'fieldErrors', 'detail'}
    for filename in ['problem-' + str(s) + '.json' for s in (400, 401, 403, 500)] + ['application-problem.json']:
        problem = json.loads((evidence / filename).read_text())
        assert set(problem) <= allowed and allowed - {'detail'} <= set(problem)
        assert problem['correlationId'] == problem['traceId']
        assert 'retryMode' not in problem and 'statusPath' not in problem
    response = json.loads((evidence / 'numeric-response.json').read_text())
    assert isinstance(response['amount'], (int, float)) and isinstance(response['child']['revision'], int)
    document, timing = official_export(evidence, catalog, blocks)
    client = generated_client(evidence, document)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    (evidence / 'result.json').write_text(json.dumps({'status': 'passed', 'foundationJson': version,
        'aspnetDefaultMismatchReproduced': True, 'profileMetadataTruthful': True, 'numericStringsRejected': True,
        'actualOpenApiProducerVerified': True,
        'scopedDtoCandidateVerified': True, 'contractApproval': 'pending-consumer-review', 'sourceCommit': commit,
        'recipeSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'capabilityValidatorSha256': hashlib.sha256((TEMPLATE / 'scripts/openapi_capabilities.py').read_bytes()).hexdigest(),
        'selectedCapabilityProjectorSha256': hashlib.sha256((ROOT / 'extensions/program-kit-building-blocks/scripts/wire_capabilities.py').read_bytes()).hexdigest(),
        'sdk': subprocess.run(['dotnet', '--version'], cwd=evidence, capture_output=True, text=True, check=True).stdout.strip(),
        'cacheScope': 'Fresh disposable fixture and npm ci; user NuGet/tool/npm caches may be warm. Prepared metadata export timing excludes preparation, business operation execution and agent reasoning.',
        'sourceState': 'Working-tree candidate at recorded HEAD plus exact recipe/fixture/validator hashes; not a clean-commit publication receipt.',
        'fixtureSha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'tests/fixtures/composition-numeric').glob('*.cs')},
        'actualClosedProblemWriter': True, 'nestedArraysAndOverflow': True,
        'actualEffectOnlyRegistrationExcluded': True, 'controlledEffectOnlyTrueRejectedBeforeOutput': True,
        'nullableNumericDisposition': json.loads((evidence / 'nullable-admission.json').read_text()),
        'intentionallyMalformedNumericRejected': True,
        'officialExporter': catalog['packages']['nuget:Orbyss.Foundation.OpenApi.Exporter']['version'],
        'maintainedGeneratedClient': client, 'preparedMetadataExportTiming': timing,
        'scope': 'Scoped strict DTO defaults under selected unmodified pins, native typed bindings and selected parser/writer/producer/client parity. Custom converters/shared types under different profiles remain explicit unresolved. No consumer baseline or approval changed; fixture timings exclude agent reasoning.'}, indent=2))
    print('Scoped numeric parser/writer/official producer/client qualification and selected nullable disposition passed: ' + str(evidence))


if __name__ == '__main__':
    main()
