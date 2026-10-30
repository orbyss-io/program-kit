"""F5 retained fictional application; real current native features/provider/HTTP/browser. No agent."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'scripts'),
               str(ROOT / 'extensions/program-kit-building-blocks/scripts')]
import building_blocks as blocks
from live.v2.postgresql_service import PostgreSqlService
from live.v2.supervisor import run_supervised
from live.v2.cli import supervisor_environment
from run_validation import input_snapshot

EXAMPLE = ROOT / 'extensions/program-kit-dotnet/references/examples/evidence-submission'
FIXTURE = ROOT / 'tests/fixtures/evidence-submission'
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
        return
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def projects(work, catalog):
    foundation = catalog['families']['foundation']['releaseVersion']
    shared = blocks.effective_dependency_context(ROOT)['sharedAbi']['pins']
    persistence = ET.parse(TEMPLATE / 'config/program-kit/build/profiles/persistence/ProgramKit.Persistence.EfPostgreSql.props')
    pins = {row.get('Include'): row.get('Version') for row in persistence.iter('PackageVersion')}
    packages = {
        'Core': {},
        'Runtime': {'CShells.Abstractions': shared['CShells.Abstractions']},
        'PostgreSql': {'CShells.Abstractions': shared['CShells.Abstractions'], 'Orbyss.Foundation.Json': foundation,
                      'Microsoft.EntityFrameworkCore': pins['Microsoft.EntityFrameworkCore'],
                      'Npgsql.EntityFrameworkCore.PostgreSQL': pins['Npgsql.EntityFrameworkCore.PostgreSQL']},
        'Api': {'CShells.AspNetCore.Abstractions': shared['CShells.AspNetCore.Abstractions'],
                'Orbyss.Foundation.Json.AspNetCore': foundation},
        'Probe': {'CShells.AspNetCore': shared['CShells.AspNetCore.Abstractions'],
                  'CShells.Abstractions': shared['CShells.Abstractions'],
                  'CShells.AspNetCore.Abstractions': shared['CShells.AspNetCore.Abstractions'],
                  'Orbyss.Foundation.WebDefaults': foundation, 'Orbyss.Foundation.Web.ProblemDetails': foundation,
                  'Orbyss.Foundation.Web.OpenApi': foundation},
    }
    for role, dependencies in packages.items():
        directory = work / ('tests/Probe' if role == 'Probe' else 'src/' + role)
        source = FIXTURE if role == 'Probe' else EXAMPLE / role
        directory.mkdir(parents=True)
        for path in source.glob('*.cs'):
            shutil.copyfile(path, directory / path.name)
        references = ['Core'] if role not in ('Core', 'Probe') else ['Core', 'Runtime', 'Api', 'PostgreSql'] if role == 'Probe' else []
        project_references = ''.join('<ProjectReference Include="' + str(work / 'src' / name / ('Evidence.' + name + '.csproj')) + '" />' for name in references)
        package_references = ''.join('<PackageReference Include="' + name + '" Version="' + version + '" />' for name, version in dependencies.items())
        sdk = 'Microsoft.NET.Sdk.Web' if role == 'Probe' else 'Microsoft.NET.Sdk'
        properties = '<TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally><RestorePackagesWithLockFile>true</RestorePackagesWithLockFile><NuGetAudit>false</NuGetAudit>'
        if role == 'Probe': properties += '<AssemblyName>Evidence.Probe</AssemblyName>'
        framework = '<FrameworkReference Include="Microsoft.AspNetCore.App" />' if role not in ('Core', 'Probe') else ''
        if role != 'Probe':
            analyzer = catalog['packages']['nuget:Orbyss.Foundation.Analyzers']['version']
            dependencies['Orbyss.Foundation.Analyzers'] = analyzer
            package_references += '<PackageReference Include="Orbyss.Foundation.Analyzers" Version="' + analyzer + '" PrivateAssets="all" />'
            properties += '<GenerateDocumentationFile>true</GenerateDocumentationFile><TreatWarningsAsErrors>true</TreatWarningsAsErrors>'
        write(directory / ('Evidence.' + role + '.csproj'), '<Project Sdk="' + sdk + '"><PropertyGroup>' + properties + '</PropertyGroup><ItemGroup>' + project_references + package_references + framework + '</ItemGroup></Project>')
    return packages


def prepare_web(work, registry, entry):
    web = work / 'web'
    shutil.copytree(EXAMPLE / 'web', web, ignore=shutil.ignore_patterns('*.ts'))
    for name, source in {
        'file-selection.mjs': ROOT / 'extensions/program-kit-governance/references/file-selection-example.mjs',
        'operation-recovery.mjs': ROOT / 'extensions/program-kit-governance/references/operation-recovery-example.mjs',
        'interactions.mjs': ROOT / 'extensions/program-kit-governance/templates/ui-experience/interactions.mjs',
        'native.css': TEMPLATE.parent / 'hosted-pages/web/src/styles.css',
    }.items(): shutil.copyfile(source, web / name)
    knowledge = blocks.load_json(registry / entry['knowledge']['path'])
    native = web / 'native'; native.mkdir()
    provenance = []
    for name in ('presentation.mjs', 'session.mjs', 'bff.mjs', 'configuration.mjs'):
        path = 'src/Orbyss.Foundation.Web.Presentation/browser/' + name
        row = next(row for row in knowledge['documents'] if row['publisherPath'] == path)
        raw = blocks.publisher_document_bytes(registry, row)
        if hashlib.sha256(raw).hexdigest() != row['sha256']: raise ValueError('Selected native module differs')
        (native / name).write_bytes(raw); provenance.append(row)
    write(work / 'native-module-provenance.json', provenance)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--native-only', action='store_true')
    parser.add_argument('--mutations', action='store_true', help='Compile and execute independent invalid controls; preserve every source snapshot and expected failure')
    parser.add_argument('--engines', default='chromium,webkit' if os.name == 'nt' else 'chromium,firefox,webkit')
    parser.add_argument('--browser-root', type=Path, help='Explicit existing exact selected Playwright/axe package graph; no installation')
    parser.add_argument('--client-tools-root', type=Path, default=ROOT / 'artifacts/cache/f5-client-tools', help='Prepared selected generator/compiler packages; versions are independently admitted, no installation')
    args = parser.parse_args()
    engines = args.engines.split(',')
    if not engines or len(set(engines)) != len(engines) or set(engines) - {'chromium', 'webkit', 'firefox'}: parser.error('Select distinct supported engines')
    identity = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6]
    review = ROOT / 'artifacts/f5-review' / identity
    work = ROOT / 'artifacts/t' / ('f5-' + uuid.uuid4().hex[:8])
    work.mkdir(parents=True); review.mkdir(parents=True)
    catalog = blocks.new_project_catalog(); registry = blocks.profile_registry(); index = blocks.load_json(registry / 'index.json')
    entry = index['profiles'][index['default']]
    result = {'status': 'running', 'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'workingInputsDigest': input_snapshot()['digest'], 'profile': index['default'], 'consumer': str(work),
              'fixtureHash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'commands': [],
              'limits': ['Fictional identity/session projections; no real authentication/provider/account acceptance.', 'No Firefox claim without an actual supported run.', 'PostgreSQL results do not qualify other providers.', 'No worker, paid operation or stopped consumer.']}
    write(review / 'results.json', result)
    write(review / 'index.md', '# F5 incomplete retained run\n\nInspect [results](results.json). No success or human acceptance is inferred.\n')
    started = time.monotonic()
    environment = supervisor_environment()
    environment['NUGET_PACKAGES'] = str(Path.home() / '.nuget/packages')
    environment['F5_NODE'] = shutil.which('node') or 'node'
    def run(name, command, *, env=None, secrets=(), expected=0, marker=None):
        directory = review / 'output' / name
        before = time.monotonic()
        process = run_supervised(list(map(str, command)), cwd=work, environment=env or environment,
                                 evidence_directory=directory, timeout_seconds=180, secrets=list(secrets))
        write(directory / 'process.json', process.as_dict())
        result['commands'].append({'name':name, 'command': list(map(str, command)), 'expectedExit':expected,
                                   'actualExit':process.exitCode, 'seconds':round(time.monotonic()-before,3), 'process':process.as_dict()})
        write(review / 'results.json', result)
        exit_matches = process.exitCode != 0 if expected == 'nonzero' else process.exitCode == expected
        if not exit_matches or process.timedOut or not process.cleanupComplete or not process.logsDrained:
            raise RuntimeError(name + ' failed; inspect ' + str(directory))
        if marker and marker not in (directory / process.stderr.path).read_text(encoding='utf-8'):
            raise RuntimeError(name + ' failed for an unrelated cause; inspect ' + str(directory))
        return (directory / process.stdout.path).read_text(encoding='utf-8')
    try:
        result['selectedPackages'] = projects(work, catalog)
        shutil.copyfile(TEMPLATE / 'global.json', work / 'global.json')
        shutil.copyfile(TEMPLATE / 'NuGet.config', work / 'NuGet.config')
        shutil.copyfile(FIXTURE / 'accepted-model.json', work / 'accepted-model.json')
        prepare_web(work, registry, entry)
        if args.prepare_only:
            result['status'] = 'prepared'; write(review / 'results.json', result); print(work); print(review); return
        project = work / 'tests/Probe/Evidence.Probe.csproj'
        run('restore', ['dotnet', 'restore', project, '--use-lock-file'])
        run('build', ['dotnet', 'build', project, '--no-restore', '-m:1', '--verbosity', 'quiet'])
        executable = work / 'tests/Probe/bin/Debug/net10.0/Evidence.Probe.dll'
        if not args.native_only:
            browser_root = args.browser_root or ROOT / 'artifacts/cache/f5-browser'
            packages = {name: blocks.load_json(browser_root / 'node_modules' / name / 'package.json')['version'] for name in ('playwright', '@axe-core/playwright')}
            selected = blocks.load_json(ROOT / 'extensions/program-kit-governance/templates/ui-experience/acceptance/package.json')['devDependencies']
            if packages != {'playwright':selected['@playwright/test'], '@axe-core/playwright':selected['@axe-core/playwright']}: raise ValueError('Prepared browser graph differs from selected package versions')
            script = (FIXTURE / 'browser.mjs').read_text()
            script = script.replace('__PLAYWRIGHT__', (browser_root / 'node_modules/playwright/index.mjs').as_uri())
            script = script.replace('__AXE__', (browser_root / 'node_modules/@axe-core/playwright/dist/index.mjs').as_uri())
            write(work / 'browser.mjs', script); result['browserPackages'] = packages
            result['browserLockSha256'] = hashlib.sha256((browser_root / 'package-lock.json').read_bytes()).hexdigest()
            result['browserCache'] = environment.get('PLAYWRIGHT_BROWSERS_PATH', 'operator default cache')
            generator = args.client_tools_root / 'generator/node_modules/openapi-typescript'
            compiler = args.client_tools_root / 'compiler/node_modules/typescript'
            selected_generator = blocks.load_json(TEMPLATE / 'scripts/openapi-defaults.json')['typescriptGenerator']
            selected_compiler = blocks.load_json(TEMPLATE.parent / 'web-profiles/common/tools/program-kit/web/package.json')['devDependencies']['typescript']
            if blocks.load_json(generator / 'package.json')['version'] != selected_generator['version'] or blocks.load_json(compiler / 'package.json')['version'] != selected_compiler:
                raise ValueError('Prepared native generator/compiler differs from selected inputs')
            result['clientTools'] = {'generator':selected_generator,'typescript':selected_compiler}
            result['clientToolLocks'] = {role:hashlib.sha256((args.client_tools_root / role / 'package-lock.json').read_bytes()).hexdigest() for role in ('generator','compiler')}
            source = work / 'client-source'; source.mkdir()
            shutil.copyfile(EXAMPLE / 'web/client.ts', source / 'client.ts')
            script = script.replace('__OPENAPI_TYPESCRIPT__', str(generator / 'bin/cli.js').replace('\\','/'))
            script = script.replace('__TYPESCRIPT__', str(compiler / 'bin/tsc').replace('\\','/'))
            write(work / 'browser.mjs', script)
        contract = blocks.load_json(ROOT / 'tests/live/scenarios/knowledge-application/v1/bootstrap-seed/fixture/acceptance/services.json')
        # Runtime image follows the maintained current persistence owner, not the historical specimen.
        runtime = blocks.load_json(ROOT / 'extensions/program-kit-dotnet/references/persistence-runtimes.json')['profiles']['ef-postgresql']
        contract['image'] = runtime['image']
        with PostgreSqlService(contract, work, review / 'database', environment) as database:
            schema = (FIXTURE / 'schema.sql').read_text()
            database.command(['exec', database.container, 'psql', '-U', 'fixture', '-d', 'lending', '-v', 'ON_ERROR_STOP=1', '-c', schema], 'explicit-fixture-deployment')
            connection = database.connection().replace('Username=fixture;', 'Username=evidence_runtime;').replace(database.password, 'fictional-fixture-only')
            env = {**environment, 'F5_CONNECTION':connection}
            command = ['dotnet', executable, work]
            if not args.native_only: command += [work / 'browser.mjs', args.engines]
            run('actual-application', command, env=env, secrets=[database.password, connection])
            observation = database.command(['exec', database.container, 'psql', '-U', 'fixture', '-d', 'lending', '-Atc',
                "SELECT packet->>'title', accepted, revision, packet->>'hash' FROM evidence.entries ORDER BY identity"], 'independent-sql-observation')
            observed = (review / 'database/independent-sql-observation' / observation.stdout.path).read_text()
            native_hash = hashlib.sha256(b'fictional evidence').hexdigest()
            if 'Native evidence|t|1|' + native_hash not in observed: raise AssertionError('Replay repeated or lost the native effect or JSON content')
            result['independentSql'] = observed.splitlines()
            if not args.native_only:
                browser_hash = hashlib.sha256(b'fictional browser evidence').hexdigest()
                for engine in engines:
                    if 'Browser evidence ' + engine + '|t|1|' + browser_hash not in observed:
                        raise AssertionError('Browser effect/replay or immutable content differs from one acceptance')
            if args.mutations:
                controls = [
                    ('model-drift','src/PostgreSql/EvidenceDbContext.cs','ToTable("entries", "evidence")','ToTable("wrong_entries", "evidence")','independent-accepted-table-authority'),
                    ('captive-registration','src/Runtime/EvidenceRuntimeFeature.cs','AddScoped<IEvidenceSubmissions','AddSingleton<IEvidenceSubmissions','actual-feature-request-scopes-are-independent'),
                    ('missing-registration','src/Runtime/EvidenceRuntimeFeature.cs','services.AddScoped<IEvidenceSubmissions, EvidenceSubmissions>()','_ = services','actual-runtime-registration'),
                    ('root-only-options','src/Api/EvidenceApiFeature.cs','services.AddShellInitializer<EvidenceOptionsAdmission>(LifecyclePhase.Prepare, 0);','// removed activation admission','invalid options admitted an active shell'),
                    ('omitted-effect','src/PostgreSql/PostgreSqlEvidenceJournal.cs','AND NOT {accepted}"','AND NOT {accepted} AND FALSE"','actual-provider-json-and-business-acceptance'),
                    ('owner-bypass','src/PostgreSql/PostgreSqlEvidenceJournal.cs',' && entry.Owner == owner','','provider-owner-query-isolation'),
                    ('middleware-order','tests/Probe/FixtureBoundaryFeature.cs','Order => -700','Order => -1300','native-headers-cover-denial'),
                ]
                result['negativeControls'] = []
                for name, relative, before, after, marker in controls:
                    path = work / relative; original = path.read_bytes()
                    if before.encode() not in original: raise AssertionError('Independent mutation has no exact source precondition: '+name)
                    write(review / 'snapshots' / 'valid-before' / relative, original)
                    write(review / 'snapshots' / name / relative, original.replace(before.encode(), after.encode()))
                    try:
                        path.write_bytes(original.replace(before.encode(), after.encode()))
                        run(name+'-compile',['dotnet','build',project,'--no-restore','-m:1','--verbosity','quiet'])
                        run(name+'-behavior',['dotnet',executable,work],env={**env,'F5_CASE_LABEL':'Negative '+name},
                            secrets=[database.password,connection],expected='nonzero',marker=marker)
                        result['negativeControls'].append({'name':name,'expectedFailure':marker,'compiled':True,'observed':True})
                    finally:
                        path.write_bytes(original)
                        write(review / 'snapshots' / 'valid-restored' / relative, original)
                run('restore-valid-build',['dotnet','build',project,'--no-restore','-m:1','--verbosity','quiet'])
        if not args.native_only:
            from evidence_context_review import scenario
            scenario(work, review, result)
        result['status'] = 'passed'
        result['elapsedSeconds'] = round(time.monotonic()-started,3)
        result['sourceChangedDuringRun'] = input_snapshot()['digest'] != result['workingInputsDigest']
        if result['sourceChangedDuringRun']: raise AssertionError('Source changed during proof')
        write(review / 'results.json', result)
        relative = os.path.relpath(work, review).replace('\\','/')
        write(review / 'index.md', '# F5 evidence desk: actual-output review\n\nFictional product/identity; real selected native features, application, PostgreSQL and browser execution.\n\n'
              + '1. Inspect [source](' + relative + '/src), [accepted model](' + relative + '/accepted-model.json) and [native assertions](' + relative + '/native-result.json).\n'
              + '2. Inspect [actual process](output/actual-application/process.json) and both retained streams.\n'
              + '3. Compare [independent SQL](database/independent-sql-observation/workflow.stdout.log) with the actual response/retained identity. Each accepted row has revision 1.\n'
              + ('4. Inspect [browser results](' + relative + '/browser-result.json), [generated types](' + relative + '/client-source/types.ts), the served compiled client and rendered desktop/mobile screens beside them. Human visual review remains due. Read [installed context results](context-results.json) for initial rejection, actual observation check, qualified selection, unrelated exclusion and stale-source rejection/restoration.\n' if not args.native_only else '4. Inspect [invalid and restored source](snapshots) and each compiled negative control in the results. This run makes no browser claim.\n')
              + '5. Read [results](results.json) for exact source/profile/packages, commands, timing and limits. Retain this consumer and every failed run.\n')
        print('F5 retained review: ' + str(review / 'index.md'))
    except BaseException as error:
        result.update(status='failed', failure=type(error).__name__, elapsedSeconds=round(time.monotonic()-started,3))
        write(review / 'results.json', result)
        print('F5 failed run retained: ' + str(review), file=sys.stderr)
        raise


if __name__ == '__main__': main()
