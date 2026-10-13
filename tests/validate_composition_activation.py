"""Build/execute consumer-owned tests against the generated public CShells seam.

This does not qualify the Foundation host/providers. Native runtime acceptance
remains in the composition golden; no real consumer, service or agent is started.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import foundation_composition
import composition_model
import composition_migrate
sys.path.insert(0, str(TEMPLATE / 'files/eng'))

CONTRACTS = ('CShells.Abstractions', 'CShells.AspNetCore.Abstractions')


def main():
    evidence = ROOT / 'artifacts/tests/composition-activation' / uuid.uuid4().hex
    root = evidence / 'consumer'; root.mkdir(parents=True)
    def command(arguments, name, succeeds=True):
        result = subprocess.run(arguments, cwd=root, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=240)
        output = result.stdout + result.stderr
        (evidence / (name + '.log')).write_text(output, encoding='utf-8')
        if (result.returncode == 0) != succeeds:
            raise AssertionError('Unexpected command result; inspect ' + str(evidence / (name + '.log')))
        return output

    try:
        shutil.copyfile(TEMPLATE / 'files/global.json', root / 'global.json')
        (root / 'Directory.Build.props').write_text('''<Project><PropertyGroup>
<TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
</PropertyGroup></Project>''', encoding='utf-8')
        # Use only the existing production contract pins and maintained test pin.
        pins = {item.get('Include'): item.get('Version') for item in
                ET.parse(TEMPLATE / 'files/eng/ProgramKit.Packages.props').iter('PackageVersion')}
        test_pins = json.loads((TEMPLATE / 'files/eng/foundation-test-support/packages.json').read_text())
        packages = ET.Element('Project')
        ET.SubElement(ET.SubElement(packages, 'PropertyGroup'), 'ManagePackageVersionsCentrally').text = 'true'
        group = ET.SubElement(packages, 'ItemGroup')
        for identity in (*CONTRACTS, 'xunit.v3.mtp-v2'):
            ET.SubElement(group, 'PackageVersion', Include=identity, Version=(pins | test_pins)[identity])
        (root / 'Directory.Packages.props').write_bytes(ET.tostring(packages))
        (root / 'NuGet.Config').write_text('''<configuration><packageSources><clear />
<add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
</packageSources></configuration>''', encoding='utf-8')
        project = {'path': 'src/Activation.Api/Activation.Api.csproj', 'packageId': 'Activation.Api',
                   'featureIdentity': 'Activation.Api', 'role': 'implementation'}
        legacy = json.loads((TEMPLATE / 'compositions/foundation-bff-keycloak.json').read_text())
        legacy['projects'] = [project]
        legacy['runtime']['rootPackages'] = [project['packageId']]
        (root / 'eng').mkdir()
        (root / composition_model.INPUT).write_text(json.dumps(legacy), encoding='utf-8')
        migration = composition_migrate.preview(root)
        composition_migrate.apply(root, migration['planDigest'])
        project = next(iter(composition_model.resources(composition_model.load(root), 'feature').values()))
        # The generated API seam uses only public shell contracts. Omit publisher
        # runtime packages from this bounded compiler probe, with no build/pack claim.
        files = foundation_composition.scaffold_project(project, {'packages': {}})
        for path, payload in files.items():
            target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
        source_refs = {item.get('Include'): item.get('PrivateAssets') for item in
                       ET.fromstring(files[project['path']]).iter('PackageReference')}
        assert all(source_refs[identity] == 'all' for identity in CONTRACTS)
        fixture = ROOT / 'tests/fixtures/composition-activation'
        tests = root / 'tests/Activation'; shutil.copytree(fixture, tests)
        test_project = tests / 'Activation.Tests.csproj'
        # Generate actual references from reviewed test responsibility; this fixture
        # no longer hand-authors the activation contracts it is supposed to prove.
        import test_project as test_scaffold
        activation = {'path': test_project.relative_to(root).as_posix(), 'role': 'test',
                      'projectReferences': [project['path']], 'packageReferences': ['xunit.v3.mtp-v2'],
                      'responsibilities': [{'name': 'selected API shell activation', 'kind': 'test',
                                            'effects': [], 'testSeams': ['activation']}]}
        original = test_scaffold.scaffold(activation, {k.casefold(): v for k, v in (pins | test_pins).items()})
        test_project.write_bytes(original)
        document = ET.fromstring(original)
        refs = {item.get('Include') for item in document.iter('PackageReference')}
        assert set(CONTRACTS) <= refs
        command(['dotnet', 'restore', str(test_project), '--nologo', '-warnaserror'], 'restore')
        for group in document.findall('ItemGroup'):
            for item in list(group):
                if item.tag == 'PackageReference' and item.get('Include') in CONTRACTS:
                    group.remove(item)
        test_project.write_bytes(ET.tostring(document))
        command(['dotnet', 'restore', str(test_project), '--nologo', '-warnaserror'], 'restore-missing-contracts')
        failed = command(['dotnet', 'build', str(test_project), '--no-restore', '--nologo'], 'missing-contracts', succeeds=False)
        assert 'CS0246' in failed and "'CShells'" in failed, 'Expected missing CShells compiler diagnostic'
        test_project.write_bytes(original)
        command(['dotnet', 'restore', str(test_project), '--nologo', '-warnaserror'], 'restore-contracts')
        command(['dotnet', 'restore', str(test_project), '--locked-mode', '--nologo', '-warnaserror'], 'restore-locked')
        command(['dotnet', 'build', str(test_project), '--no-restore', '--nologo'], 'build')
        output = command(['dotnet', 'run', '--project', str(test_project), '--no-build'], 'execute')
        assert re.search(r'^\s*total:\s*1\s*$', output, re.MULTILINE), 'Activation assertion did not execute'
        assert re.search(r'^\s*succeeded:\s*1\s*$', output, re.MULTILINE), 'Activation assertion did not pass'
        # Activate the mixed generated seams through the selected real shell
        # runtime, instead of treating direct ConfigureServices calls as activation.
        runtime = {'path': 'src/Activation.Runtime/Activation.Runtime.csproj', 'packageId': 'Activation.Runtime',
                   'featureIdentity': 'Existing.RuntimeIdentity', 'role': 'implementation', 'responsibility': 'runtime'}
        runtime_files = foundation_composition.scaffold_project(runtime, {'packages': {}})
        for path, payload in runtime_files.items():
            target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
        runtime_source = root / 'src/Activation.Runtime/ActivationRuntimeFeature.cs'
        runtime_source.write_text(runtime_source.read_text().replace(
            'public void ConfigureServices(IServiceCollection services) { }',
            'public void ConfigureServices(IServiceCollection services) { services.AddScoped<OwnedRuntimeService>(); }'))
        (runtime_source.parent / 'OwnedRuntimeService.cs').write_text('''namespace Activation.Runtime;
public sealed class OwnedRuntimeService : IDisposable {
    public Guid Identity { get; } = Guid.NewGuid();
    public bool Disposed { get; private set; }
    public void Dispose() => Disposed = true;
}
''')
        runtime_refs = {item.get('Include') for item in ET.fromstring(runtime_files[runtime['path']]).iter('PackageReference')}
        assert runtime_refs == {'CShells.Abstractions'}
        assert b'IWebShellFeature' not in runtime_files['src/Activation.Runtime/ActivationRuntimeFeature.cs']
        central = ET.parse(root / 'Directory.Packages.props').getroot()
        ET.SubElement(central.find('ItemGroup'), 'PackageVersion', Include='CShells.AspNetCore', Version=pins['CShells.AspNetCore.Abstractions'])
        (root / 'Directory.Packages.props').write_bytes(ET.tostring(central))
        mixed = root / 'tests/MixedActivation'; mixed.mkdir()
        (mixed / 'MixedActivation.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable></PropertyGroup>
  <ItemGroup><PackageReference Include="CShells.AspNetCore" />
    <ProjectReference Include="../../src/Activation.Api/Activation.Api.csproj" />
    <ProjectReference Include="../../src/Activation.Runtime/Activation.Runtime.csproj" />
  </ItemGroup>
</Project>''')
        (mixed / 'Program.cs').write_text('''using CShells.AspNetCore.Configuration;
using CShells.DependencyInjection;
using CShells.Features;
using CShells.Lifecycle;
using Activation.Runtime;
var builder = WebApplication.CreateBuilder();
builder.Logging.ClearProviders();
builder.Configuration.AddInMemoryCollection(new Dictionary<string, string?> {
    ["CShells:Shells:mixed:Features:Activation.Api"] = "true",
    ["CShells:Shells:mixed:Features:Existing.RuntimeIdentity"] = "true"
});
builder.Services.AddCShells(shells => shells.WithAssemblies(typeof(Program).Assembly,
    typeof(Activation.Api.ApiFeature).Assembly, typeof(ActivationRuntimeFeature).Assembly)
    .WithConfigurationProvider(builder.Configuration));
await using var host = builder.Build();
var registry = host.Services.GetRequiredService<IShellRegistry>();
var shell = await registry.GetOrActivateAsync("mixed");
if (shell.State != ShellLifecycleState.Active) throw new InvalidOperationException("Mixed shell did not activate.");
OwnedRuntimeService first;
using (var scope = shell.ServiceProvider.CreateScope()) {
    first = scope.ServiceProvider.GetRequiredService<OwnedRuntimeService>();
    if (!ReferenceEquals(first, scope.ServiceProvider.GetRequiredService<OwnedRuntimeService>()))
        throw new InvalidOperationException("Owned service did not retain scope lifetime.");
}
if (!first.Disposed) throw new InvalidOperationException("Owned scope did not dispose.");
using (var scope = shell.ServiceProvider.CreateScope()) {
    if (first.Identity == scope.ServiceProvider.GetRequiredService<OwnedRuntimeService>().Identity)
        throw new InvalidOperationException("Owned service leaked across scopes.");
    if (scope.ServiceProvider.GetRequiredService<ActivationMarker>() is null)
        throw new InvalidOperationException("Generated HTTP prerequisites were not activated.");
}
using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(5));
await (await registry.DrainAsync(shell, deadline.Token)).WaitAsync(deadline.Token);
Console.WriteLine("Mixed generated feature activation and owned scope lifetime passed.");
public sealed class ActivationMarker;
[ShellFeature("Orbyss.Foundation.Authentication")]
public sealed class AuthenticationPrerequisite : IShellFeature {
    public void ConfigureServices(IServiceCollection services) => services.AddSingleton<ActivationMarker>();
}
[ShellFeature("Orbyss.Foundation.WebDefaults")]
public sealed class WebPrerequisite : IShellFeature {
    public void ConfigureServices(IServiceCollection services) { }
}
''')
        mixed_project = mixed / 'MixedActivation.csproj'
        command(['dotnet', 'restore', str(mixed_project), '--nologo', '-warnaserror'], 'mixed-restore')
        command(['dotnet', 'restore', str(mixed_project), '--locked-mode', '--nologo', '-warnaserror'], 'mixed-locked')
        command(['dotnet', 'build', str(mixed_project), '--no-restore', '--nologo'], 'mixed-build')
        mixed_output = command(['dotnet', 'run', '--project', str(mixed_project), '--no-build'], 'mixed-activation')
        assert 'Mixed generated feature activation and owned scope lifetime passed.' in mixed_output
        scoped = {}
        for name, seam, source, expected in (
            ('Lifecycle', 'shell-lifecycle', '''using CShells.Lifecycle;
using Xunit;
public sealed class Prepare : IShellInitializer {
    public int Invocations { get; private set; }
    public Task InitializeAsync(CancellationToken token) { token.ThrowIfCancellationRequested(); Invocations++; return Task.CompletedTask; }
}
public sealed class LifecycleTests { [Fact] public async Task OwnerPreparationRunsExactlyOnce() {
    var prepare = new Prepare(); await prepare.InitializeAsync(CancellationToken.None); Assert.Equal(1, prepare.Invocations);
} }
''', {'CShells.Abstractions'}),
            ('PureCore', 'pure-core', '''using Xunit;
public sealed class PurePolicyTests { [Fact] public void PurePolicyHasNoShellContractDependency() {
    Func<int, bool> eligible = years => years >= 18;
    Assert.False(eligible(17)); Assert.True(eligible(18));
} }
''', set())):
            relative = f'tests/{name}/{name}.Tests.csproj'
            declaration = {'path': relative, 'role': 'test', 'projectReferences': [],
                           'packageReferences': ['xunit.v3.mtp-v2'],
                           'responsibilities': [{'name': name + ' test ownership', 'kind': 'test',
                                                 'effects': [], 'testSeams': [seam]}]}
            payload = test_scaffold.scaffold(declaration, {k.casefold(): v for k, v in (pins | test_pins).items()})
            target = root / relative; target.parent.mkdir(parents=True); target.write_bytes(payload)
            (target.parent / 'OwnedTests.cs').write_text(source, encoding='utf-8')
            actual = {p.get('Include') for p in ET.fromstring(payload).iter('PackageReference')}
            assert actual - {'xunit.v3.mtp-v2'} == expected
            command(['dotnet', 'restore', str(target), '--nologo', '-warnaserror'], name.lower() + '-restore')
            command(['dotnet', 'restore', str(target), '--locked-mode', '--nologo', '-warnaserror'], name.lower() + '-locked')
            command(['dotnet', 'build', str(target), '--no-restore', '--nologo'], name.lower() + '-build')
            result = command(['dotnet', 'run', '--project', str(target), '--no-build'], name.lower() + '-execute')
            assert re.search(r'^\s*total:\s*1\s*$', result, re.MULTILINE) and re.search(r'^\s*succeeded:\s*1\s*$', result, re.MULTILINE)
            lock = json.loads((target.parent / 'packages.lock.json').read_text())
            direct = {k for framework in lock['dependencies'].values() for k, row in framework.items() if row['type'] == 'Direct'}
            assert expected <= direct and not (set(CONTRACTS) - expected) & direct
            scoped[seam] = {'directContracts': sorted(expected), 'testsExecuted': 1, 'lockedRestore': True}
        (evidence / 'status.json').write_text(json.dumps({'status': 'passed',
            'contractPins': {identity: pins[identity] for identity in CONTRACTS},
            'missingContractsRejected': True, 'activationTestsExecuted': 1, 'generatedTestDependencies': True,
            'activationLockedRestore': True, 'mixedShellActivation': True, 'runtimeScopedResolutionAndDisposal': True,
            'responsibilityScopes': scoped}, indent=2), encoding='utf-8')
        print('Composition activation-test build/execution passed: ' + str(evidence))
    except Exception as error:
        (evidence / 'status.json').write_text(json.dumps({'status': 'failed', 'failure': str(error)}), encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
