"""One fictional consumer: scaffold, prepare, run, then add consumer code.

This deterministic test never invokes a coding agent or a paid provider. The
execution option uses only its generated disposable consumer and local Docker.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-dotnet/scripts'
sys.path.insert(0, str(SCRIPTS))
from composition_fixture import two_apps, accept_fixture
from owned_fixture import native_path
import composition_migrate


def add_typed_operation(root):
    """Use the shipping example bytes in actual independent native projects."""
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
    import typed_operation
    owners = {'core': 'src/Planned.Core/Planned.Core.csproj', 'runtime': 'src/Application.Runtime/Application.Runtime.csproj',
              'api': 'src/Application.Api/Application.Api.csproj', 'provider': 'src/Application.PostgreSql/Application.PostgreSql.csproj',
              'test': 'tests/Application.Tests/Application.Tests.csproj', 'frontend': 'web/policy-web',
              'generatedTypes': 'tools/openapi/policies/generated/types.ts'}
    for destination, content in typed_operation.render(owners, ROOT / 'extensions').items():
        if destination.endswith('client.ts'):
            continue  # The actual native generator runs before client integration below.
        (root / destination).write_bytes(content)
    runtime = root / 'src/Application.Runtime/ApplicationRuntimeFeature.cs'
    text = runtime.read_text()
    seam = 'public void ConfigureServices(IServiceCollection services) { }'
    if text.count(seam) != 1:
        raise ValueError('Native runtime registration seam changed; preserve source for review')
    runtime.write_text('using ProgramKit.Examples.TypedOperation;\n' + text.replace(seam,
        'public void ConfigureServices(IServiceCollection services) { LabelServices.Configure(services); }'), encoding='utf-8')
    runtime_project = root / owners['runtime']
    runtime_project.write_text(runtime_project.read_text().replace('</Project>',
        '<ItemGroup><ProjectReference Include="../Planned.Core/Planned.Core.csproj" /></ItemGroup></Project>'), encoding='utf-8')
    provider = root / 'src/Application.PostgreSql/ProviderFeature.cs'
    provider.write_text('using ProgramKit.Examples.TypedOperation;\n' + provider.read_text().replace(
        'public void ConfigureServices(IServiceCollection services)\n    {',
        'public void ConfigureServices(IServiceCollection services)\n    {\n        services.AddScoped<ILabelStore, PostgreSqlLabelStore<PolicyDbContext>>();'), encoding='utf-8')
    project = root / 'src/Application.PostgreSql/Application.PostgreSql.csproj'
    project.write_text(project.read_text().replace('</Project>',
        '<ItemGroup><ProjectReference Include="../Planned.Core/Planned.Core.csproj" /></ItemGroup></Project>'), encoding='utf-8')
    project = root / 'src/Application.Api/Application.Api.csproj'
    text = project.read_text().replace('</Project>',
        '<ItemGroup><PackageReference Include="Orbyss.Foundation.Json.AspNetCore" /><PackageReference Include="Orbyss.Foundation.Web.ProblemDetails" /></ItemGroup></Project>')
    document = ET.fromstring(text); dependencies = document.find('PropertyGroup/FoundationFeatureDependencies')
    dependencies.text = dependencies.text + ';Orbyss.Foundation.Json.AspNetCore;Orbyss.Foundation.Web.ProblemDetails'
    project.write_bytes(ET.tostring(document) + b'\n')
    architecture = root / 'eng/architecture.json'; value = json.loads(architecture.read_bytes())
    for row in value['runtimeComposition']['projects']:
        if row['path'] == owners['runtime']:
            row['projectReferences'].append(owners['core'])
        if row['path'] == 'src/Application.PostgreSql/Application.PostgreSql.csproj':
            row['projectReferences'].append('src/Planned.Core/Planned.Core.csproj')
        if row['path'] == 'src/Application.Api/Application.Api.csproj' and 'packageReferences' in row:
            row['packageReferences'].extend(['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'])
    architecture.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    settings = root / 'runtime/policies/shells.json'; value = json.loads(settings.read_bytes())
    value['CShells']['Shells']['policies'].setdefault('Configuration', {})['Sample'] = {'Api': {'Prefix': 'configured-'}}
    value['CShells']['Shells']['policies']['Configuration'].setdefault('Foundation', {}).setdefault('Json', {})['Profiles'] = {
        'sample-label-request': {'Preset': 'strict-request', 'MaxBytes': 1024},
        'sample-label-response': {'Preset': 'tolerant-response', 'MaxBytes': 2048}}
    settings.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def sample_database(root, evidence, *, observe=False):
    """Separate explicit disposable deployment/observation; no product startup DDL."""
    script = '''import json,re,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'eng'))
import composition_run as run
graph=run.read(root/'eng/foundation-composition.json'); contract=run.read(root/run.render.CONTRACT)
resolved=run.read(root/run.render.RESOLVED);credentials=run.private_credentials(root,graph)
_,environment=run.compose_model(root,graph,contract,resolved,credentials)
receipt=run.latest(root); command=run.Commands(root,root/'artifacts/composition/runs/typed-sample')
command.secrets=tuple({*credentials.values(),*environment.values()})
database=graph['resources']['database-1']['name']
username=run.model.environment(graph)['database-1'].get('username',database)
run.require(all(re.fullmatch('[a-z][a-z0-9_]{0,62}',value) for value in (database,username)),'Synthetic database identity changed')
sql = 'SELECT json_build_object(\\'value\\',value,\\'revision\\',revision)::text FROM sample_labels WHERE id=1;' if OBSERVE else (
 'CREATE TABLE sample_labels(id integer PRIMARY KEY,value text NOT NULL,revision integer NOT NULL DEFAULT 0); '
 'INSERT INTO sample_labels(id,value) VALUES (1,\\'ready\\'); GRANT SELECT,UPDATE ON sample_labels TO "'+username+'";')
args=[*run.compose_arguments(root,receipt),'exec','-T',run.service('postgresql'),'psql','-U','_programkit','-d',database,'-At','-v','ON_ERROR_STOP=1','-c',sql]
print(command.output(args,environment=environment))
'''.replace('OBSERVE', repr(observe))
    command([sys.executable, '-c', script], root, evidence)
    return json.loads((evidence / 'stdout.log').read_text()) if observe else None


def declare_typed_settings(root, evidence):
    """Review a first declaration against actual native Compile inspection.

    This owns only the new fictional API declaration. It never refreshes an
    existing declaration, nor treats inspection as compiled/packed provenance.
    """
    project = 'src/Application.Api/Application.Api.csproj'
    destination = root / 'src/Application.Api/settings.source.json'
    if destination.exists():
        raise ValueError('Refuse to overwrite an existing settings declaration')
    # This fixture already binds private storage to its API feature. The first
    # complete native declaration must include a real binding for that setting.
    private_options = root / 'src/Application.Api/PrivateEvidenceOptions.cs'
    if private_options.exists():
        raise ValueError('Refuse to overwrite existing private storage options')
    private_options.write_text('''using CShells;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
namespace Application.Api;
/// <summary>Application-owned private storage configuration for this disposable fixture.</summary>
public sealed class PrivateEvidenceOptions
{
    /// <summary>Private mounted storage root; never served as a hosted frontend.</summary>
    public string Root { get; set; } = "";
    /// <summary>Binds the composition-owned section without resolving a provider.</summary>
    public static void Configure(IServiceCollection services, ShellSettings settings)
    {
        services.AddOptions<PrivateEvidenceOptions>().Bind(settings.GetConfigurationRoot().GetSection("EvidenceFiles"))
            .Validate(value => !string.IsNullOrWhiteSpace(value.Root), "EvidenceFiles:Root is required.");
    }
}
''', encoding='utf-8')
    feature = root / 'src/Application.Api/ApiFeature.cs'
    current = feature.read_text(encoding='utf-8')
    seam = 'LabelEndpoints.Configure(services, settings);'
    if current.count(seam) != 1:
        raise ValueError('Actual owned typed registration seam is missing or ambiguous')
    feature.write_text(current.replace(seam, seam + ' PrivateEvidenceOptions.Configure(services, settings);'), encoding='utf-8')
    command(['dotnet', 'restore', project], root, evidence / 'restore')
    command(['dotnet', 'msbuild', project, '-t:FoundationInspectSettingsSourceBindings',
             '-p:Configuration=Release'], root, evidence / 'native-inspection')
    reports = list((root / 'src/Application.Api/obj').rglob('settings-source-bindings.json'))
    if len(reports) != 1:
        raise ValueError('Native settings inspection must produce one current report')
    report = json.loads(reports[0].read_bytes())
    expected = {path.relative_to(root / 'src/Application.Api').as_posix()
                for path in (root / 'src/Application.Api').rglob('*.cs')
                if not {'obj', 'bin'}.intersection(path.relative_to(root / 'src/Application.Api').parts)}
    if (report.get('schemaVersion') != 1 or report.get('contract') != 'utf8-optional-bom-crlf-to-lf-v1'
            or set(report.get('sourceSha256', {})) != expected):
        raise ValueError('Native settings inspection differs from the new owned API sources')
    template = ROOT / 'extensions/program-kit-dotnet/references/examples/typed-operation/settings.source.template.json'
    declaration = json.loads(template.read_bytes())
    declaration['sourceSha256'] = report['sourceSha256']
    declaration['contracts'].append({
        'scope': 'private-evidence', 'typeName': 'Application.Api.PrivateEvidenceOptions', 'complete': True,
        'settings': [{'property': 'Root', 'path': 'EvidenceFiles:Root', 'required': True, 'secret': False,
            'constraints': {'minLength': 1}, 'binding': 'PrivateEvidenceOptions.Configure binds the selected shell EvidenceFiles section and validates Root.',
            'precedence': ['typed source initializer', 'selected shell configuration providers'], 'reload': 'restart',
            'description': 'Application-owned private mounted storage; an empty root is invalid.'}],
        'semanticConstraints': ['The selected composition must supply the private mounted storage root.'],
        'appliesTo': {'kind': 'shell', 'features': ['Application.Api'], 'configuration': ['EvidenceFiles']}})
    destination.write_text(json.dumps(declaration, indent=2) + '\n', encoding='utf-8')
    document = ET.fromstring((root / project).read_bytes())
    ET.SubElement(document.find('PropertyGroup'), 'FoundationSettingsMetadataSource').text = 'settings.source.json'
    (root / project).write_bytes(ET.tostring(document) + b'\n')


def review_fixture_response_edit(root, original, evidence):
    """Review only the known fictional response edit; no consumer re-signing path."""
    import hashlib
    source = root / 'src/Application.Api/ProbeService.cs'
    if (original.count(b'"consumer-ready"') != 1 or source.read_bytes()
            != original.replace(b'"consumer-ready"', b'"consumer-prepared-ready"')):
        raise ValueError('Expected exact owned fixture response edit before source review')
    declaration = root / 'src/Application.Api/settings.source.json'
    previous = declaration.read_bytes(); value = json.loads(previous)
    original_hash = hashlib.sha256(original.decode('utf-8-sig').replace('\r\n', '\n').encode('utf-8')).hexdigest()
    if value['sourceSha256'].get('ProbeService.cs') != original_hash:
        raise ValueError('Original fixture source differs from its reviewed declaration')
    command(['dotnet', 'msbuild', 'src/Application.Api/Application.Api.csproj',
             '-t:FoundationInspectSettingsSourceBindings', '-p:Configuration=Release'], root, evidence / 'native-inspection')
    reports = list((root / 'src/Application.Api/obj').rglob('settings-source-bindings.json'))
    if len(reports) != 1:
        raise ValueError('One current native source inspection is required for the known edit')
    report = json.loads(reports[0].read_bytes()); current = report.get('sourceSha256', {})
    changed = {name for name in set(current) | set(value['sourceSha256'])
               if current.get(name) != value['sourceSha256'].get(name)}
    if (report.get('schemaVersion') != 1 or report.get('contract') != 'utf8-optional-bom-crlf-to-lf-v1'
            or set(current) != set(value['sourceSha256']) or changed != {'ProbeService.cs'}):
        raise ValueError('Known fixture edit cannot refresh any other source or option binding')
    (evidence / 'previous-declaration.json').write_bytes(previous)
    value['sourceSha256'] = current
    declaration.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    (evidence / 'review.json').write_text(json.dumps({
        'scope': 'Explicit review of one owned fictional Policy response literal; option/binding sources unchanged',
        'changedSources': sorted(changed), 'previousDeclarationSha256': hashlib.sha256(previous).hexdigest(),
        'currentDeclarationSha256': hashlib.sha256(declaration.read_bytes()).hexdigest(),
        'nativeCompiledAndPackedProvenanceStillRequired': True}, indent=2) + '\n', encoding='utf-8')


def command(arguments, root, evidence, expected=0, environment=None):
    evidence.mkdir(parents=True, exist_ok=True)
    with (evidence / 'stdout.log').open('wb') as stdout, (evidence / 'stderr.log').open('wb') as stderr:
        completed = subprocess.run([native_path(argument) for argument in arguments], cwd=native_path(root),
                                   stdout=stdout, stderr=stderr, timeout=1800, env=environment)
    if completed.returncode != expected:
        raise ValueError('command failed (' + str(completed.returncode) + '); inspect ' + str(evidence))


def browser_command(arguments, root, evidence, expected=0):
    """Use the exact owned runtime already acquired by native preparation."""
    plan = json.loads(Path(arguments[2]).read_text(encoding='utf-8'))
    cache = (root / 'artifacts/cache/playwright-browsers').resolve()
    selected = plan.get('browserCache')
    if (not isinstance(selected, str) or not cache.is_dir()
            or not Path(selected).resolve().is_relative_to(root.resolve())
            or not Path(selected).samefile(cache)):
        raise ValueError("Browser check must use this consumer's actual prepared owned cache")
    command(arguments, root, evidence, expected=expected,
            environment=dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=native_path(cache)))


def wait_for_typed_host_restart(root, host, evidence):
    """Wait for actual native HTTP readiness before checking retained product data."""
    sys.path.insert(0, str(root / 'eng'))
    import foundation_fixture
    import foundation_qualification
    elapsed = foundation_fixture.poll(
        lambda: foundation_qualification.ready(host['origin'], (host.get('pathBase') or '') + '/bff/user'), timeout=60)
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / 'result.json').write_text(json.dumps({'status': 'ready', 'elapsedSeconds': elapsed,
        'readiness': 'actual selected native BFF HTTP endpoint'}, indent=2) + '\n', encoding='utf-8')
    return elapsed


def install_native_tooling(root, directory):
    """Actual current packaged adapters, never a permissive OpenAPI fallback."""
    imported = os.environ.get('PROGRAM_KIT_IMPORTED_PACKAGES')
    if imported:
        script = "import sys; from pathlib import Path; sys.path.insert(0,str(Path.cwd()/'scripts')); from release_candidate import read,source,verify_payload; verify_payload(read(Path(sys.argv[1])),Path.cwd()/'artifacts',source())"
        command([sys.executable, '-c', script, imported], ROOT, directory / 'imported-payload-verification')
    else:
        script = "import sys; from pathlib import Path; sys.path.insert(0,str(Path.cwd()/'scripts')); import build_release; build_release.build_bundle_from_source(Path.cwd(),Path(sys.argv[1]))"
        command([sys.executable, '-c', script, str(directory)], ROOT, directory / 'current-bundle-build')
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
    from owned_scratch import filesystem_path
    release = Path(filesystem_path(directory / 'release')); release.mkdir()
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    bundle = (ROOT / 'artifacts' if imported else directory) / ('program-kit-' + version + '.zip')
    with zipfile.ZipFile(bundle) as archive:
        for name in archive.namelist():
            path = (release / name).resolve()
            if not path.is_relative_to(release.resolve()): raise ValueError('Owned bundle entry escaped its release directory')
        archive.extractall(release)
    # Library-based native installation uses the existing Spec Kit environment;
    # consumer execution still uses the selected shared device Python.
    site = os.environ.get('PROGRAM_KIT_SPECIFY_SITE_PACKAGES')
    if not site:
        import shutil
        sys.path.insert(0, str(ROOT / 'scripts'))
        from invoke_specify import launcher_site_packages
        launcher = shutil.which('specify')
        if not launcher:
            raise ValueError('Existing Spec Kit launcher/site-packages required; no runtime installation was attempted')
        site = str(launcher_site_packages(Path(launcher)))
    environment = dict(os.environ, SPECIFY_INIT_DIR=filesystem_path(root), PROGRAM_KIT_SPECIFY_SITE_PACKAGES=site)
    cli = [sys.executable, str(ROOT / 'scripts/invoke_specify.py'), '--site-packages', site, '--']
    command([*cli, 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'],
        root, directory / 'native-init', environment=environment)
    for component in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet'):
        command([*cli, 'extension', 'add', str(release / 'extensions' / component), '--dev'],
            root, directory / ('native-' + component), environment=environment)


def containers(project):
    result = subprocess.run(['docker', 'ps', '--no-trunc', '--filter', 'label=com.docker.compose.project=' + project,
                             '--format', '{{.ID}} {{.Label "com.docker.compose.service"}}'],
                            capture_output=True, text=True, timeout=30, check=True)
    return {line.split()[1]: line.split()[0] for line in result.stdout.splitlines() if line.strip()}


def dispose_fixture(root, preparation, evidence):
    """Remove only this generated fixture's containers/network; retain all data.

    Use the shipping credential and output-hash checks, keeping secrets in its
    redacted child environment. Never prune Docker or remove named volumes.
    """
    script = '''import json,sys
from pathlib import Path
root=Path.cwd(); sys.path.insert(0,str(root/'eng'))
import composition_run as run
graph=run.read(root/'eng/foundation-composition.json')
receipt=run.read(root/run.STATE)
# A failed build can leave an honest failure record without Compose fields.
# Use the retained successful preparation for cleanup only; its exact output
# hash/owned project checks still run, and the failed record stays untouched.
if not {'compose','composeSha256','project'} <= set(receipt): receipt=json.loads(sys.argv[1])
credentials=run.private_credentials(root,graph)
contract=run.read(root/run.render.CONTRACT)
resolved=run.read(root/run.render.RESOLVED)
document,environment=run.compose_model(root,graph,contract,resolved,credentials)
command=run.Commands(root,root/'artifacts/composition/runs/test-disposal')
command.secrets=tuple({*credentials.values(),*environment.values()})
command.run([*run.compose_arguments(root,receipt),'down'],environment=environment,timeout=120)
'''
    command([sys.executable, '-c', script, json.dumps(preparation)], root, evidence)


def add_unimplemented_product_plan(root):
    """Planning may name future product bindings before foundation startup."""
    core = 'src/Planned.Core/Planned.Core.csproj'
    path = root / core; path.parent.mkdir(parents=True)
    path.write_text('<Project Sdk="Microsoft.NET.Sdk" />\n', encoding='utf-8')
    project = root / 'src/Application.Api/Application.Api.csproj'
    project.write_text(project.read_text().replace('</Project>',
        '<ItemGroup><ProjectReference Include="../Planned.Core/Planned.Core.csproj" /></ItemGroup></Project>'), encoding='utf-8')
    solution = root / 'Application.slnx'; document = ET.fromstring(solution.read_bytes())
    ET.SubElement(document, 'Project', Path=core)
    solution.write_bytes(ET.tostring(document) + b'\n')
    path = root / 'eng/architecture.json'; architecture = json.loads(path.read_text())
    graph = architecture['runtimeComposition']
    graph['projects'].append({'path': core, 'role': 'core', 'projectReferences': [], 'packageReferences': [],
        'responsibilities': [{'name': 'Planned.Core.ProductContract', 'kind': 'contract', 'effects': []}]})
    api = next(row for row in graph['projects'] if row['path'] == 'src/Application.Api/Application.Api.csproj')
    api['projectReferences'] = [core]
    graph['bindings'].append({'capabilityProject': core, 'capability': 'Planned.Core.IFutureProduct',
        'implementationProject': api['path'], 'implementation': 'Application.Api.FutureProduct',
        'registration': 'Application.Api.FutureRegistration.Register'})
    path.write_text(json.dumps(architecture, indent=2) + '\n', encoding='utf-8')


def verify_build_stages(root, feature, directory):
    """Exercise the emitted Build entrypoint and real host-scoped freshness guards."""
    command(['pwsh', '-NoProfile', '-File', 'eng/Build.ps1', '-LockedMode', '-SkipTests'], root, directory / 'typed-build')
    sys.path.insert(0, str(root / 'eng'))
    import runtime_closure
    from program_kit_version import PROGRAM_KIT_VERSION
    resolved = json.loads((root / 'eng/foundation-composition.resolved.json').read_text())
    for host_id, host in resolved['hosts'].items():
        stage = root / host['runtimeStage']
        closure = root / 'artifacts/composition/closures' / (host_id + '.json')
        runtime_closure.validate(root, stage, closure, PROGRAM_KIT_VERSION)
        other = next((name for name in resolved['hosts'] if name != host_id), None)
        if other:
            try:
                runtime_closure.validate(root, stage, root / 'artifacts/composition/closures' / (other + '.json'), PROGRAM_KIT_VERSION)
            except ValueError:
                pass
            else:
                raise ValueError('wrong-host closure evidence was admitted')
    original_feature = feature.read_bytes()
    try:
        feature.write_bytes(original_feature + b'\n// Changed source must invalidate export closure.\n')
        try:
            runtime_closure.validate(root, root / resolved['hosts']['application-host']['runtimeStage'],
                root / 'artifacts/composition/closures/application-host.json', PROGRAM_KIT_VERSION)
        except ValueError:
            pass
        else:
            raise ValueError('stale source closure was admitted')
    finally:
        feature.write_bytes(original_feature)


def prepare_comparison_tool(root, binary):
    """Stage and probe the reviewed comparator before any emitted Build call."""
    sys.path.insert(0, str(root / 'eng'))
    import toolchain
    pin = (root / '.oasdiff-version').read_text().strip()
    toolchain.install_oasdiff(root, pin, str(binary))
    resolved, actual = toolchain.resolve_oasdiff(root, pin, '')
    if resolved is None or actual != pin:
        raise ValueError('Prepared comparison binary is unavailable to the emitted toolchain')
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='exercise real local Docker startup in the fictional consumer')
    parser.add_argument('--engines', default=os.environ.get('PROGRAMKIT_BROWSER_ENGINES', 'chromium,webkit'))
    parser.add_argument('--tooling', action='store_true', help='also exercise migrated Build, fixture and OpenAPI tooling')
    parser.add_argument('--oasdiff', type=Path, help='existing exact adopted comparison binary; no pin adoption')
    parser.add_argument('--single-host', action='store_true', help='qualify the typed single-host build/export boundary')
    parser.add_argument('--foundation-only', action='store_true', help='scaffold without the fictional unfinished product binding, for the ordinary emitted CI gate')
    parser.add_argument('--nested-shell', action='store_true', help='qualify native BFF/HostedPages paths below a non-root shell prefix')
    args = parser.parse_args()
    if args.nested_shell and (args.tooling or args.foundation_only):
        parser.error('--nested-shell uses the full native runtime fixture; the root-only typed example is a separate qualifier')
    if args.foundation_only and args.execute:
        parser.error('--foundation-only is a scaffold fixture; it cannot narrow the full runtime exercise')
    if args.tooling and (not args.execute or not args.oasdiff or not args.oasdiff.is_file()):
        parser.error('--tooling requires --execute and an existing --oasdiff binary')
    if args.tooling:
        import dependency_profile
        selected = dependency_profile.resolver().new_project_catalog()
        version = selected['families']['foundation']['releaseVersion']
        if tuple(map(int, version.split('-')[0].split('.'))) < (0, 3, 6):
            raise ValueError('Typed operation requires the released Foundation public problem wire contract (0.3.6 or later) '
                             'in the qualified default profile. Publish Foundation and qualify its public profile first; '
                             'no private package or duplicated problem schema substitutes for it.')
    # Native MSBuild assembly probing on Windows still rejects some ordinary
    # package paths over MAX_PATH. Keep this retained SDK fixture short; this
    # qualifies the stated native path envelope, not arbitrary-depth SDK builds.
    directory = ROOT / 'artifacts/t' / ('cs-' + uuid.uuid4().hex[:8])
    root = directory / 'c'
    (root / 'eng').mkdir(parents=True)
    if args.tooling:
        install_native_tooling(root, directory)
    started = time.monotonic()
    graph = two_apps(ROOT, dynamic_ports=True)
    graph['resources']['label-runtime'] = {'kind': 'feature', 'role': 'implementation', 'responsibility': 'runtime',
        'path': 'src/Application.Runtime/Application.Runtime.csproj', 'packageId': 'Application.Runtime', 'featureIdentity': 'Application.Runtime'}
    graph['bindings'].append({'kind': 'featureShell', 'featureRef': 'label-runtime', 'shellRef': 'application-shell'})
    if args.nested_shell:
        graph['resources']['application-shell']['pathBase'] = '/products/orders'
    graph['resources']['ordinary-provider'] = {'kind': 'feature', 'role': 'provider', 'responsibility': 'runtime',
        'path': 'src/Owned.Files/Owned.Files.csproj', 'packageId': 'Owned.Files', 'featureIdentity': 'Owned.Files'}
    graph['bindings'].append({'kind': 'featureShell', 'featureRef': 'ordinary-provider', 'shellRef': 'application-shell'})
    if args.single_host:
        removed = {name for name in graph['resources'] if name.startswith('assessment-')}
        for name in removed:
            del graph['resources'][name]
            graph['environments']['development']['resources'].pop(name, None)
        graph['bindings'] = [row for row in graph['bindings'] if not any(value in removed for value in row.values())]
    page_binding = next(row for row in graph['bindings'] if row['kind'] == 'frontend')
    graph['bindings'].extend([
        {**page_binding, 'routeId': 'second-page', 'path': '/second-page'},
        {**page_binding, 'routeId': 'restricted-page', 'path': '/restricted-page', 'pagePermission': 'restricted.read'}])
    graph['resources']['private-evidence'] = {'kind': 'privateFiles', 'ownerRef': 'application'}
    graph['environments']['development']['resources']['private-evidence'] = {'directory': 'artifacts/private-evidence/policies'}
    graph['bindings'].append({'kind': 'privateFiles', 'filesRef': 'private-evidence', 'hostRef': 'application-host',
        'shellRef': 'application-shell', 'featureRef': 'feature-0', 'setting': 'Root'})
    selection, catalog = accept_fixture(root, graph, ROOT)
    # Exercise reviewed adoption, preserving a source/lock/task history sentinel.
    (root / 'composition-proposal.json').write_text(json.dumps(graph, indent=2) + '\n', encoding='utf-8')
    retained = root / 'specs/001-consumer/tasks.md'; retained.parent.mkdir(parents=True)
    retained.write_text('T007 activation before T008/T009 behavior; T012 retained-baseline regression. Human review pending. Effort retained.\n')
    retained_bytes = retained.read_bytes()
    migration = composition_migrate.preview(root, 'composition-proposal.json')
    composition_migrate.apply(root, migration['planDigest'], 'composition-proposal.json')
    if retained.read_bytes() != retained_bytes:
        raise ValueError('migration rewrote consumer task history')
    environment = os.environ.copy()
    environment.setdefault('PROGRAMKIT_DEVICE_PYTHON', sys.executable)
    os.environ.update(environment)
    os.environ['PROGRAMKIT_BROWSER_ENGINES'] = args.engines
    sync = [sys.executable, str(SCRIPTS / 'dotnet_sync.py'), '--target', str(root), '--profile-selected',
            '--foundation-host-accepted', '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
    command(sync, ROOT, directory / 'scaffold')
    blocks = ROOT / 'extensions/program-kit-building-blocks/scripts/building_blocks.py'
    native = [sys.executable, str(blocks)]
    options = ['--target', str(root), '--catalog', str(catalog)]
    command([*native, 'plan', *options], ROOT, directory / 'native-plan')
    native_plan = json.loads((directory / 'native-plan/stdout.log').read_text())
    command([*native, 'apply', *options, '--plan-digest', native_plan['planDigest']], ROOT, directory / 'native-apply')
    # A second reconciliation must preserve source and produce no new contribution.
    command([*sync, '--check'], ROOT, directory / 'scaffold-check')
    command([*native, 'check', *options], ROOT, directory / 'native-check')
    if not args.foundation_only:
        add_unimplemented_product_plan(root)
    command(sync, ROOT, directory / 'product-plan-scaffold')
    command([*sync, '--check'], ROOT, directory / 'product-plan-scaffold-check')
    command([*native, 'check', *options], ROOT, directory / 'product-plan-native-check')
    ordinary = root / 'src/Owned.Files/ProviderFeature.cs'
    ordinary_source = ordinary.read_text()
    if 'IWebShellFeature' in ordinary_source or 'AddFoundationPostgreSql' in ordinary_source:
        raise ValueError('ordinary provider acquired a foreign HTTP/database responsibility')
    ordinary.write_text(ordinary_source.replace('public void ConfigureServices(IServiceCollection services) { }',
        'public void ConfigureServices(IServiceCollection services) { System.Console.WriteLine("ORDINARY_PROVIDER_REGISTERED"); }'), encoding='utf-8')
    # Model admission is item-specific, never a blanket project/pin exemption.
    project = root / 'src/Application.Api/Application.Api.csproj'
    original_project = project.read_bytes()
    try:
        project.write_bytes(original_project.replace(b'</Project>', b'<ItemGroup><PackageReference Include="Orbyss.Foundation.Mcp.AspNetCore" /></ItemGroup></Project>'))
        command([*native, 'check', *options], ROOT, directory / 'unselected-reference-rejection', expected=2)
        if 'PKB405' not in (directory / 'unselected-reference-rejection/stderr.log').read_text():
            raise ValueError('extra dependency was not rejected by native ownership admission')
    finally:
        project.write_bytes(original_project)
    pins = root / 'eng/ProgramKit.Foundation.props'; original_pins = pins.read_bytes()
    try:
        pins.write_bytes(original_pins.replace(b'</Project>', b'<ItemGroup><PackageVersion Include="Orbyss.Foundation.Mcp.AspNetCore" Version="0.3.3" /></ItemGroup></Project>'))
        command([*native, 'check', *options], ROOT, directory / 'unowned-pin-rejection', expected=2)
        if 'PKB405' not in (directory / 'unowned-pin-rejection/stderr.log').read_text():
            raise ValueError('altered dependency contribution was not rejected by native ownership admission')
    finally:
        pins.write_bytes(original_pins)
    if (root / 'eng/Dev.ps1').exists() or (root / 'deploy/compose.identity.yml').exists():
        raise ValueError('competing startup authoring route was generated')
    result = {'schemaVersion': 2, 'status': 'scaffolded', 'consumer': root.relative_to(ROOT).as_posix(),
              'scaffoldSeconds': round(time.monotonic() - started, 3), 'runtimeExercised': False,
              'engines': args.engines.split(','), 'singleHost': args.single_host, 'toolingExercised': False}
    if args.tooling:
        prepare_comparison_tool(root, args.oasdiff)
    if args.execute:
        command([sys.executable, 'eng/composition_run.py', 'prepare'], root, directory / 'prepare')
        preparation = json.loads((root / 'artifacts/composition/prepared.json').read_text())
        frontend_output = root / graph['resources']['policy-web']['directory'] / 'dist'
        prepared_manifest = json.loads((frontend_output / 'manifest.json').read_text())
        prepared_revision = prepared_manifest['revisions'][-1]
        prepared_assets = {asset['file']: (frontend_output / asset['file']).read_bytes()
                           for asset in prepared_revision['assets']}
        try:
            # Preparation can leave managed prerequisites stopped. Update must
            # admit just this host's dependencies before its --no-deps activation.
            command([sys.executable, 'eng/composition_run.py', 'update', '--host', 'application-host'], root, directory / 'cold-update')
            cold = containers(preparation['project'])
            if args.single_host is False and 'r-' + __import__('hashlib').sha256(b'assessment-host').hexdigest()[:16] in cold:
                raise ValueError('cold selected update activated an unrelated host')
            pending = json.loads((root / 'artifacts/composition/prepared.json').read_text()).get('pendingActivationHosts', [])
            if ('assessment-host' in pending) != (not args.single_host) or 'application-host' in pending:
                raise ValueError('selected activation cleared another host or retained its own pending marker')
            # No source change follows preparation. Plain update must activate
            # the remaining prepared bundle rather than report unchanged.
            command([sys.executable, 'eng/composition_run.py', 'update'], root, directory / 'pending-plain-update')
            if json.loads((root / 'artifacts/composition/prepared.json').read_text()).get('pendingActivationHosts'):
                raise ValueError('ready prepared bundles still have pending activation')
            command([sys.executable, 'eng/composition_run.py', 'run'], root, directory / 'run')
            preparation = json.loads((root / 'artifacts/composition/prepared.json').read_text())
            private_root = root / graph['environments']['development']['resources']['private-evidence']['directory']
            active = containers(preparation['project'])
            application_service = 'r-' + __import__('hashlib').sha256(b'application-host').hexdigest()[:16]
            application_container = active[application_service]
            command(['docker', 'logs', application_container], root, directory / 'ordinary-provider-activation')
            if 'ORDINARY_PROVIDER_REGISTERED' not in (directory / 'ordinary-provider-activation/stdout.log').read_text():
                raise ValueError('published Host did not activate the ordinary IShellFeature provider')
            # Write as the immutable Host's actual non-root identity, and verify
            # bytes independently through the retained host directory.
            command(['docker', 'exec', application_container, 'sh', '-c',
                     'head -c 65536 /dev/zero > /private-evidence/private-evidence/retained.bin'], root, directory / 'private-host-write')
            private_bytes = (private_root / 'retained.bin').read_bytes()
            if private_bytes != bytes(65536):
                raise ValueError('private Host write did not reach the selected retained directory')
            command(['docker', 'restart', application_container], root, directory / 'private-host-restart')
            command([sys.executable, 'eng/composition_run.py', 'run', '--host', 'application-host'], root, directory / 'private-restart-readiness')
            if (private_root / 'retained.bin').read_bytes() != private_bytes:
                raise ValueError('Host restart lost retained private bytes')
            # Stop a real shared prerequisite and update the selected host. Its
            # existing container must be restarted, never recreated.
            database_service = 'r-' + __import__('hashlib').sha256(b'postgresql').hexdigest()[:16]
            command(['docker', 'stop', active[database_service]], root, directory / 'dependency-stop')
            command([sys.executable, 'eng/composition_run.py', 'update', '--host', 'application-host'], root, directory / 'stopped-dependency-update')
            if containers(preparation['project'])[database_service] != active[database_service]:
                raise ValueError('selected update recreated the retained database prerequisite')
            before = containers(preparation['project'])
            edit_started = time.monotonic()
            feature = root / 'src/Application.Api/ApiFeature.cs'
            add_typed_operation(root)
            if args.tooling:
                entry = root / 'web/policy-web/src/app.ts'
                source = entry.read_text(encoding='utf-8')
                seam = 'await bindFoundationPresentation(root);'
                if source.count(seam) != 1:
                    raise ValueError('Expected actual generated native browser binding')
                entry.write_text("import { attachExampleEditor } from './unsaved-editor';\n" + source.replace(seam,
                    'const presentation = await bindFoundationPresentation(root);\n  attachExampleEditor(root, presentation);'), encoding='utf-8')
                entry.with_name('unsaved-editor.ts').write_bytes((ROOT / 'extensions/program-kit-dotnet/references/examples/unsaved-editor.ts').read_bytes())
            sample_database(root, directory / 'sample-schema')
            source = feature.read_text()
            source = 'using CShells;\nusing ProgramKit.Examples.TypedOperation;\n' + source
            source = source.replace('public sealed class ApiFeature :', 'public sealed class ApiFeature(ShellSettings settings) :')
            source = source.replace('"Orbyss.Foundation.DomainEvents"]',
                '"Orbyss.Foundation.DomainEvents", "Orbyss.Foundation.Json.AspNetCore", "Orbyss.Foundation.Web.ProblemDetails"]')
            source = source.replace('using CShells.AspNetCore.Features;',
                                    'using CShells.AspNetCore.Features;\nusing Microsoft.AspNetCore.Builder;\nusing Microsoft.AspNetCore.Http;\nusing Microsoft.AspNetCore.Mvc;')
            source = source.replace('public void ConfigureServices(IServiceCollection services) { }',
                                    'public void ConfigureServices(IServiceCollection services) { services.AddScoped<ProbeService>(); LabelEndpoints.Configure(services, settings); }')
            feature.with_name('ProbeService.cs').write_text('''namespace Application.Api;
/// <summary>Consumer-owned service resolved only during the real operation.</summary>
public sealed class ProbeService
{
    /// <summary>Marks actual resolution; offline export must never construct this service.</summary>
    public ProbeService() { System.Console.WriteLine("TOOLING_SERVICE_ACTIVATED"); }
    /// <summary>Supplies the deterministic owned operation result.</summary>
    public string Policy => "consumer-ready";
}
''', encoding='utf-8')
            seam = 'public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) { }'
            if seam not in source:
                raise ValueError('consumer-owned endpoint seam changed')
            feature.write_text(source.replace(seam, 'public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)\n'
                               '    {\n        LabelEndpoints.Map(endpoints);\n        endpoints.MapGet("/api/first-policy", ([FromServices] ProbeService service) => Results.Ok(new { policy = service.Policy }))'
                               '.WithName("ReadFirstPolicy").RequireAuthorization().ExcludeFromDescription();\n'
                               '        endpoints.MapGet("/api/permission-probe", () => Results.NoContent())'
                               '.WithName("ProbePermission").RequireAuthorization(policy => policy.RequireRole("admin")).ExcludeFromDescription();\n    }'), encoding='utf-8')
            # This new slice changes actual project/package references. Explicit
            # preparation owns their restore; ordinary update acquires nothing.
            if args.tooling:
                declare_typed_settings(root, directory / 'typed-settings-source')
            command([sys.executable, 'eng/composition_run.py', 'prepare'], root, directory / 'consumer-dependencies-prepare')
            command([sys.executable, 'eng/composition_run.py', 'update', '--host', 'application-host'], root, directory / 'consumer-update')
            after = containers(preparation['project'])
            import hashlib
            changed = 'r-' + hashlib.sha256(b'application-host').hexdigest()[:16]
            if set(before) != set(after) or any(before[name] != after[name] for name in before if name != changed):
                raise ValueError('consumer edit recreated unrelated application/identity/database services')
            if before[changed] == after[changed]:
                raise ValueError('consumer feature update did not replace its activated host')
            # Reuse the same real authenticated adapter with an explicit owned
            # product assertion; this does not add a product route to the scaffold.
            native_run = sorted((root / 'artifacts/composition/runs').glob('run-*/browser-plan.json'))[-1]
            plan = json.loads(native_run.read_text())
            first = next(host for host in plan['hosts'] if host['id'] == 'application-host')
            first.update(productPath='/api/first-policy', productResponse={'policy': 'consumer-ready'})
            first['pageChecks'] = [{'path': '/second-page', 'status': 200},
                                  {'path': '/restricted-page', 'status': 302, 'denialPath': '/bff/access-denied'},
                                  {'path': '/private-evidence/private-evidence/retained.bin', 'status': 404}]
            plan_path = directory / 'consumer-feature-plan.json'
            plan_path.write_text(json.dumps(plan), encoding='utf-8')
            product_result = directory / 'consumer-feature-result.json'
            browser_command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(product_result)], root, directory / 'consumer-feature')
            if json.loads(product_result.read_text())['status'] != 'ready':
                raise ValueError('first consumer feature did not pass actual authenticated HTTP')
            edit_elapsed = round(time.monotonic() - edit_started, 3)
            # Separately prepare changed content. Preparation marks every staged
            # host pending, so plain update must activate that full prepared set.
            probe = feature.with_name('ProbeService.cs')
            previous_probe = probe.read_bytes()
            probe.write_text(probe.read_text().replace('consumer-ready', 'consumer-prepared-ready'), encoding='utf-8')
            if args.tooling:
                review_fixture_response_edit(root, previous_probe, directory / 'reviewed-response-edit')
            prepared_before = containers(preparation['project'])
            command([sys.executable, 'eng/composition_run.py', 'prepare'], root, directory / 'consumer-edit-prepare')
            prepared_edit = json.loads((root / 'artifacts/composition/prepared.json').read_text())
            if 'application-host' not in prepared_edit.get('pendingActivationHosts', []):
                raise ValueError('changed prepared bundle did not retain activation intent')
            command([sys.executable, 'eng/composition_run.py', 'update'], root, directory / 'consumer-prepared-update')
            prepared_after = containers(preparation['project'])
            host_services = {'r-' + hashlib.sha256(name.encode()).hexdigest()[:16]
                             for name in prepared_edit['pendingActivationHosts']}
            if set(prepared_before) != set(prepared_after) or any(
                    prepared_before[name] != prepared_after[name] for name in prepared_before if name not in host_services):
                raise ValueError('prepared update recreated retained non-host prerequisites')
            if any(prepared_before[name] == prepared_after[name] for name in host_services):
                raise ValueError('plain update did not activate every prepared host bundle')
            first['productResponse'] = {'policy': 'consumer-prepared-ready'}
            plan_path.write_text(json.dumps(plan), encoding='utf-8')
            browser_command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(product_result)], root, directory / 'consumer-prepared-feature')
            if json.loads(product_result.read_text())['status'] != 'ready':
                raise ValueError('prepared content was not served by the activated published Host')
            after = prepared_after
            verify_build_stages(root, feature, directory)
            if args.tooling:
                import shutil
                import composition_render
                sys.path.insert(0, str(root / 'eng'))
                import foundation_qualification as qualification
                # Loader must use the migrated provider realm, with no credential output.
                command([sys.executable, 'eng/web_identity.py', '--repository', '.', '--shell', 'application-shell'],
                    root, directory / 'selected-web-identity')
                selected_identity = json.loads((directory / 'selected-web-identity/stdout.log').read_text())
                os.environ['PROGRAMKIT_IDENTITY_REALM_FILE'] = selected_identity['realmFile']
                os.environ['PROGRAMKIT_IDENTITY_AUTHORITY'] = selected_identity['authority']
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(root / 'artifacts/cache/playwright-browsers')
                command(['node', '--input-type=module', '-e', "await import('./eng/web/persona-fixture.ts')"], root, directory / 'migrated-personas')
                os.environ['PROGRAMKIT_PERMISSION_PROBE_PATH'] = '/api/permission-probe'
                browser_dir = directory / 'maintained-bff'; browser_dir.mkdir()
                projection = composition_render.recipe_projection(graph, 'application-shell')
                browser_config = qualification.authentication_browser_configuration(root, projection, browser_dir, args.engines.split(','))
                command(['node', str(root / 'eng/web/node_modules/@playwright/test/cli.js'), 'test',
                         '--config', str(browser_config), 'authentication.spec.ts'], root, browser_dir / 'execution')
                command(['pwsh', '-NoProfile', '-File', 'eng/Test-Web.ps1', '-BaseUrl', first['origin'],
                         '-Shell', 'application-shell', '-PermissionProbePath', '/api/permission-probe'],
                        root, directory / 'emitted-test-web')
                for shell_id, frontend_id in [('application-shell', 'policy-web'), ('assessment-shell', 'assessment-web')]:
                    if shell_id not in graph['resources']:
                        continue
                    shell = graph['resources'][shell_id]['name']
                    feature_ids = [graph['resources'][row['featureRef']]['featureIdentity'] for row in graph['bindings']
                                   if row['kind'] == 'featureShell' and row['shellRef'] == shell_id]
                    arguments = [sys.executable, 'eng/openapi_init.py', '--repository', '.', '--identity', shell,
                                 '--document-name', 'v1', '--shell', shell, '--application-directory', 'web/' + frontend_id,
                                 '--application-script', 'check', '--application-tsconfig', 'web/' + frontend_id + '/tsconfig.json']
                    for feature_id in feature_ids: arguments.extend(['--feature', feature_id])
                    command(arguments, root, directory / ('openapi-init-' + shell))
                    command([sys.executable, 'eng/js_toolchain.py', '--repository', '.', 'npm', '--', '--prefix',
                             'tools/openapi/' + shell, 'install', '--package-lock-only', '--ignore-scripts',
                             '--strict-peer-deps', '--engine-strict'], root, directory / ('openapi-lock-' + shell))
                # Init and generator locks are source changes: restage normally, never reseal old evidence.
                command(['pwsh', '-NoProfile', '-File', 'eng/Build.ps1', '-LockedMode', '-SkipTests', '-InitializeOpenApiBaseline'],
                        root, directory / 'typed-openapi-pipeline')
                export_output = (directory / 'typed-openapi-pipeline/stdout.log').read_text()
                if 'TOOLING_SERVICE_ACTIVATED' in export_output:
                    raise ValueError('offline export constructed the consumer operation service')
                document = json.loads((root / 'contracts/openapi/policies.json').read_text())
                if 'requestBody' in document['paths']['/api/sample-label']['get'] or 'ProbeService' in json.dumps(document):
                    raise ValueError('service dependencies leaked into the public wire schema')
                if any(path in document['paths'] for path in ('/api/first-policy', '/api/permission-probe')):
                    raise ValueError('test-only diagnostics leaked into the public generated client')
                if 'requestBody' not in document['paths']['/api/sample-label']['post']:
                    raise ValueError('shipping typed operation did not export its actual request contract')
                # Compile and execute the application adapter against actual
                # maintained generated paths, rather than a handwritten schema.
                frontend_source = root / 'web/policy-web/src'
                frontend_source.joinpath('client.ts').write_bytes((ROOT / 'extensions/program-kit-dotnet/references/examples/typed-operation/client.ts').read_bytes())
                entry = frontend_source / 'app.ts'
                entry.write_text(entry.read_text() + '''
import { storeLabel } from './client';
declare global { interface Window { programKitTypedExample: { storeLabel: typeof storeLabel }; } }
window.programKitTypedExample = { storeLabel };
''', encoding='utf-8')
                before_effect = sample_database(root, directory / 'sample-before-operation', observe=True)
                if before_effect != {'value': 'ready', 'revision': 0}:
                    raise ValueError('metadata export or registration caused an application write')
                command([sys.executable, 'eng/composition_run.py', 'update', '--host', 'application-host'],
                    root, directory / 'typed-client-update')
                first['typedOperation'] = {'body': {'policy': 'stored'}, 'response': {'policy': 'configured-stored'}}
                typed_plan = directory / 'typed-client-plan.json'; typed_plan.write_text(json.dumps(plan), encoding='utf-8')
                typed_result = directory / 'typed-client-result.json'
                browser_command(['node', 'eng/web/composition-readiness.mjs', str(typed_plan), str(typed_result)],
                    root, directory / 'typed-client-operation')
                first.pop('typedOperation')
                committed = sample_database(root, directory / 'sample-committed-observation', observe=True)
                if committed != {'value': 'stored', 'revision': len(args.engines.split(','))}:
                    raise ValueError('actual generated-client operation duplicated or lost a durable write')
                active_host = containers(preparation['project'])[changed]
                command(['docker', 'restart', active_host], root, directory / 'typed-operation-restart')
                result['typedHostRestartReadinessSeconds'] = wait_for_typed_host_restart(
                    root, first, directory / 'typed-operation-restart-readiness')
                restart_plan = {**plan, 'hosts': [{**first, 'productPath': '/api/sample-label',
                    'productResponse': {'policy': 'configured-stored'}}]}
                restart_path = directory / 'typed-operation-restart-plan.json'; restart_path.write_text(json.dumps(restart_plan), encoding='utf-8')
                browser_command(['node', 'eng/web/composition-readiness.mjs', str(restart_path),
                    str(directory / 'typed-operation-restart-result.json')], root, directory / 'typed-operation-retained')
                result.update(actualTypedRequestResponse=True, actualGeneratedTypesAndClient=True,
                    actualProviderPortResolution=True, actualNondefaultScalarOptions=True,
                    independentDurableWriteObservation=True, actualHostRestartRetainsEffect=True)
                resolved = json.loads((root / 'eng/foundation-composition.resolved.json').read_bytes())
                archives = list((root / resolved['hosts']['application-host']['runtimeStage'] / 'packages').glob('Application.Api.*.nupkg'))
                if len(archives) != 1:
                    raise ValueError('Expected one actual packed API settings owner')
                with zipfile.ZipFile(archives[0]) as archive:
                    metadata = json.loads(archive.read('orbyss-foundation/settings.json'))
                    assembly = archive.read('lib/net10.0/Application.Api.dll')
                options = next(row for row in metadata['contracts'] if row['scope'] == 'sample-api')
                prefix = next(row for row in options['settings'] if row['path'] == 'Sample:Api:Prefix')
                if (metadata['assembly']['sha256'] != hashlib.sha256(assembly).hexdigest()
                        or not options['complete'] or prefix['default'] != '' or not prefix['required']
                        or prefix['constraints'] != {'minLength': 1, 'maxLength': 32}):
                    raise ValueError('Actual packed source-backed options metadata differs from its owner')
                result['actualPackedSettingsMetadata'] = True
                presentation = json.loads((root / 'eng/foundation-settings.contract.json').read_bytes())['shells']['application-shell']['browserPresentation']
                settings = presentation['settings']
                control_plan = {**plan, 'hosts': [{**first, 'productPath': '/api/sample-label',
                    'productResponse': {'policy': 'configured-stored'}, 'presentationProbe': {
                        'routePrefix': settings['RoutePrefix'], 'signOutText': settings['Copy'].get('sign-out', 'Sign out')}}]}
                control_path = directory / 'native-generated-controls-plan.json'
                control_path.write_text(json.dumps(control_plan), encoding='utf-8')
                control_result = directory / 'native-generated-controls-result.json'
                browser_command(['node', 'eng/web/composition-readiness.mjs', str(control_path), str(control_result)],
                    root, directory / 'native-generated-controls')
                control_observed = json.loads(control_result.read_bytes())
                if control_observed['status'] != 'ready' or not all(check.get('nativeGeneratedControls') is True for check in control_observed['checks']):
                    raise ValueError('Actual generated native control binding was not qualified')
                result['actualNativeGeneratedControls'] = True
                result['toolingExercised'] = True
            frontend = root / graph['resources']['policy-web']['directory'] / graph['resources']['policy-web']['entry']
            frontend.write_text(frontend.read_text().replace("heading.textContent = 'Application foundation'", "heading.textContent = 'Consumer edited frontend'").replace("createElement('h1')", "createElement('h2')"), encoding='utf-8')
            styles = frontend.with_name('styles.css')
            styles.write_text(styles.read_text() + '\nh2 { color: rebeccapurple; }\n', encoding='utf-8')
            command([sys.executable, 'eng/composition_run.py', 'update'], root, directory / 'frontend-update')
            updated_manifest = json.loads((frontend_output / 'manifest.json').read_text())
            if updated_manifest['currentRevision'] == prepared_manifest['currentRevision'] or prepared_revision not in updated_manifest['revisions']:
                raise ValueError('frontend update did not retain the prepared revision alongside a new revision')
            for name, payload in prepared_assets.items():
                if (frontend_output / name).read_bytes() != payload:
                    raise ValueError('frontend update changed a previous revision asset: ' + name)
            ui_updated = containers(preparation['project'])
            if any(after[name] != ui_updated[name] for name in after if name != changed):
                raise ValueError('frontend edit recreated unrelated services')
            first['expectedHeading'] = 'Consumer edited frontend'
            plan_path.write_text(json.dumps(plan), encoding='utf-8')
            browser_command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(directory / 'frontend-feature-result.json')], root, directory / 'frontend-feature')
            for engine in args.engines.split(','):
                privacy = {**plan, 'engines': [engine], 'hosts': [first], 'privacyProbe': True}
                privacy_plan = directory / ('privacy-' + engine + '.json')
                privacy_plan.write_text(json.dumps(privacy), encoding='utf-8')
                privacy_result = directory / ('privacy-' + engine + '-result.json')
                evidence = directory / ('privacy-' + engine)
                browser_command(['node', 'eng/web/composition-readiness.mjs', str(privacy_plan), str(privacy_result)], root, evidence, expected=2)
                outcome = json.loads(privacy_result.read_text())
                if outcome['status'] != 'failed' or outcome.get('failure', {}).get('phase') != 'privacy-failure-check':
                    raise ValueError('privacy negative case did not reach the intended authenticated failure')
                files = [privacy_result, *evidence.rglob('*')]
                if any('PROGRAMKIT_PRIVATE_FAILURE_SENTINEL' in file.read_text(encoding='utf-8', errors='replace') for file in files if file.is_file()):
                    raise ValueError('authenticated private DOM escaped into failure evidence')
            prior_identity = json.loads((root / 'artifacts/composition/private/identity-state.json').read_text())['product-identity']
            graph['resources']['application-client']['callbackPath'] = '/consumer-signin'
            if args.tooling:
                entry = root / 'web/policy-web/src/app.ts'
                graph['resources']['application-shell'].setdefault('presentation', {'enabled': True})['entrypoints'] = {
                    'policy-web': hashlib.sha256(entry.read_bytes()).hexdigest()}
            graph['resources']['reports-api'] = {'kind': 'protectedResource', 'authorityRef': 'product-identity',
                                                  'ownerRef': graph['resources']['application-api']['ownerRef']}
            graph['environments']['development']['resources']['reports-api'] = {'audience': 'reports-api'}
            (root / 'eng/foundation-composition.json').write_text(json.dumps(graph), encoding='utf-8')
            command(sync, ROOT, directory / 'identity-reconcile-scaffold')
            command([sys.executable, 'eng/composition_run.py', 'prepare'], root, directory / 'identity-reconcile-prepare')
            current_identity = json.loads((root / 'artifacts/composition/private/identity-state.json').read_text())['product-identity']
            if current_identity['users'] != prior_identity['users'] or any(current_identity['clients'][name] != identity for name, identity in prior_identity['clients'].items()):
                raise ValueError('identity reconciliation replaced existing users or registration identities')
            if 'reports-api' not in current_identity['clients']:
                raise ValueError('new protected resource was not provisioned into the existing identity authority')
            command([sys.executable, 'eng/composition_run.py', 'run'], root, directory / 'identity-reconcile-run')
            command([sys.executable, 'eng/composition_run.py', 'stop', '--host', 'application-host'], root, directory / 'private-unavailable-stop')
            retained_root = private_root.with_name(private_root.name + '-retained-test')
            private_root.rename(retained_root)
            try:
                command([sys.executable, 'eng/composition_run.py', 'prepare'], root, directory / 'private-unavailable', expected=2)
                if private_root.exists() or 'private storage is unavailable' not in (directory / 'private-unavailable/stderr.log').read_text():
                    raise ValueError('missing retained storage was recreated or accepted')
            finally:
                retained_root.rename(private_root)
            command([sys.executable, 'eng/composition_run.py', 'run', '--host', 'application-host'], root, directory / 'private-volume-recovery')
            browser_command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(directory / 'post-reconcile-feature-result.json')], root, directory / 'post-reconcile-feature')
            # The ordinary product gate still rejects the incomplete binding.
            # Run this last: its metadata-helper restore legitimately adds lock
            # inputs and invalidates prior staging; do not reseal that evidence.
            command([sys.executable, 'eng/repository_architecture.py', '--repository', '.',
                     '--manifest', 'eng/architecture.json', '--configuration', 'Release',
                     '--build-subject', 'Application.slnx', '--output', 'artifacts/product-architecture.xml'],
                    root, directory / 'pending-product-architecture', expected=2)
            if 'Binding must name real compiled interface and implementation types' not in (directory / 'pending-product-architecture/stderr.log').read_text():
                raise ValueError('ordinary product architecture gate failed before the intended unimplemented binding')
            run_result = json.loads((directory / 'run/stdout.log').read_text().splitlines()[-1])
            result.update(status='passed', runtimeExercised=True, nestedShellQualified=args.nested_shell, preparation=preparation['timings'],
                          preparationSeconds=preparation['elapsedSeconds'], preparedStartupSeconds=run_result['elapsedSeconds'],
                          editToWorkingConsumerSeconds=edit_elapsed, authenticatedPrivacyFailureChecked=True,
                          unchangedServiceCount=len(before) - 1, infrastructureRepairsAfterReadiness=0,
                          frontendIncrementalUpdate=True, persistentIdentityReconciliation=True,
                          retainedPrivateHostBytes=65536, privateRestartRetention=True, privatePublicIsolation=True,
                          missingPrivateVolumeRejected=True, coldSelectedUpdate=True, stoppedDependencyUpdate=True,
                          pendingProductBindingPreserved=True, completeProductArchitectureStillRequired=True,
                          ordinaryRuntimeProviderActivated=True, preparedPlainUpdateActivated=True,
                          measurement='Deterministic edit/build/authenticated operation; no agent reasoning-time claim')
        finally:
            model_file = root / 'eng/foundation-composition.json'
            original = model_file.read_bytes()
            try:
                model_file.write_text('{"schemaVersion": "deliberately-invalid-pending-edit"}', encoding='utf-8')
                command([sys.executable, 'eng/composition_run.py', 'stop'], root, directory / 'stop')
                if containers(preparation['project']):
                    raise ValueError('owned shutdown left running services after a pending model edit')
            finally:
                model_file.write_bytes(original)
            dispose_fixture(root, preparation, directory / 'dispose-fixture')
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
