"""Versioned Notes preparation and independent real-package/Host/PostgreSQL oracle.

The default/self-test is deterministic source/negative-fixture validation. --prepare
restores/builds/packs explicitly selected private candidates. --qualify additionally
requires preserved successful F6 evidence and an explicitly disposable PostgreSQL
database; it starts no coding agent and writes no actual consumer repository.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/foundation-consumer-contracts/notes/v1'
SCENARIO = ROOT / 'tests/live/scenarios/foundation-notes/v1'
RECIPE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py'
ORACLE_SCENARIO = 'foundation-notes-v1'
PROJECTS = ('Notes.Core', 'Notes', 'Notes.Api', 'Notes.PostgreSql')
FIXTURE_VERSION = '1.0.0-fixture.1'
HOST_CONTRACT_PACKAGES = {'cshells.abstractions', 'cshells.aspnetcore.abstractions'}
BEHAVIOR_SEEDS = ('private-claim-parsing', 'profile-bypass', 'shared-concurrent-context', 'programming-error-400', 'inconsistent-envelope')
GRAPH_SEEDS = {'merged-roles': 'Binding capability must have a Core role:',
               'missing-bindings': 'Unlisted active capability binding:'}


def seed_cases():
    def shared_context(text):
        field = '''
    private readonly Lazy<Task<(PostgreSqlUnitLease<NotesDbContext> Unit, NotesDbContext Db)>> shared = new(async () =>
    {
        var unit = await units.BeginUnitAsync(CancellationToken.None);
        var db = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        return (unit, db);
    });
'''
        text = text.replace(': INoteQueries\n{', ': INoteQueries\n{' + field)
        return text.replace('await using var unit = await units.BeginUnitAsync(cancellationToken);\n            await using var db = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);',
            'var cached = await shared.Value;\n            var unit = cached.Unit;\n            var db = cached.Db;\n            await db.Database.ExecuteSqlRawAsync("SELECT pg_sleep(0.15)", unit.Deadline.Token);', 1)
    return {
        'merged-roles': ('eng/architecture.json', lambda text: text.replace('"role":"core"', '"role":"provider"')),
        'missing-bindings': ('eng/architecture.json', lambda text: json.dumps({**json.loads(text), 'runtimeComposition': {
            **json.loads(text)['runtimeComposition'], 'bindings': json.loads(text)['runtimeComposition']['bindings'][1:]}})),
        'private-claim-parsing': ('src/Notes.Api/NoteOwnerAdapter.cs', lambda text: text.replace('return new(identity.Issuer, identity.Subject);',
            'return new(http.User.FindFirst("iss")!.Value, http.User.FindFirst("sub")!.Value);')),
        'profile-bypass': ('src/Notes.Api/CreateNote/CreateNoteEndpoint.cs', lambda text: text.replace(
            'responses.Create(new(value.OperationId, NoteWire.From(value.Note)))',
            'Results.Ok(new CreateNoteResponse(value.OperationId, NoteWire.From(value.Note)))').replace(
            'var packet = await requests.ReadAsync', '_ = responses;\n        var packet = await requests.ReadAsync')),
        'shared-concurrent-context': ('src/Notes.PostgreSql/NoteQueries.cs', shared_context),
        'programming-error-400': ('src/Notes.Api/ReadNote/ReadNoteEndpoint.cs', lambda text: text.replace(
            'var result = await queries.ReadAsync(owners.Read(http), noteId, http.RequestAborted);',
            'NoteOutcome<NoteSnapshot> result; try { result = await queries.ReadAsync(owners.Read(http), noteId, http.RequestAborted); } catch (ArgumentException) { return FoundationProblemResults.Problem(new ProblemDefinition(400, "note_bad_input")); }')),
        'inconsistent-envelope': ('src/Notes.Api/CreateNote/CreateNoteEndpoint.cs', lambda text: text.replace(
            'FoundationProblemResults.Problem(problems.Map(result.Failure!.Value))', 'Microsoft.AspNetCore.Http.Results.Json(new { error = result.Failure!.Value.ToString() }, statusCode: 409)').replace(
            'var packet = await requests.ReadAsync', '_ = problems;\n        var packet = await requests.ReadAsync')),
        'deadline-reset': ('src/Notes.PostgreSql/NoteRevisionLifecycle.cs', lambda text: text.replace('units.BeginUnitAsync(caller, outer)', 'units.BeginUnitAsync(caller)')),
    }


def apply_seed(source: Path, name: str) -> None:
    relative, mutate = seed_cases()[name]
    path = source / relative
    original = path.read_text(encoding='utf-8')
    changed = mutate(original)
    require(changed != original, 'Negative seed did not change its source: ' + name)
    path.write_text(changed, encoding='utf-8')


def require(value, message):
    if not value:
        raise AssertionError(message)


def recipe():
    sys.path.insert(0, str(RECIPE.parent))
    specification = importlib.util.spec_from_file_location('notes_repository_architecture', RECIPE)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_source(source: Path) -> None:
    manifest = json.loads((source / 'eng/architecture.json').read_text(encoding='utf-8'))
    recipe().validate_planned(source, manifest)
    bindings = manifest['runtimeComposition']['bindings']
    require({row['capability'] for row in bindings} == {'Notes.Core.INoteAuthoring', 'Notes.Core.INoteRevisionLifecycle', 'Notes.Core.INoteQueries'},
            'Notes has a missing active semantic binding.')
    for project in source.rglob('*.csproj'):
        for reference in ET.parse(project).iter('ProjectReference'):
            target = (project.parent / reference.attrib['Include']).resolve()
            require(target.is_relative_to(source.resolve()), 'Foundation source ProjectReference is forbidden; consume the candidate packages.')
        if project.parent.name == 'Notes.Core':
            require(not list(ET.parse(project).iter('PackageReference')), 'Notes Core must remain framework/provider free.')
    api = source / 'src/Notes.Api'
    api_text = '\n'.join(path.read_text(encoding='utf-8') for path in api.rglob('*.cs'))
    require('IValidatedAccountIdentityReader' in api_text and '.TryRead(http.User' in api_text, 'Notes must use the public validated identity admission seam.')
    owner_adaptation = '\n'.join(path.read_text(encoding='utf-8') for path in (source / 'src/Notes.Api').rglob('*.cs')
                                 if path.name != 'FixtureAuthenticationAliases.cs')
    require(not re.search(r'FindFirst|FindAll|urn:orbyss|"iss"|"sub"', owner_adaptation), 'Private claim parsing is forbidden in Notes adaptation.')
    fixture_aliases = source / 'src/Notes.Api/FixtureAuthenticationAliases.cs'
    require(not re.search(r'FindFirst|FindAll|urn:orbyss', fixture_aliases.read_text(encoding='utf-8')),
            'Native fixture claim actions cannot implement private owner admission.')
    require('Results.Ok' not in api_text and 'WriteAsJsonAsync' not in api_text and 'Response.Body' not in api_text,
            'Notes response-profile bypass must be rejected.')
    for operation in ('CreateNote', 'ReadNote', 'RenameNote', 'ListNotes'):
        text = (api / operation / (operation + 'Endpoint.cs')).read_text(encoding='utf-8')
        require('IJsonResponseFactory<' in text and 'responses.Create(' in text, 'Each Notes success operation needs its admitted typed result.')
        require('FoundationProblemResults.Problem(problems.Map(' in text, 'Notes failures must use the shared problem representation.')
    require('IOptions<FoundationJsonOptions>' in api_text and '.Paging.Admit(size)' in api_text, 'Page count admission must use the actual configured JSON settings.')
    provider = source / 'src/Notes.PostgreSql'
    provider_text = '\n'.join(path.read_text(encoding='utf-8') for path in provider.rglob('*.cs'))
    require(not re.search(r'(?:private|public|internal)\s+(?:readonly\s+)?NotesDbContext\s+\w+\s*[;=]', provider_text),
            'A shared concurrent context is forbidden; independent tracked factory units are required.')
    require(not re.search(r'NoteQueries\([^)]*\bNotesDbContext\s+\w+', provider_text),
            'A singleton Notes query implementation cannot capture a shared concurrent context.')
    require('Lazy<Task<(PostgreSqlUnitLease<NotesDbContext> Unit, NotesDbContext Db)>>' not in provider_text,
            'A singleton cannot retain its factory context for concurrent queries.')
    require('await using var reconciliation = await units.BeginUnitAsync(caller, outer)' in provider_text,
            'Receipt reconciliation needs a distinct tracked unit with the same outer deadline.')
    require('await using var db = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token)' in provider_text,
            'Contexts must use the admitted factory and owned deadline.')
    require(not re.search(r'catch\s*\(\s*(?:ArgumentException|Exception)(?:\s+\w+)?\s*\)\s*\{', api_text + provider_text),
            'Broad programming-error mapping is forbidden.')
    require('Take(checked(size + 1))' in provider_text and 'row.Issuer == owner.Issuer' in provider_text and 'row.Subject == owner.Subject' in provider_text,
            'Page reads must stay bounded and owner filtered.')
    require('commitStarted = true;' in provider_text and 'NoteFailure.Uncertain' in provider_text,
            'Commit cancellation must not imply proven rollback.')
    oracle = source / 'oracle/NotesBehaviorOracle.cs'
    require(oracle.is_file() and 'NpgsqlConnection' in oracle.read_text(encoding='utf-8'), 'The Notes-specific actual PostgreSQL oracle is missing.')


def self_test() -> None:
    validate_source(FIXTURE)
    cases = seed_cases()
    for name, (relative, mutate) in cases.items():
        with tempfile.TemporaryDirectory(prefix='notes-negative-') as temporary:
            source = Path(temporary) / 'fixture'
            shutil.copytree(FIXTURE, source, ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__'))
            apply_seed(source, name)
            try:
                validate_source(source)
            except (AssertionError, ValueError):
                pass
            else:
                raise AssertionError('Seeded violation was accepted: ' + name)
    specification = importlib.util.spec_from_file_location('notes_adapter', SCENARIO / 'oracle_adapter.py')
    adapter = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(adapter)
    require(adapter.load_notes_oracle(ROOT).ORACLE_SCENARIO == ORACLE_SCENARIO, 'Notes scenario selected another oracle.')
    with tempfile.TemporaryDirectory(prefix='notes-missing-oracle-') as temporary:
        try:
            adapter.load_notes_oracle(Path(temporary))
        except RuntimeError as error:
            require('missing' in str(error), 'Missing oracle diagnostic was unclear.')
        else:
            raise AssertionError('Scenario accepted a missing Notes-specific oracle.')
    print('Notes source preparation passed; eight seeded violations and missing scenario oracle fail closed. No Host/PostgreSQL qualification is claimed.')


def run(command: list[str], cwd: Path, log: Path, environment=None) -> None:
    with log.open('w', encoding='utf-8') as output:
        output.write(json.dumps(command) + '\n')
        output.flush()
        result = subprocess.run(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, env=environment, timeout=300)
    require(result.returncode == 0, f'Command failed ({result.returncode}); preserved output: {log}')


def write_descriptors(source: Path) -> None:
    for name in PROJECTS[1:]:
        directory = source / 'src' / name
        descriptor = json.loads((directory / 'feature.json').read_text(encoding='utf-8'))
        descriptor['sourceSha256'] = {path.relative_to(directory).as_posix(): hashlib.sha256(
            path.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode()).hexdigest()
            for path in sorted(directory.rglob('*.cs')) if not {'obj', 'bin'} & set(path.parts)}
        descriptor['hostProvidedDependencies'] = [{'packageId': 'CShells.Abstractions', 'minimumVersion': '0.0.29-preview.147'}]
        if name == 'Notes.Api':
            descriptor['hostProvidedDependencies'].append({'packageId': 'CShells.AspNetCore.Abstractions', 'minimumVersion': '0.0.29-preview.147'})
        (directory / 'feature.json').write_text(json.dumps(descriptor, indent=2) + '\n', encoding='utf-8')


def prepare(args) -> tuple[Path, Path]:
    require(args.packages and args.version, '--prepare requires an explicit private candidate feed and exact version.')
    packages = Path(args.packages).resolve()
    require(packages.is_dir(), 'The candidate feed is unreadable.')
    require((packages / f'Orbyss.Foundation.PostgreSql.{args.version}.nupkg').is_file(), 'The exact candidate PostgreSql package is missing.')
    evidence = (Path(args.evidence_directory).resolve() if args.evidence_directory else
                ROOT / 'artifacts/foundation-notes' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]))
    require(evidence.is_relative_to(ROOT / 'artifacts') and not evidence.exists(),
            'Notes evidence must use a new owned artifacts directory; preserved runs cannot be overwritten.')
    evidence.mkdir(parents=True)
    source = evidence / 'source'
    shutil.copytree(FIXTURE, source, ignore=shutil.ignore_patterns('obj', 'bin', '__pycache__'))
    if args.behavior_seed or args.graph_seed:
        apply_seed(source, args.behavior_seed or args.graph_seed)
    feed = evidence / 'packages'
    shutil.copytree(packages, feed)
    write_descriptors(source)
    configuration_path = Path(args.nuget_config).resolve() if args.nuget_config else FIXTURE / 'NuGet.config'
    configuration = ET.parse(configuration_path)
    package_sources = configuration.getroot().find('packageSources')
    require(package_sources is not None, 'An explicit dependency NuGet configuration must declare package sources.')
    ET.SubElement(package_sources, 'add', key='private-candidate', value=str(feed))
    mappings = configuration.getroot().find('packageSourceMapping')
    if mappings is None:
        mappings = ET.SubElement(configuration.getroot(), 'packageSourceMapping')
        for selected in package_sources.findall('add'):
            if selected.get('key') != 'private-candidate':
                node = ET.SubElement(mappings, 'packageSource', key=selected.get('key'))
                ET.SubElement(node, 'package', pattern='*')
    local = ET.SubElement(mappings, 'packageSource', key='private-candidate')
    ET.SubElement(local, 'package', pattern='Orbyss.Foundation.*')
    ET.SubElement(local, 'package', pattern='Notes*')
    # Build is independently published tooling at the unchanged public baseline.
    # The runtime candidate feed deliberately excludes it.
    public = next((node for node in mappings.findall('packageSource') if node.get('key') == 'nuget.org'), None)
    require(public is not None, 'The explicit dependency configuration must retain the published public tooling source.')
    ET.SubElement(public, 'package', pattern='Orbyss.Foundation.Build')
    configuration.write(source / 'NuGet.config', encoding='utf-8', xml_declaration=True)
    selection = '-p:FoundationCandidateVersion=' + args.version
    cwd = Path(args.sdk_working_directory).resolve() if args.sdk_working_directory else ROOT
    environment = os.environ.copy()
    environment['NUGET_PACKAGES'] = str(evidence / 'package-cache')
    run([args.dotnet, '--version'], cwd, evidence / 'sdk.log', environment)
    run([args.dotnet, 'restore', str(source / 'Notes.slnx'), selection, '--configfile', str(source / 'NuGet.config'), '--force-evaluate'], cwd, evidence / 'restore.log', environment)
    run([args.dotnet, 'restore', str(source / 'Notes.slnx'), selection, '--configfile', str(source / 'NuGet.config'), '--locked-mode'], cwd, evidence / 'locked-restore.log', environment)
    run([args.dotnet, 'build', str(source / 'Notes.slnx'), '-c', 'Release', '--no-restore', selection], cwd, evidence / 'build.log', environment)
    architecture_environment = environment.copy()
    architecture_environment['PATH'] = str(Path(args.dotnet).resolve().parent) + os.pathsep + architecture_environment.get('PATH', '') if Path(args.dotnet).is_file() else architecture_environment.get('PATH', '')
    architecture_environment['FoundationCandidateVersion'] = args.version
    architecture_command = [sys.executable, str(RECIPE), '--manifest', 'eng/architecture.json', '--configuration', 'Release', '--output', 'artifacts/architecture.xml']
    if args.graph_seed:
        with (evidence / 'architecture.log').open('w', encoding='utf-8') as output:
            result = subprocess.run(architecture_command, cwd=source, env=architecture_environment,
                                    stdout=output, stderr=subprocess.STDOUT, timeout=300)
        diagnostic = (evidence / 'architecture.log').read_text(encoding='utf-8')
        require(result.returncode == 2 and GRAPH_SEEDS[args.graph_seed] in diagnostic,
                'Actual compiled/evaluated graph did not reject the intended violation.')
        (evidence / 'result.json').write_text(json.dumps({'status': 'rejected', 'graphSeed': args.graph_seed,
            'actualCompilation': True, 'actualEvaluatedArchitecture': True, 'actualHttp': False,
            'version': args.version, 'qualificationClaimed': False,
            'sourceHashes': {path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in sorted(source.rglob('*')) if path.is_file() and path.suffix in ('.cs', '.csproj', '.json')
                             and not {'bin', 'obj'} & set(path.parts)}} , indent=2) + '\n', encoding='utf-8')
        print('Actual compiled Notes graph seed rejected: ' + str(evidence))
        return evidence, source
    run(architecture_command, source, evidence / 'architecture.log', architecture_environment)
    for name in PROJECTS:
        run([args.dotnet, 'pack', str(source / 'src' / name / (name + '.csproj')), '-c', 'Release', '--no-build', '--no-restore', selection,
             '--output', str(feed)], cwd, evidence / (name + '-pack.log'), environment)
    with zipfile.ZipFile(feed / f'Notes.Core.{FIXTURE_VERSION}.nupkg') as archive:
        require('orbyss-foundation/feature.json' not in archive.namelist(), 'A contract-only assembly was advertised as a feature.')
    manifest = {'scenario': ORACLE_SCENARIO, 'status': 'prepared', 'foundationVersion': args.version,
        'behaviorSeed': args.behavior_seed,
        'executedSourceHashes': {path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted(source.rglob('*.cs')) if not {'bin', 'obj'} & set(path.parts)},
        'sdkWorkingDirectory': str(cwd), 'sourceProjectReferencesToFoundation': False,
        'packageHashes': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(feed.glob('*.nupkg'))},
        'fixtureHashes': {path.relative_to(FIXTURE).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sorted(FIXTURE.rglob('*')) if path.is_file() and not {'bin', 'obj', '__pycache__'} & set(path.parts)}}
    (evidence / 'inputs.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Notes exact candidate restore/build/compiled boundaries/private pack prepared: ' + str(evidence))
    return evidence, source


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def settings(issuer: str) -> dict:
    bundle = json.loads((FIXTURE / 'bundle.json').read_text(encoding='utf-8'))
    return {'CShells': {'Shells': {'default': {'Features': {name: True for name in bundle['features']}, 'Configuration': {'Foundation': {
        'Web': {'Authority': issuer, 'ClientId': 'notes-fixture', 'ClientSecret': 'disposable-fixture-only', 'Audience': 'notes-fixture',
                'Scopes': ['openid'], 'AllowHttpForLocalDevelopment': True},
        'Json': {'Profiles': {'strict-request': {'Preset': 'strict-request', 'MaxBytes': 2097152, 'MaxDepth': 32},
                             'success-response': {'Preset': 'tolerant-response', 'MaxBytes': 1048576, 'MaxDepth': 32},
                             'problem-response': {'Preset': 'tolerant-response', 'MaxBytes': 65536, 'MaxDepth': 8}},
                 'Paging': {'DefaultSize': 100, 'MaximumSize': 500}},
        'PostgreSql': {'Policies': {'notes': {'OperationTimeout': '00:00:10', 'ConnectionTimeout': '00:00:02',
            'CommandTimeout': '00:00:05', 'LockTimeout': '00:00:01', 'CancellationTimeout': '00:00:02'}}}
    }}}}}}


def wait_ready(address: str, process, log: Path):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        require(process.poll() is None, 'A fixture process exited; see ' + str(log))
        try:
            with urllib.request.urlopen(address, timeout=1) as response:
                if response.status < 500:
                    return
        except urllib.error.HTTPError as error:
            if error.code < 500:
                return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.2)
    raise AssertionError('A fixture process did not become ready; see ' + str(log))


def qualify(args, evidence: Path, source: Path) -> None:
    require(args.f6_evidence and args.host, 'Actual Notes qualification requires successful F6 evidence and the matching actual Host DLL.')
    require(args.development_profile and args.profile_identity,
            'Actual Notes qualification requires an explicitly selected PK2A development profile; there is no development default.')
    f6 = json.loads(Path(args.f6_evidence).read_text(encoding='utf-8'))
    require(f6.get('status') == 'passed' and f6.get('version') == args.version and f6.get('actualHost') is True
            and f6.get('actualNugetPackages') is True and f6.get('actualPostgreSql') is True,
            'F6 qualification has not passed for this exact private candidate.')
    require(os.environ.get('NOTES_ORACLE_DISPOSABLE') == 'true' and os.environ.get('NOTES_ORACLE_CONNECTION'),
            'Qualification requires the independently supplied disposable PostgreSQL database; never use a consumer database.')
    runtime = evidence / 'runtime'
    runtime.mkdir()
    runtime_feed = runtime / 'packages'
    runtime_feed.mkdir()
    # Preserve the complete F6 feed for proof/restore. Native activation shares
    # these exact contracts from Host and must not load a second archive identity.
    for package in (evidence / 'packages').glob('*.nupkg'):
        with zipfile.ZipFile(package) as archive:
            nuspec = next(entry for entry in archive.namelist() if entry.endswith('.nuspec'))
            identity = ET.fromstring(archive.read(nuspec)).find('./{*}metadata/{*}id').text
        if identity.lower() not in HOST_CONTRACT_PACKAGES:
            shutil.copy2(package, runtime_feed / package.name)
    host = Path(args.host).resolve()
    require(host.is_file() and (host.parent / 'appsettings.json').is_file(), 'The actual Foundation Host output is missing.')
    f6_inputs_path = Path(args.f6_evidence).resolve().parent / 'inputs.json'
    require(f6_inputs_path.is_file(), 'F6 preserved exact package/Host input hashes are missing.')
    f6_inputs = json.loads(f6_inputs_path.read_text(encoding='utf-8'))
    require(f6_inputs.get('version') == args.version and f6_inputs.get('host', {}).get('sha256') == hashlib.sha256(host.read_bytes()).hexdigest(),
            'The actual Host differs from the matching F6-qualified input.')
    expected = {name: digest for name, digest in f6_inputs.get('packages', {}).items() if name.startswith('Orbyss.Foundation.')}
    actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (evidence / 'packages').glob('Orbyss.Foundation.*.nupkg')}
    require(expected and actual == expected, 'The exact private Foundation package bytes differ from F6-qualified inputs.')
    sys.path.insert(0, str(ROOT / 'scripts'))
    import prepare_foundation_contracts_development_profile as development_profile
    selected = development_profile.verify(Path(args.development_profile), args.profile_identity,
        f6_result=Path(args.f6_evidence), packages=Path(args.packages), host=host)
    require(selected['version'] == args.version and selected['status'] == 'development-qualified',
            'The selected PK2A profile does not qualify this exact candidate.')
    # Execute an owned snapshot of the verified native Host closure. Another
    # source build must not replace a DLL between admission and process startup.
    host_snapshot = evidence / 'host'
    host_snapshot.mkdir()
    host_runtime_files = f6_inputs.get('hostRuntimeFiles')
    require(isinstance(host_runtime_files, dict) and host_runtime_files,
            'F6 complete Host runtime input hashes are missing.')
    for relative, expected_hash in host_runtime_files.items():
        original = (host.parent / relative).resolve()
        copied = (host_snapshot / relative).resolve()
        require(original.is_relative_to(host.parent) and copied.is_relative_to(host_snapshot),
                'F6 Host runtime inventory escapes its owned directory.')
        require(original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest() == expected_hash,
                'Host payload changed while Notes captured qualification inputs.')
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, copied)
        require(hashlib.sha256(copied.read_bytes()).hexdigest() == expected_hash,
                'Notes Host snapshot differs from admitted F6 inputs.')
    qualified_host = host_snapshot / host.name
    shutil.copy2(host_snapshot / 'appsettings.json', runtime / 'appsettings.json')
    address, issuer = 'http://127.0.0.1:' + str(free_port()), 'http://127.0.0.1:' + str(free_port())
    (runtime / 'shells.json').write_text(json.dumps(settings(issuer), indent=2), encoding='utf-8')
    (runtime / 'hostsettings.json').write_text(json.dumps({
        'Foundation': {'Transport': {'MaxRequestBodyBytes': 30000000, 'MaxRequestHeadersBytes': 32768}},
        'Nuplane': {'Setup': {'StateFilePath': str(runtime / 'nuplane-store-state.json')},
                    'FeedResolution': {'PackageInstallRoot': str(runtime / 'installed')},
                    'Loading': {'ActiveStoreRoot': str(runtime / 'packages/.installed')}}}), encoding='utf-8')
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(('CSHELLS__', 'FOUNDATION__', 'NUPLANE__'))}
    environment.update({'ASPNETCORE_ENVIRONMENT': 'Development', 'DOTNET_ENVIRONMENT': 'Development',
        'CShells__Shells__default__Configuration__Foundation__PostgreSql__Policies__notes__ConnectionString': os.environ['NOTES_ORACLE_CONNECTION']})
    oracle = source / 'oracle/bin/Release/net10.0/Notes.Oracle.dll'
    processes = []
    cleanup = []
    try:
        for label, command, cwd in (
            ('issuer', [args.dotnet, str(oracle), 'serve', '--url', issuer, '--target', address], source),
            ('host', [args.dotnet, str(qualified_host), '--contentRoot', str(runtime), '--urls', address], runtime)):
            log_path = evidence / (label + '.log')
            with log_path.open('w', encoding='utf-8') as log:
                process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            processes.append((label, process))
            wait_ready(issuer + '/ready' if label == 'issuer' else address + '/bff/user', process, log_path)
        run([args.dotnet, str(oracle), 'check', '--host', address, '--issuer', issuer], source, evidence / 'oracle.log', environment)
    finally:
        for label, process in reversed(processes):
            if process.poll() is None:
                process.terminate()
            forced = False
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                forced = True
                process.kill()
                process.wait(timeout=15)
            cleanup.append({'process': label, 'pid': process.pid, 'exitCode': process.poll(),
                            'forcedTermination': forced, 'exited': process.poll() is not None})
        (evidence / 'process-cleanup.json').write_text(json.dumps(cleanup, indent=2) + '\n', encoding='utf-8')
    require(len(cleanup) == 2 and all(process['exited'] for process in cleanup), 'Actual Notes server cleanup was incomplete.')
    require('PRIVATE_SQL_SENTINEL' not in (evidence / 'host.log').read_text(encoding='utf-8', errors='replace'), 'Actual host diagnostics leaked private SQL.')
    result = {'scenario': ORACLE_SCENARIO, 'status': 'passed', 'version': args.version, 'actualHost': True,
        'actualNugetPackages': True, 'actualPostgreSql': True, 'nativeSignedOidc': True, 'paidWorkersStarted': False,
        'f6EvidenceSha256': hashlib.sha256(Path(args.f6_evidence).read_bytes()).hexdigest(),
        'developmentProfile': args.profile_identity,
        'developmentEvidenceSha256': hashlib.sha256((Path(args.development_profile) / 'evidence.json').read_bytes()).hexdigest(),
        'hostSha256': hashlib.sha256(qualified_host.read_bytes()).hexdigest(),
        'hostRuntimeFiles': host_runtime_files, 'executedHost': str(qualified_host), 'processCleanup': cleanup}
    (evidence / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Actual Notes package/Host/PostgreSQL/native OIDC oracle passed: ' + str(evidence))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--qualify', action='store_true')
    parser.add_argument('--packages')
    parser.add_argument('--version')
    parser.add_argument('--host')
    parser.add_argument('--f6-evidence')
    parser.add_argument('--development-profile')
    parser.add_argument('--profile-identity')
    parser.add_argument('--nuget-config', help='Explicit dependency sources/mapping for CShells/Nuplane previews; private candidate mapping is added locally.')
    parser.add_argument('--dotnet', default='dotnet')
    parser.add_argument('--sdk-working-directory')
    parser.add_argument('--evidence-directory', help='New owned artifacts directory; existing evidence is never overwritten.')
    parser.add_argument('--behavior-seed', choices=BEHAVIOR_SEEDS,
                        help='Compile and package one intentional violating copy; only independent oracle rejection admits the negative evidence.')
    parser.add_argument('--graph-seed', choices=tuple(GRAPH_SEEDS),
                        help='Require an actual build followed by rejection of the evaluated/compiled graph; no HTTP acceptance claim.')
    args = parser.parse_args()
    require(not (args.graph_seed and (args.qualify or args.behavior_seed)), 'Graph rejection is a separate preparation check, not HTTP qualification.')
    self_test()
    if args.prepare or args.qualify:
        evidence, source = prepare(args)
        if args.qualify:
            qualify(args, evidence, source)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
