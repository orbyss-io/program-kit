"""Independent bounded oracle for the shipped label application capability.

Uses the actual scoped registration and runtime/Core sources, without
HTTP or PostgreSQL. The runtime uses the selected native deadline implementation;
Core remains BCL-only. No expected result comes from scaffold metadata.
"""
from pathlib import Path
import argparse
import subprocess
import sys
import uuid

ORACLE = '''using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Configuration;
using ProgramKit.Examples.TypedOperation;

internal static class Program
{
    private static void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }

    private static async Task Main()
    {
        var services = new ServiceCollection();
        services.AddScoped<ILabelStore, Store>();
        var configuration = new ConfigurationBuilder().Build();
        LabelServices.Configure(services, configuration);
        var options = new ServiceProviderOptions { ValidateScopes = true };
        using var provider = services.BuildServiceProvider(options);
        using var first = provider.CreateScope();
        using var second = provider.CreateScope();
        var operation = first.ServiceProvider.GetRequiredService<ILabelOperations>();
        var sameScopeOperation = first.ServiceProvider.GetRequiredService<ILabelOperations>();
        var otherScopeOperation = second.ServiceProvider.GetRequiredService<ILabelOperations>();
        var sameScope = ReferenceEquals(operation, sameScopeOperation);
        var differentScope = !ReferenceEquals(operation, otherScopeOperation);
        Check(sameScope, "same scope identity");
        Check(differentScope, "different scope identity");
        var store = (Store)first.ServiceProvider.GetRequiredService<ILabelStore>();
        var initial = await operation.ReadAsync(CancellationToken.None);
        Check(initial == "ready", "initial label");
        store.Calls.Clear();
        using var source = new CancellationTokenSource();
        var updated = await operation.UpdateAsync("edited", source.Token);
        Check(updated == "edited", "committed label representation");
        var callsAfterUpdate = string.Join(",", store.Calls);
        Check(callsAfterUpdate == "write:edited,read", "write then read exactly once");
        Check(store.LastToken != source.Token, "native outer token reaches both stages");
        store.Calls.Clear();
        source.Cancel();
        try { await operation.UpdateAsync("canceled", source.Token); throw new Exception("cancellation omitted"); }
        catch (OperationCanceledException) { }
        Check(store.Value == "edited" && store.Calls.Count == 0, "cancel before effect");
        store.Fail = true;
        try { await operation.UpdateAsync("failure", CancellationToken.None); throw new Exception("failure omitted"); }
        catch (InvalidOperationException error) when (error.Message == "fictional write failed") { }
        var callsAfterFailure = string.Join(",", store.Calls);
        Check(callsAfterFailure == "write:failure", "no read or retry after fault");
        Console.WriteLine("Independent application/registration assertions passed; no HTTP, database, browser or atomic snapshot claim.");
    }

    private sealed class Store : ILabelStore
    {
        public string Value = "ready";
        public bool Fail;
        public readonly List<string> Calls = new();
        public CancellationToken LastToken;
        public Task<string> ReadAsync(CancellationToken token)
        {
            token.ThrowIfCancellationRequested(); LastToken = token; Calls.Add("read");
            return Task.FromResult(Value);
        }
        public Task WriteAsync(string value, CancellationToken token)
        {
            token.ThrowIfCancellationRequested(); LastToken = token; Calls.Add("write:" + value);
            if (Fail) throw new InvalidOperationException("fictional write failed");
            Value = value; return Task.CompletedTask;
        }
    }
}
'''


def check(root, invalid=False):
    governance = root / '.specify/extensions/program-kit-governance/scripts'
    if not governance.is_dir():
        governance = root / 'extensions/program-kit-governance/scripts'
    sys.path.insert(0, str(governance))
    from asset_sources import read as source_bytes, tree as source_tree
    engineering = root / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng'
    if not engineering.is_dir():
        engineering = root / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
    sys.path.insert(0, str(engineering))
    from owned_scratch import native_path
    source = root / '.specify/extensions/program-kit-dotnet/references/examples/typed-operation'
    if not source_tree(source):
        source = root / 'extensions/program-kit-dotnet/references/examples/typed-operation'
    directory = root / 'artifacts/label-check' / uuid.uuid4().hex[:8]
    directory.mkdir(parents=True)
    for name in ('ILabelStore.cs', 'ILabelOperations.cs', 'LabelOperations.cs', 'LabelServices.cs', 'LabelExecutionOptions.cs'):
        text = source_bytes(source / 'Labels' / name).decode('utf-8')
        if invalid and name == 'LabelOperations.cs':
            original = 'await store.WriteAsync(value, deadline.Token);'
            if text.count(original) != 1:
                raise ValueError('Actual missing-effect negative seam is absent; preserve source for review')
            text = text.replace(original, '// Deliberately omit the effect.')
        (directory / name).write_text(text, encoding='utf-8')
    for name in ('Directory.Build.props', 'Directory.Build.targets'):
        (directory / name).write_text('<Project/>', encoding='utf-8')
    (directory / 'NuGet.Config').write_text('<configuration><packageSources><clear/></packageSources></configuration>', encoding='utf-8')
    (directory / 'LabelCheck.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        '<OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit>'
        '<RestoreSources></RestoreSources></PropertyGroup><ItemGroup>'
        '<FrameworkReference Include="Microsoft.AspNetCore.App" /><PackageReference Include="Orbyss.Foundation.Execution" Version="0.3.7" /></ItemGroup></Project>', encoding='utf-8')
    (directory / 'Program.cs').write_text(ORACLE, encoding='utf-8')
    run = subprocess.run(['dotnet', 'run', '--project', native_path(directory / 'LabelCheck.csproj'), '--configuration', 'Release'],
                         cwd=native_path(root), capture_output=True, text=True, encoding='utf-8', timeout=90)
    print(run.stdout, end='')
    print(run.stderr, end='')
    print('Independent check sources/results retained: ' + str(directory))
    return run.returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--invalid', action='store_true')
    args = parser.parse_args()
    raise SystemExit(check(Path.cwd(), args.invalid))
