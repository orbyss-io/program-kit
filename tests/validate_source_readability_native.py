"""Real generated-policy build against explicitly supplied development analyzer bytes.

This is local source qualification, never public version/profile or release acceptance.
The same version in the development package requires an isolated cache/feed per control.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
import uuid
from contextlib import nullcontext

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
MANDATORY_IDS = ['ORB1001', 'ORB1003', 'ORB1004', 'ORB1005', 'ORB1006', 'ORB1007', 'ORB1008', 'ORB1009', 'ORB1010']
LAYOUT_IDS = ['ORB1007', 'ORB1008', 'ORB1009', 'ORB1010']
SUPPRESSION_GUARD = {'policyId': 'FoundationSourceSuppressionPolicy', 'kind': 'generated-compiler-error',
                     'errorId': 'CS1029', 'includesGeneratedCompileInputs': True, 'excludesSiblingGeneratorOutputs': True}

BAD = '''/// <summary>Native source admission control.</summary>
internal sealed class Sample
{
    /// <summary>Exercises the invalid authored composition.</summary>
    internal void Run() { value++; this.Next().Next(); Take(Next(), this, this); }
    /// <summary>Retains the current execution count.</summary>
    private int value;
    /// <summary>Returns the same finite sample.</summary>
    private Sample Next() => this;
    /// <summary>Accepts already prepared values.</summary>
    private void Take(params object[] values) { }
}
'''
GOOD = '''/// <summary>Native source admission control.</summary>
internal sealed class Sample
{
    /// <summary>Retains the current execution count.</summary>
    private int value;
    /// <summary>Exercises correctly prepared values and separate chain invocations.</summary>
    internal void Run()
    {
        value++;
        this
            .Next()
            .Next();
        var prepared = Next();
        Take(
            prepared,
            this,
            this
        );
    }
    /// <summary>Returns the same finite sample.</summary>
    private Sample Next() => this;
    /// <summary>Accepts already prepared values.</summary>
    private void Take(params object[] values) { }
}
'''


def execute(root, command, label, expected=0, codes=(), allowed_compiler_errors=()):
    started = time.monotonic()
    process = subprocess.run(command, cwd=root, text=True, encoding='utf-8', capture_output=True, timeout=120)
    elapsed = time.monotonic() - started
    (root / (label + '.stdout.log')).write_text(process.stdout, encoding='utf-8')
    (root / (label + '.stderr.log')).write_text(process.stderr, encoding='utf-8')
    output = process.stdout + process.stderr
    if (expected == 0 and process.returncode != 0) or (expected != 0 and process.returncode == 0):
        raise AssertionError(label + ': unexpected execution outcome\n' + output)
    compiler_errors = set(re.findall(r'error\s+(CS[0-9]+)', output))
    if allowed_compiler_errors and (set(allowed_compiler_errors) != {'CS1029'} or 'FoundationSourceSuppressionPolicy' not in codes):
        raise AssertionError('Only an explicit native source-suppression policy control may admit compiler CS1029.')
    if any(code not in output for code in codes) or 'AD0001' in output or compiler_errors - set(allowed_compiler_errors):
        raise AssertionError(label + ': expected diagnostic rejection was not established\n' + output)
    return {'command': command, 'exitCode': process.returncode, 'codes': list(codes), 'allowedCompilerErrors': list(allowed_compiler_errors),
            'elapsedSeconds': round(elapsed, 3), 'stdoutSha256': hashlib.sha256(process.stdout.encode('utf-8')).hexdigest(),
            'stderrSha256': hashlib.sha256(process.stderr.encode('utf-8')).hexdigest()}


def fixture(directory, package):
    directory.mkdir(parents=True)
    feed = directory / 'feed'; feed.mkdir()
    shutil.copy2(package, feed / package.name)
    with zipfile.ZipFile(package) as archive:
        nuspec = ET.fromstring(archive.read(next(p for p in archive.namelist() if p.endswith('.nuspec'))))
        version = next(n.text for n in nuspec.iter() if n.tag.rsplit('}', 1)[-1] == 'version')
    eng = directory / 'scripts'; eng.mkdir()
    for name in ('ProgramKit.Build.props', 'ProgramKit.Build.targets'):
        shutil.copy2(FILES / 'scripts' / name, eng / name)
    (directory / 'Sample.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><Import Project="config/program-kit/build/ProgramKit.Build.props"/>'
        '<PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup>'
        '<Import Project="config/program-kit/build/ProgramKit.Build.targets"/></Project>', encoding='utf-8')
    (directory / 'Directory.Packages.props').write_text('<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup>'
        '<ItemGroup><PackageVersion Include="Orbyss.Foundation.Analyzers" Version="' + version + '"/></ItemGroup></Project>', encoding='utf-8')
    (directory / 'NuGet.Config').write_text('<configuration><packageSources><clear/><add key="exact-local" value="' + feed.as_posix()
        + '"/></packageSources><config><add key="globalPackagesFolder" value="' + (directory / 'packages').as_posix()
        + '"/></config></configuration>', encoding='utf-8')
    (directory / 'Sample.cs').write_text(GOOD, encoding='utf-8')
    return directory / 'Sample.csproj'


# Fictional native semantic boundaries, not Foundation.Build feature packaging.
MODELS = """// <auto-generated/>
namespace CShells.Features {
    internal interface IShellFeature { }
    [System.AttributeUsage(System.AttributeTargets.Class)]
    internal sealed class ShellFeatureAttribute : System.Attribute {
        public ShellFeatureAttribute(string name) { }
    }
}
namespace Microsoft.Extensions.DependencyInjection {
    internal interface IServiceCollection { }
    internal sealed class ServiceCollection : IServiceCollection { }
    internal static class ServiceCollectionHostedServiceExtensions {
        internal static IServiceCollection AddHostedService<T>(this IServiceCollection services) => services;
    }
}
namespace NativePolicyFixture { internal static class Keys { internal const string Code = "ORB1001:title"; } }
"""
FEATURE = """using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
namespace NativePolicyFixture;
/// <summary>Supplies the finite fictional typed feature boundary.</summary>
[ShellFeature("{identity}")]
internal sealed class OwnedFeature : IShellFeature
{{
    /// <summary>Exercises registration without running a provider.</summary>
    {attribute}internal void Configure()
    {{
        var services = new ServiceCollection();
        {body}
    }}
}}
"""
OLD_BAD = """namespace NativePolicyFixture;
internal sealed class First
{
    private static void Helper() { }
    internal static void Run() { Helper(); }
}
internal sealed class Second { }
"""


def existing_policy_controls(owner, project):
    """Qualify each old mandatory family and the separate intentional compiler error."""
    results = []
    command = ['dotnet', 'build', str(project), '--no-restore', '--nologo']
    source = owner / 'Sample.cs'
    editorconfig = owner / '.editorconfig'
    # The native analyzer reads this real global compiler option. This fixture does
    # not claim the separately packaged Foundation.Build feature lifecycle.
    (owner / '.globalconfig').write_text('is_global = true\nglobal_level = 200\nbuild_property.FoundationFeatureIdentity = Governed\n', encoding='utf-8')
    (owner / 'Models.g.cs').write_text(MODELS, encoding='utf-8')
    source.write_text(GOOD, encoding='utf-8')
    results.append(execute(owner, command, 'old-policy-valid-first'))
    feature = lambda identity, body, attribute='': FEATURE.format(identity=identity, body=body, attribute=attribute)
    for name, bad, codes in (
        ('structure-documentation', OLD_BAD, ['ORB1003', 'ORB1004', 'ORB1005']),
        ('hosted-service', feature('Governed', 'services.AddHostedService<object>();'), ['ORB1001']),
        ('feature-identity', feature('Wrong', '_ = services;'), ['ORB1006']),
    ):
        source.write_text(bad, encoding='utf-8')
        results.append(execute(owner, command, 'old-policy-' + name, 1, codes))
        editorconfig.write_text('root = true\n[*.cs]\n' + ''.join('dotnet_diagnostic.' + code + '.severity = none\n' for code in MANDATORY_IDS), encoding='utf-8')
        source.write_text('#pragma warning disable ' + ', '.join(MANDATORY_IDS) + '\n' + bad, encoding='utf-8')
        results.append(execute(owner, command + ['-p:NoWarn=' + '%3B'.join(MANDATORY_IDS)], 'old-policy-' + name + '-combined-waiver', 1, codes))
        editorconfig.write_text('root = true\n[*.cs]\n', encoding='utf-8')
    # A typed alias/constant ID targets an actual authored ORB1001 boundary.
    attribute = '[PolicySuppression("Lifecycle", Keys.Code)]\n    '
    suppressed = 'using PolicySuppression = System.Diagnostics.CodeAnalysis.SuppressMessageAttribute;\n' + feature('Governed', 'services.AddHostedService<object>();', attribute)
    source.write_text('#pragma warning disable CS1029, ORB1001\n' + suppressed, encoding='utf-8')
    (owner / 'GlobalSuppressions.g.cs').write_text('// <auto-generated/>\n[assembly: System.Diagnostics.CodeAnalysis.SuppressMessage("Compiler", "CS1029", Scope="module")]\n', encoding='utf-8')
    editorconfig.write_text('root = true\n[*.cs]\ndotnet_diagnostic.CS1029.severity = none\ndotnet_diagnostic.ORB1001.severity = none\n', encoding='utf-8')
    results.append(execute(owner, command + ['-p:NoWarn=CS1029%3BORB1001'], 'typed-source-suppression-compiler-guard', 1,
                           ['CS1029', 'FoundationSourceSuppressionPolicy'], allowed_compiler_errors=['CS1029']))
    (owner / 'GlobalSuppressions.g.cs').unlink()
    source.write_text(GOOD.replace('internal sealed class Sample', '[System.Diagnostics.CodeAnalysis.SuppressMessage("Style", "ORB1002")]\ninternal sealed class Sample'), encoding='utf-8')
    editorconfig.write_text('root = true\n[*.cs]\n', encoding='utf-8')
    results.append(execute(owner, command, 'recommendation-source-suppression-allowed'))
    source.write_text(GOOD, encoding='utf-8')
    results.append(execute(owner, command, 'old-policy-and-guard-repaired'))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyzer-package', type=Path, default=os.environ.get('PROGRAM_KIT_ANALYZER_CANDIDATE'))
    parser.add_argument('--released-package', type=Path)
    args = parser.parse_args()
    if not args.analyzer_package or not args.analyzer_package.is_file():
        raise ValueError('Supply --analyzer-package with exact local Foundation candidate bytes; unpublished qualification is a separate explicit development-only check.')
    started = time.monotonic()
    with zipfile.ZipFile(args.analyzer_package) as archive:
        marker = json.loads(archive.read('buildTransitive/source-readability-contract.json'))
    assert marker['contractId'] == 'source-readability-v1'
    assert marker['requiredDiagnosticIds'] == MANDATORY_IDS, 'Independent contract expectation must not follow an incomplete marker.'
    assert marker['recommendationDiagnosticIds'] == ['ORB1002'], 'A recommendation must not silently become mandatory.'
    assert marker['sourceSuppressionGuard'] == SUPPRESSION_GUARD, 'The separate native compiler guard must declare its exact input and proof limits.'
    retained = ROOT / 'artifacts/t' / ('native-' + uuid.uuid4().hex[:8])
    retained.mkdir(parents=True)
    with nullcontext(retained) as name:
        directory = Path(name)
        results = []
        project = fixture(directory / 'candidate', args.analyzer_package)
        owner = project.parent
        results.append(execute(owner, ['dotnet', 'restore', str(project), '--nologo'], 'restore'))
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo'], 'valid-first'))
        # Direct target invocation deliberately omits ResolveReferences. This is
        # the structural missing-attachment guard, not compiled behavior proof.
        results.append(execute(owner, ['dotnet', 'msbuild', str(project), '--nologo',
            '-target:ProgramKitRequireSourceReadability'], 'missing-attachment-structural-reject', 1, ['PKQ003']))
        (owner / 'Sample.cs').write_text(BAD, encoding='utf-8')
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo'], 'bad-manual-edit', 1, LAYOUT_IDS))
        # This is the SDK's normal IDE options pass, never implementation evidence.
        results.append(execute(owner, ['dotnet', 'msbuild', str(project), '--nologo', '-target:CoreCompile',
            '-p:DesignTimeBuild=true', '-p:SkipCompilerExecution=true', '-p:ProvideCommandLineArgs=true',
            '-getItem:CscCommandLineArgs'], 'ide-compiler-options'))
        metadata = json.loads((owner / 'ide-compiler-options.stdout.log').read_text(encoding='utf-8'))
        assert metadata['Items']['CscCommandLineArgs'], 'The real IDE pass must return compiler options.'
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo'],
                               'actual-build-after-ide-still-rejects', 1, LAYOUT_IDS))
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo',
            '-p:SkipCompilerExecution=true', '-p:ProvideCommandLineArgs=true'],
            'skipped-compiler-with-options-without-design-time-reject', 1, ['PKQ003']))
        for property_name in ('RunAnalyzers', 'RunAnalyzersDuringBuild', 'EnableNETAnalyzers', 'EnforceCodeStyleInBuild', 'GenerateMSBuildEditorConfigFile'):
            results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo', '-p:' + property_name + '=false'],
                                   'disabled-' + property_name, 1, ['PKQ003']))
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo',
            '-p:SkipCompilerExecution=true'], 'skipped-compiler-reject', 1, ['PKQ003']))
        for property_name in ('NoWarn', 'WarningsNotAsErrors'):
            for spelling in ('CS8784%3Bcs8785', '8784%2C8785'):
                label = property_name.lower() + '-' + ('named' if spelling.startswith('CS') else 'numeric')
                results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo',
                    '-p:' + property_name + '=' + spelling], label + '-generator-failure-reject', 1, ['PKQ003']))
        fresh = fixture(directory / 'fresh', args.analyzer_package)
        (fresh.parent / 'Sample.cs').write_text(BAD, encoding='utf-8')
        results.append(execute(fresh.parent, ['dotnet', 'restore', str(fresh), '--nologo'], 'fresh-restore'))
        results.append(execute(fresh.parent, ['dotnet', 'build', str(fresh), '--no-restore', '--nologo',
            '-p:GenerateMSBuildEditorConfigFile=false'], 'fresh-property-pipeline-reject', 1, ['PKQ003']))
        results.append(execute(fresh.parent, ['dotnet', 'build', str(fresh), '--no-restore', '--nologo',
            '-p:SkipCompilerExecution=true'], 'fresh-skipped-compiler-reject', 1, ['PKQ003']))
        editorconfig = owner / '.editorconfig'
        editorconfig.write_text('root = true\n[*.cs]\n' + ''.join('dotnet_diagnostic.' + rule + '.severity = none\n'
            for rule in ('ORB1007', 'ORB1008', 'ORB1009', 'ORB1010')), encoding='utf-8')
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo'],
                               'editorconfig-cannot-waive', 1, LAYOUT_IDS))
        editorconfig.write_text('root = true\n', encoding='utf-8')
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo',
            '-p:NoWarn=ORB1007%3BORB1008%3BORB1009%3BORB1010'], 'nowarn-cannot-waive', 1, LAYOUT_IDS))
        (owner / 'Sample.cs').write_text('#pragma warning disable ORB1007, ORB1008, ORB1009, ORB1010\n' + BAD, encoding='utf-8')
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo'],
                               'pragma-cannot-waive', 1, LAYOUT_IDS))
        (owner / 'Sample.cs').write_text(GOOD, encoding='utf-8')
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo'], 'repaired'))
        results.extend(existing_policy_controls(owner, project))
        results.append(execute(owner, ['dotnet', 'build', str(project), '--no-restore', '--nologo', '-p:FoundationSourceReadability=false'], 'disabled-reject', 1, ['PKQ001']))
        if args.released_package:
            with zipfile.ZipFile(args.released_package) as archive:
                assert 'buildTransitive/source-readability-contract.json' not in archive.namelist(), 'Old-package control must actually lack capability.'
            old = fixture(directory / 'current-published-pin', args.released_package)
            results.append(execute(old.parent, ['dotnet', 'restore', str(old), '--nologo'], 'restore'))
            results.append(execute(old.parent, ['dotnet', 'build', str(old), '--no-restore', '--nologo'], 'old-capability-reject', 1, ['PKQ002']))
        (directory / 'result.json').write_text(json.dumps({'claim': 'Development-only generated policy/native analyzer and compiler suppression-guard integration; no publication/profile qualification',
            'candidateSha256': hashlib.sha256(args.analyzer_package.read_bytes()).hexdigest(), 'results': results,
            'elapsedSeconds': round(time.monotonic() - started, 3), 'contract': marker,
            'generatedPolicySha256': {name: hashlib.sha256((owner / 'scripts' / name).read_bytes()).hexdigest()
                                      for name in ('ProgramKit.Build.props', 'ProgramKit.Build.targets')},
            'oldPublishedPackageControl': 'executed' if args.released_package else 'not supplied; no current-public-package build claim'}, indent=2), encoding='utf-8')
        print('Generated source-readability policy rejected manual violations/disabled enforcement and accepted corrected native source: ' + str(directory))


if __name__ == '__main__':
    main()
