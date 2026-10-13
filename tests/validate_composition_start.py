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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='exercise real local Docker startup in the fictional consumer')
    parser.add_argument('--engines', default=os.environ.get('PROGRAMKIT_BROWSER_ENGINES', 'chromium,webkit'))
    args = parser.parse_args()
    directory = ROOT / 'artifacts/tests/composition-start' / uuid.uuid4().hex
    root = directory / 'consumer'
    (root / 'eng').mkdir(parents=True)
    started = time.monotonic()
    graph = two_apps(ROOT, dynamic_ports=True)
    page_binding = next(row for row in graph['bindings'] if row['kind'] == 'frontend')
    graph['bindings'].extend([
        {**page_binding, 'routeId': 'second-page', 'path': '/second-page'},
        {**page_binding, 'routeId': 'restricted-page', 'path': '/restricted-page', 'pagePermission': 'restricted.read'}])
    selection, catalog = accept_fixture(root, graph, ROOT)
    (root / 'eng/foundation-composition.json').write_text(json.dumps(graph, indent=2) + '\n', encoding='utf-8')
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
              'scaffoldSeconds': round(time.monotonic() - started, 3), 'runtimeExercised': False}
    if args.execute:
        command([sys.executable, 'eng/composition_run.py', 'prepare'], root, directory / 'prepare')
        preparation = json.loads((root / 'artifacts/composition/prepared.json').read_text())
        frontend_output = root / graph['resources']['policy-web']['directory'] / 'dist'
        prepared_manifest = json.loads((frontend_output / 'manifest.json').read_text())
        prepared_revision = prepared_manifest['revisions'][-1]
        prepared_assets = {asset['file']: (frontend_output / asset['file']).read_bytes()
                           for asset in prepared_revision['assets']}
        try:
            command([sys.executable, 'eng/composition_run.py', 'run'], root, directory / 'run')
            preparation = json.loads((root / 'artifacts/composition/prepared.json').read_text())
            before = containers(preparation['project'])
            edit_started = time.monotonic()
            feature = root / 'src/Application.Api/ApiFeature.cs'
            source = feature.read_text()
            source = source.replace('using CShells.AspNetCore.Features;',
                                    'using CShells.AspNetCore.Features;\nusing Microsoft.AspNetCore.Builder;\nusing Microsoft.AspNetCore.Http;')
            seam = 'public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) { }'
            if seam not in source:
                raise ValueError('consumer-owned endpoint seam changed')
            feature.write_text(source.replace(seam, 'public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)\n'
                               '    {\n        endpoints.MapGet("/api/first-policy", () => Results.Ok(new { policy = "consumer-ready" }))'
                               '.RequireAuthorization();\n    }'), encoding='utf-8')
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
                                  {'path': '/restricted-page', 'status': 302, 'denialPath': '/bff/access-denied'}]
            plan_path = directory / 'consumer-feature-plan.json'
            plan_path.write_text(json.dumps(plan), encoding='utf-8')
            product_result = directory / 'consumer-feature-result.json'
            command(['node', 'eng/web/composition-readiness.mjs', str(plan_path), str(product_result)], root, directory / 'consumer-feature')
            if json.loads(product_result.read_text())['status'] != 'ready':
                raise ValueError('first consumer feature did not pass actual authenticated HTTP')
            edit_elapsed = round(time.monotonic() - edit_started, 3)
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
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
