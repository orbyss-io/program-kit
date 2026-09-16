"""Bind existing synthetic host/provider fixtures to the selected bootstrap design."""
import json
from pathlib import Path
import re

from bootstrap_provider_context import project


CASES = {
    'foundation-activation': ['Shell.compiled_boundary_positive_and_negative',
        'PublishedHost.exact_image_activation', 'Shell.actual_registration_and_replacement',
        'PublishedHost.http_profiles_headers_openapi', 'PublishedHost.bundle_restart'],
    'bff-keycloak': ['Identity.pinned_provider_discovery', 'Identity.published_bff_activation',
        'Identity.code_flow_permission_negatives_and_logout'],
    'ef-postgresql': ['PostgreSql.exact_server', 'PostgreSql.write_read',
        'PostgreSql.atomic_expected_revision_conflict', 'PostgreSql.transaction_rollback',
        'PostgreSql.restart_preserves_state'],
}


def render(root, kind, identity, host_image):
    decisions = json.loads((root / 'docs/architecture/bootstrap-decisions.json').read_text(encoding='utf-8'))
    selected = project(root, decisions)
    if kind == 'ef-postgresql':
        return render_postgresql(root, identity, selected)
    host = next((p for p in selected['selected_packages'] if p['ecosystem'] == 'oci'), None)
    if not host or host['version'] != '0.2.2':
        raise ValueError('Maintained activation fixture requires selected Foundation 0.2.2; review the fixture for other releases')
    if not isinstance(host_image, str) or not re.fullmatch(re.escape(host['packageId']) + r'@sha256:[0-9a-f]{64}', host_image):
        raise ValueError('Supply --host-image with the registry-verified digest for the selected Foundation tag')
    if decisions.get('toolchain', {}).get('pins', {}).get('dotnet-sdk', '').split('.')[0] != '10':
        raise ValueError('Maintained provider fixtures require the selected .NET 10 toolchain')
    directory = root / 'docs/architecture/compatibility'
    recipe = directory / (identity + '.py')
    config = directory / (identity + '.inputs.json')
    contract = recipe.with_suffix('.contract.json')
    if any(p.exists() for p in (recipe, config, contract)):
        raise ValueError('Recipe already exists; preserve reviewed inputs or use a new identity')
    governance = Path(__file__).resolve().parents[1]
    extensions = governance.parent
    sources = {'runtime-inputs.json': config.relative_to(root).as_posix(),
               'bounded_process.py': (governance / 'scripts/compatibility_process.py').relative_to(root).as_posix()}
    parameters = {'hostImage': host_image, 'foundationRelease': host['version'],
                  'source': selected['publisher_sources']['foundation']['repository'],
                  'license': 'MIT; exact tagged publisher and package license evidence remains in tooling-evaluation.md'}

    def fixture(destination, source):
        if not source.is_file():
            raise ValueError('Maintained provider fixture is missing: ' + str(source))
        sources[destination] = source.relative_to(root).as_posix()

    if kind == 'foundation-activation':
        example = governance / 'examples/bootstrap-runtime'
        for name in ['Core/Core.csproj', 'Core/Port.cs', 'Feature/Feature.csproj', 'Feature/Features.cs',
                     'Boundary/Boundary.csproj', 'Boundary/Program.cs', 'runtime_probe.py']:
            fixture(name, example / name)
        targets = ['Core/Core.csproj', 'Feature/Feature.csproj', 'Boundary/Boundary.csproj']
        entry = 'runtime_probe'
    else:
        if decisions.get('web', {}).get('secure_profile') != 'bff-cookie-v1' or not selected['identity_runtime']:
            raise ValueError('BFF/Keycloak recipe requires that exact selected profile and managed local identity')
        parameters['identityImage'] = selected['identity_runtime']['image']
        parameters['identityLicense'] = 'Apache-2.0; local non-production fixture only'
        example = governance / 'examples/bootstrap-identity'
        for name in ['Probe.csproj', 'Feature.cs', 'browser.mjs', 'identity_probe.py']:
            fixture(name, example / name)
        templates = extensions / 'program-kit-dotnet/templates/dotnet/web-profiles'
        fixture('realm-source.json', templates / 'common/deploy/keycloak/program-kit-realm.json')
        fixture('client-source.json', templates / 'bff-cookie/identity-client.json')
        fixture('shell-source.json', templates / 'bff-cookie/.program-kit/web-profile.shells.json')
        fixture('package.json', templates / 'common/.program-kit/eng/web/package.json')
        theme = templates / 'common/deploy/keycloak/themes'
        for source in sorted(p for p in theme.rglob('*') if p.is_file()):
            fixture('themes/' + source.relative_to(theme).as_posix(), source)
        targets = ['Probe.csproj', 'package.json']
        entry = 'identity_probe'
    directory.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(parameters, indent=2) + '\n', encoding='utf-8')
    recipe.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path.cwd()))\n'
                      + 'from ' + entry + ' import main\nraise SystemExit(main())\n', encoding='utf-8')
    contract.write_text(json.dumps({'schemaVersion': 1, 'checks': [{'id': kind,
        'kind': 'runtime-compatibility', 'testCases': CASES[kind]}], 'fixtures': sources,
        'dependencyTargets': targets}, indent=2) + '\n', encoding='utf-8')
    return {'id': identity, 'recipe': recipe.relative_to(root).as_posix(), 'timeout': 600}


def render_postgresql(root, identity, selected):
    runtime = next((p for p in selected['persistence_runtimes'] if p['profile'] == 'ef-postgresql'), None)
    if not runtime:
        raise ValueError('PostgreSQL recipe requires an explicitly selected ef-postgresql owner')
    directory = root / 'docs/architecture/compatibility'
    recipe = directory / (identity + '.py')
    config = directory / (identity + '.inputs.json')
    project_file = directory / (identity + '.csproj')
    contract = recipe.with_suffix('.contract.json')
    if any(p.exists() for p in (recipe, config, project_file, contract)):
        raise ValueError('Recipe already exists; preserve reviewed inputs or use a new identity')
    governance = Path(__file__).resolve().parents[1]
    fixture = governance / 'examples/bootstrap-postgresql'
    sources = {'runtime-inputs.json': config.relative_to(root).as_posix(),
               'Probe.csproj': project_file.relative_to(root).as_posix()}
    for target, path in {'Program.cs': fixture / 'Program.cs', 'postgresql_probe.py': fixture / 'postgresql_probe.py',
                         'bounded_process.py': governance / 'scripts/compatibility_process.py'}.items():
        if not path.is_file(): raise ValueError('Maintained PostgreSQL fixture missing: ' + str(path))
        sources[target] = path.relative_to(root).as_posix()
    packages = runtime['packages']
    references = ''.join(f'<PackageReference Include="{name}" Version="{packages[name]}" />' for name in
                         ('Microsoft.EntityFrameworkCore', 'Npgsql.EntityFrameworkCore.PostgreSQL'))
    directory.mkdir(parents=True, exist_ok=True)
    project_file.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup>' + references + '</ItemGroup></Project>\n', encoding='utf-8')
    config.write_text(json.dumps(runtime, indent=2) + '\n', encoding='utf-8')
    recipe.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path.cwd()))\nfrom postgresql_probe import main\nraise SystemExit(main())\n', encoding='utf-8')
    contract.write_text(json.dumps({'schemaVersion': 1, 'checks': [{'id': 'ef-postgresql',
        'kind': 'runtime-compatibility', 'testCases': CASES['ef-postgresql']}],
        'fixtures': sources, 'dependencyTargets': ['Probe.csproj']}, indent=2) + '\n', encoding='utf-8')
    return {'id': identity, 'recipe': recipe.relative_to(root).as_posix(), 'timeout': 600}
