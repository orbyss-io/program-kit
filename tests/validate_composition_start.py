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
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-dotnet/scripts'
sys.path.insert(0, str(SCRIPTS))
from composition_fixture import two_apps, accept_fixture
import composition_migrate


def command(arguments, root, evidence, expected=0):
    evidence.mkdir(parents=True, exist_ok=True)
    with (evidence / 'stdout.log').open('wb') as stdout, (evidence / 'stderr.log').open('wb') as stderr:
        completed = subprocess.run(arguments, cwd=root, stdout=stdout, stderr=stderr, timeout=1800)
    if completed.returncode != expected:
        raise ValueError('command failed (' + str(completed.returncode) + '); inspect ' + str(evidence))


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
credentials=run.private_credentials(root,graph)
contract=run.read(root/run.render.CONTRACT)
resolved=run.read(root/run.render.RESOLVED)
document,environment=run.compose_model(root,graph,contract,resolved,credentials)
command=run.Commands(root,root/'artifacts/composition/runs/test-disposal')
command.secrets=tuple({*credentials.values(),*environment.values()})
command.run([*run.compose_arguments(root,receipt),'down'],environment=environment,timeout=120)
'''
    command([sys.executable, '-c', script], root, evidence)


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='exercise real local Docker startup in the fictional consumer')
    parser.add_argument('--engines', default=os.environ.get('PROGRAMKIT_BROWSER_ENGINES', 'chromium,webkit'))
    parser.add_argument('--tooling', action='store_true', help='also exercise migrated Build, fixture and OpenAPI tooling')
    parser.add_argument('--oasdiff', type=Path, help='existing exact adopted comparison binary; no pin adoption')
    parser.add_argument('--single-host', action='store_true', help='qualify the typed single-host build/export boundary')
    args = parser.parse_args()
    if args.tooling and (not args.execute or not args.oasdiff or not args.oasdiff.is_file()):
        parser.error('--tooling requires --execute and an existing --oasdiff binary')
    directory = ROOT / 'artifacts/tests/composition-start' / uuid.uuid4().hex
    root = directory / 'consumer'
    (root / 'eng').mkdir(parents=True)
    started = time.monotonic()
    graph = two_apps(ROOT, dynamic_ports=True)
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
    add_unimplemented_product_plan(root)
    command(sync, ROOT, directory / 'product-plan-scaffold')
    command([*sync, '--check'], ROOT, directory / 'product-plan-scaffold-check')
    command([*native, 'check', *options], ROOT, directory / 'product-plan-native-check')
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
            command([sys.executable, 'eng/composition_run.py', 'run'], root, directory / 'run')
            preparation = json.loads((root / 'artifacts/composition/prepared.json').read_text())
            private_root = root / graph['environments']['development']['resources']['private-evidence']['directory']
            active = containers(preparation['project'])
            application_service = 'r-' + __import__('hashlib').sha256(b'application-host').hexdigest()[:16]
            application_container = active[application_service]
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
            source = feature.read_text()
            source = source.replace('using CShells.AspNetCore.Features;',
                                    'using CShells.AspNetCore.Features;\nusing Microsoft.AspNetCore.Builder;\nusing Microsoft.AspNetCore.Http;\nusing Microsoft.AspNetCore.Mvc;')
            source = source.replace('public void ConfigureServices(IServiceCollection services) { }',
                                    'public void ConfigureServices(IServiceCollection services) { services.AddScoped<ProbeService>(); }')
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
                               '    {\n        endpoints.MapGet("/api/first-policy", ([FromServices] ProbeService service) => Results.Ok(new { policy = service.Policy }))'
                               '.WithName("ReadFirstPolicy").RequireAuthorization();\n'
                               '        endpoints.MapGet("/api/permission-probe", () => Results.NoContent())'
                               '.WithName("ProbePermission").RequireAuthorization(policy => policy.RequireRole("admin"));\n    }'), encoding='utf-8')
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
            command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(product_result)], root, directory / 'consumer-feature')
            if json.loads(product_result.read_text())['status'] != 'ready':
                raise ValueError('first consumer feature did not pass actual authenticated HTTP')
            edit_elapsed = round(time.monotonic() - edit_started, 3)
            verify_build_stages(root, feature, directory)
            if args.tooling:
                import shutil
                import composition_render
                sys.path.insert(0, str(root / 'eng'))
                import foundation_qualification as qualification
                # Loader must use the migrated provider realm, with no credential output.
                authority = graph['environments']['development']['resources']['product-identity']
                realm = root / 'deploy/keycloak/product-identity' / (authority['realm'] + '-realm.json')
                os.environ['PROGRAMKIT_IDENTITY_REALM_FILE'] = str(realm)
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(root / 'artifacts/cache/browsers')
                command(['node', '--input-type=module', '-e', "await import('./eng/web/persona-fixture.ts')"], root, directory / 'migrated-personas')
                os.environ['PROGRAMKIT_IDENTITY_AUTHORITY'] = authority['publicOrigin'] + '/realms/' + authority['realm']
                os.environ['PROGRAMKIT_PERMISSION_PROBE_PATH'] = '/api/permission-probe'
                browser_dir = directory / 'maintained-bff'; browser_dir.mkdir()
                projection = composition_render.recipe_projection(graph, 'application-shell')
                browser_config = qualification.authentication_browser_configuration(root, projection, browser_dir, args.engines.split(','))
                command(['node', str(root / 'eng/web/node_modules/@playwright/test/cli.js'), 'test',
                         '--config', str(browser_config), 'authentication.spec.ts'], root, browser_dir / 'execution')
                pin = (root / '.oasdiff-version').read_text().strip()
                binary_dir = root / 'artifacts/tools/oasdiff' / pin; binary_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(args.oasdiff, binary_dir / args.oasdiff.name)
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
                if 'requestBody' in document['paths']['/api/first-policy']['get'] or 'ProbeService' in json.dumps(document):
                    raise ValueError('service dependencies leaked into the public wire schema')
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
            command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(directory / 'frontend-feature-result.json')], root, directory / 'frontend-feature')
            for engine in args.engines.split(','):
                privacy = {**plan, 'engines': [engine], 'hosts': [first], 'privacyProbe': True}
                privacy_plan = directory / ('privacy-' + engine + '.json')
                privacy_plan.write_text(json.dumps(privacy), encoding='utf-8')
                privacy_result = directory / ('privacy-' + engine + '-result.json')
                evidence = directory / ('privacy-' + engine)
                command(['node', 'eng/web/composition-readiness.mjs', str(privacy_plan), str(privacy_result)], root, evidence, expected=2)
                outcome = json.loads(privacy_result.read_text())
                if outcome['status'] != 'failed' or outcome.get('failure', {}).get('phase') != 'privacy-failure-check':
                    raise ValueError('privacy negative case did not reach the intended authenticated failure')
                files = [privacy_result, *evidence.rglob('*')]
                if any('PROGRAMKIT_PRIVATE_FAILURE_SENTINEL' in file.read_text(encoding='utf-8', errors='replace') for file in files if file.is_file()):
                    raise ValueError('authenticated private DOM escaped into failure evidence')
            prior_identity = json.loads((root / 'artifacts/composition/private/identity-state.json').read_text())['product-identity']
            graph['resources']['application-client']['callbackPath'] = '/consumer-signin'
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
            command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(directory / 'post-reconcile-feature-result.json')], root, directory / 'post-reconcile-feature')
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
            result.update(status='passed', runtimeExercised=True, preparation=preparation['timings'],
                          preparationSeconds=preparation['elapsedSeconds'], preparedStartupSeconds=run_result['elapsedSeconds'],
                          editToWorkingConsumerSeconds=edit_elapsed, authenticatedPrivacyFailureChecked=True,
                          unchangedServiceCount=len(before) - 1, infrastructureRepairsAfterReadiness=0,
                          frontendIncrementalUpdate=True, persistentIdentityReconciliation=True,
                          retainedPrivateHostBytes=65536, privateRestartRetention=True, privatePublicIsolation=True,
                          missingPrivateVolumeRejected=True, coldSelectedUpdate=True, stoppedDependencyUpdate=True,
                          pendingProductBindingPreserved=True, completeProductArchitectureStillRequired=True,
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
