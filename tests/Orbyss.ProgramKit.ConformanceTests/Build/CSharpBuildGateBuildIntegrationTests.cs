using System.Diagnostics;
using System.IO.Compression;
using System.Security;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.ConformanceTests.DotNet;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
[DoNotParallelize]
public sealed class CSharpBuildGateBuildIntegrationTests
{
    [TestMethod]
    [DataRow("build")]
    [DataRow("test")]
    [DataRow("pack")]
    [DataRow("publish")]
    [DataRow("generated-project-verify")]
    public void DirectImportAutomaticallyRunsEveryFiniteCommandProfile(
        string command)
    {
        using TemporaryTestDirectory temporary =
            new("program-kit-csharp-build-gate-command-");
        var project = WriteFixture(temporary.FullName, command, "valid");

        var result = Run(temporary.FullName, "msbuild", project, "/t:CoreCompile");

        Assert.AreEqual(0, result.ExitCode, result.Output);
        var preCompilerLock = Directory
            .EnumerateFiles(
                Path.Combine(temporary.FullName, "obj"),
                "pre-compiler-inputs.lock",
                SearchOption.AllDirectories)
            .Single();
        Assert.Contains(
            $"command|{command}",
            File.ReadAllText(preCompilerLock));
        Assert.HasCount(
            1,
            Directory.EnumerateFiles(
                Path.Combine(temporary.FullName, "obj"),
                "*.json",
                SearchOption.AllDirectories)
                .Where(path => path.Contains(
                    $"{Path.DirectorySeparatorChar}participation" +
                    Path.DirectorySeparatorChar,
                    StringComparison.Ordinal)));
    }

    [TestMethod]
    [DataRow("disabled", "PKCG100")]
    [DataRow("substituted", "PKCG100")]
    [DataRow("duplicate-analyzer", "PKCG100")]
    [DataRow("duplicate-activation", "PKCG100")]
    [DataRow("demoted", "PKCG100")]
    [DataRow("extra-input", "PKCG100")]
    [DataRow("private-analyzer", "PKCG100")]
    [DataRow("missing-receipt", "PKCG200")]
    [DataRow("wrong-receipt", "PKCG200")]
    public void TamperingFailsClosedAtTheOwningMechanicsLayer(
        string scenario,
        string diagnostic)
    {
        using TemporaryTestDirectory temporary =
            new("program-kit-csharp-build-gate-tamper-");
        var project = WriteFixture(temporary.FullName, "build", scenario);

        var result = Run(temporary.FullName, "msbuild", project, "/t:CoreCompile");

        Assert.AreNotEqual(0, result.ExitCode, result.Output);
        Assert.Contains(diagnostic, result.Output);
    }

    [TestMethod]
    public void ExactGateEstablishmentExceptionEmitsNonExecutionReceipt()
    {
        using TemporaryTestDirectory temporary =
            new("program-kit-csharp-build-gate-exception-");
        var project = WriteFixture(
            temporary.FullName,
            "build",
            "valid-exception");

        var result = Run(temporary.FullName, "msbuild", project, "/t:CoreCompile");

        Assert.AreEqual(0, result.ExitCode, result.Output);
        var receipts = Directory
            .EnumerateFiles(
                Path.Combine(temporary.FullName, "obj"),
                "*.json",
                SearchOption.AllDirectories)
            .ToArray();
        Assert.HasCount(1, receipts);
        Assert.Contains(
            "\"kind\":\"temporary-exception-use\"",
            File.ReadAllText(receipts[0]));
        Assert.IsEmpty(Directory
            .EnumerateDirectories(
                Path.Combine(temporary.FullName, "obj"),
                "participation",
                SearchOption.AllDirectories)
            .ToArray());
    }

    [TestMethod]
    public void ExpiredExceptionFailsClosedInsteadOfRunningOrSkipping()
    {
        using TemporaryTestDirectory temporary =
            new("program-kit-csharp-build-gate-expired-");
        var project = WriteFixture(
            temporary.FullName,
            "build",
            "expired-exception");

        var result = Run(temporary.FullName, "msbuild", project, "/t:CoreCompile");

        Assert.AreNotEqual(0, result.ExitCode, result.Output);
        Assert.Contains("PKCG100", result.Output);
        Assert.Contains("expired", result.Output);
    }

    [TestMethod]
    public void PackageHasOnlyDirectBuildAndTaskAssets()
    {
        using TemporaryTestDirectory temporary =
            new("program-kit-csharp-build-gate-pack-");
        var project = BuildProjectPath();
        var result = Run(
            ConformanceInputs.ProgramKitRoot,
            "pack",
            project,
            "--no-restore",
            "--configuration",
            "Debug",
            "--output",
            temporary.FullName);
        Assert.AreEqual(0, result.ExitCode, result.Output);

        var package = Directory.EnumerateFiles(
            temporary.FullName,
            "*.nupkg").Single();
        using var archive = ZipFile.OpenRead(package);
        var entries = archive.Entries
            .Select(entry => entry.FullName.Replace('\\', '/'))
            .ToArray();
        Assert.Contains(
            "build/Orbyss.ProgramKit.CSharpBuildGates.Build.props",
            entries);
        Assert.Contains(
            "build/Orbyss.ProgramKit.CSharpBuildGates.Build.targets",
            entries);
        Assert.Contains(
            "tools/net10.0/Orbyss.ProgramKit.CSharpBuildGates.Build.dll",
            entries);
        Assert.IsEmpty(entries.Where(entry =>
            entry.StartsWith("lib/", StringComparison.OrdinalIgnoreCase) ||
            entry.StartsWith("ref/", StringComparison.OrdinalIgnoreCase) ||
            entry.StartsWith("runtime/", StringComparison.OrdinalIgnoreCase) ||
            entry.StartsWith(
                "buildTransitive/",
                StringComparison.OrdinalIgnoreCase)).ToArray());
    }

    [TestMethod]
    public void ManifestAndVersionMapBindTheExactBuildMechanicsSource()
    {
        var manifestPath = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "extensions",
            "reusable-csharp-build-gates",
            "build-package-manifest.json");
        using var manifest = JsonDocument.Parse(File.ReadAllBytes(manifestPath));
        var inventory = manifest.RootElement.GetProperty("sourceInventory");
        var paths = inventory.GetProperty("paths")
            .EnumerateArray()
            .Select(element => element.GetString()
                ?? throw new InvalidOperationException(
                    "Source inventory paths cannot be null."))
            .ToArray();
        Assert.AreSequenceEqual(
            paths.Order(StringComparer.Ordinal),
            paths);

        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var path in paths)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(path));
            hash.AppendData([0]);
            hash.AppendData(File.ReadAllBytes(Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                path.Replace('/', Path.DirectorySeparatorChar))));
            hash.AppendData([0]);
        }

        var sourceDigest = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(hash.GetHashAndReset()));
        Assert.AreEqual(
            inventory.GetProperty("digest").GetString(),
            sourceDigest);

        var manifestDigest = string.Concat(
            "sha256:",
            FileDigest(manifestPath));
        var versionMap = File.ReadAllText(Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "extensions",
            "reusable-csharp-build-gates",
            "build-version-map.json"));
        Assert.AreEqual(
            5,
            versionMap.Split(
                manifestDigest,
                StringSplitOptions.None).Length - 1);
    }

    private static string WriteFixture(
        string root,
        string command,
        string scenario)
    {
        var projectPath = Path.Combine(root, "Consumer.proj");
        var taskAssembly = TaskAssemblyPath();
        Assert.IsTrue(File.Exists(taskAssembly), taskAssembly);
        var selectedAnalyzer = scenario == "private-analyzer"
            ? PrivateAnalyzerPath()
            : taskAssembly;
        Assert.IsTrue(File.Exists(selectedAnalyzer), selectedAnalyzer);
        var projectDigest = FileDigest(projectPath);
        var isTest = command == "test" ? "true" : "false";
        var isPacking = command == "pack" ? "true" : "false";
        var isPublishing = command == "publish" ? "true" : "false";
        var generatedBinding = command == "generated-project-verify"
            ? "1.0.0"
            : string.Empty;
        var runAnalyzers = scenario == "disabled" ? "false" : "true";
        var assemblyDigest = scenario == "substituted"
            ? new string('b', 64)
            : FileDigest(selectedAnalyzer);
        var warningsNotAsErrors = scenario == "demoted"
            ? "CNS0001"
            : string.Empty;
        var existingAnalyzer = scenario == "duplicate-analyzer"
            ? $"<Analyzer Include=\"{Xml(selectedAnalyzer)}\" />"
            : string.Empty;
        var duplicateActivation = scenario == "duplicate-activation"
            ? Activation(command, "work-unit")
            : string.Empty;
        var extraExpectedInput = scenario == "extra-input"
            ? $$"""
                <ProgramKitCSharpGateExpectedInput Include="{{Xml(Path.Combine(root, "unexpected.txt"))}}">
                  <Kind>physical-source</Kind>
                  <Digest>sha256:{{FileDigest(Path.Combine(root, "unexpected.txt"))}}</Digest>
                </ProgramKitCSharpGateExpectedInput>
                """
            : string.Empty;
        var marker = scenario == "wrong-receipt"
            ? "wrong-marker"
            : "consumer-receipt:{nonce}:{project}:{profile}";
        var writeReceipt = scenario == "missing-receipt" ||
            scenario is "valid-exception" or "expired-exception"
            ? string.Empty
            : """
              <MakeDir Directories="$(_ProgramKitCSharpGateInvocationRoot)\generated\Fake" />
              <WriteLinesToFile
                File="$(_ProgramKitCSharpGateInvocationRoot)\generated\Fake\Receipt.$(_ProgramKitCSharpGateNonce).cs"
                Lines="consumer-receipt:$(_ProgramKitCSharpGateNonce):pkid:profile:consumer:project:work-unit"
                Overwrite="true" />
              """;
        var boundary = scenario is "valid-exception" or "expired-exception"
            ? "gate-establishment"
            : "work-unit";
        var exception = scenario switch
        {
            "valid-exception" => Exception(
                DateTimeOffset.UtcNow.AddDays(-1),
                DateTimeOffset.UtcNow.AddDays(1)),
            "expired-exception" => Exception(
                DateTimeOffset.UtcNow.AddDays(-2),
                DateTimeOffset.UtcNow.AddDays(-1)),
            _ => string.Empty,
        };

        File.WriteAllText(Path.Combine(root, "unexpected.txt"), "unexpected");
        var bindingPath = Path.Combine(root, "gate-binding.props");
        var project = $$"""
            <Project>
              <PropertyGroup>
                <ProgramKitCSharpGateEnabled>true</ProgramKitCSharpGateEnabled>
                <ProgramKitCSharpGateTaskAssembly>{{Xml(taskAssembly)}}</ProgramKitCSharpGateTaskAssembly>
                <ProgramKitCSharpGateProjectProfileId>pkid:profile:consumer:project</ProgramKitCSharpGateProjectProfileId>
                <ProgramKitCSharpGateSourceProfileId>pkid:profile:consumer:source</ProgramKitCSharpGateSourceProfileId>
                <ProgramKitCSharpGateImplementationBoundary>{{boundary}}</ProgramKitCSharpGateImplementationBoundary>
                <ProgramKitCSharpGateVerificationProfile>work-unit</ProgramKitCSharpGateVerificationProfile>
                <ProgramKitCSharpGateSelectionLockDigest>sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</ProgramKitCSharpGateSelectionLockDigest>
                <ProgramKitCSharpGateCompilerRoslynVersion>5.0.0</ProgramKitCSharpGateCompilerRoslynVersion>
                <ProgramKitCSharpGateGeneratedProjectBinding>{{generatedBinding}}</ProgramKitCSharpGateGeneratedProjectBinding>
                <IntermediateOutputPath>{{Xml(Path.Combine(root, "obj"))}}\</IntermediateOutputPath>
                <TargetFramework>net10.0</TargetFramework>
                <Configuration>Debug</Configuration>
                <NETCoreSdkVersion>10.0.302</NETCoreSdkVersion>
                <LangVersion>14.0</LangVersion>
                <IsTestProject>{{isTest}}</IsTestProject>
                <_IsPacking>{{isPacking}}</_IsPacking>
                <_IsPublishing>{{isPublishing}}</_IsPublishing>
                <RunAnalyzers>{{runAnalyzers}}</RunAnalyzers>
                <RunAnalyzersDuringBuild>true</RunAnalyzersDuringBuild>
                <CodeAnalysisTreatWarningsAsErrors>true</CodeAnalysisTreatWarningsAsErrors>
                <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
                <WarningsNotAsErrors>{{warningsNotAsErrors}}</WarningsNotAsErrors>
              </PropertyGroup>
              <Import Project="{{Xml(BuildPropsPath())}}" />
              <Import Project="{{Xml(bindingPath)}}" />
              <Target Name="CoreCompile">
                {{writeReceipt}}
              </Target>
              <Import Project="{{Xml(BuildTargetsPath())}}" />
            </Project>
            """;
        File.WriteAllText(projectPath, project, Encoding.UTF8);
        projectDigest = FileDigest(projectPath);
        File.WriteAllText(
            bindingPath,
            $$"""
            <Project>
              <ItemGroup>
                <ProgramKitCSharpGateAnalyzer Include="{{Xml(selectedAnalyzer)}}">
                  <ComponentId>pkid:analyzer:consumer:boundary</ComponentId>
                  <Kind>consumer-owned</Kind>
                  <AssemblyDigest>sha256:{{assemblyDigest}}</AssemblyDigest>
                  <HasRuntimeAssets>false</HasRuntimeAssets>
                  <HasBuildTransitiveAssets>false</HasBuildTransitiveAssets>
                  <ReceiptIdentity>pkid:receipt:consumer:boundary</ReceiptIdentity>
                  <ReceiptRelativePathTemplate>Fake/Receipt.{nonce}.cs</ReceiptRelativePathTemplate>
                  <ReceiptMarkerTemplate>{{marker}}</ReceiptMarkerTemplate>
                  <DiagnosticIds>CNS0001</DiagnosticIds>
                </ProgramKitCSharpGateAnalyzer>
                {{Activation(command, boundary)}}
                {{duplicateActivation}}
                {{exception}}
                <ProgramKitCSharpGateExpectedInput Include="{{Xml(projectPath)}}">
                  <Kind>project</Kind>
                  <Digest>sha256:{{projectDigest}}</Digest>
                </ProgramKitCSharpGateExpectedInput>
                {{extraExpectedInput}}
                {{existingAnalyzer}}
              </ItemGroup>
            </Project>
            """,
            Encoding.UTF8);

        return projectPath;
    }

    private static string Activation(string command, string boundary) =>
        $$"""
            <ProgramKitCSharpGateActivation Include="pkid:analyzer:consumer:boundary">
              <ProjectProfileId>pkid:profile:consumer:project</ProjectProfileId>
              <SourceProfileId>pkid:profile:consumer:source</SourceProfileId>
              <Command>{{command}}</Command>
              <Boundary>{{boundary}}</Boundary>
              <VerificationProfile>work-unit</VerificationProfile>
            </ProgramKitCSharpGateActivation>
            """;

    private static string Exception(
        DateTimeOffset activated,
        DateTimeOffset expires) =>
        $$"""
            <ProgramKitCSharpGateTemporaryException Include="pkid:exception:consumer:establishment">
              <AnalyzerComponentId>pkid:analyzer:consumer:boundary</AnalyzerComponentId>
              <ProjectProfileId>pkid:profile:consumer:project</ProjectProfileId>
              <SourceProfileId>pkid:profile:consumer:source</SourceProfileId>
              <Command>build</Command>
              <Boundary>gate-establishment</Boundary>
              <VerificationProfile>work-unit</VerificationProfile>
              <ExceptionDigest>sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc</ExceptionDigest>
              <HumanAuthority>pkid:approval:consumer:establishment</HumanAuthority>
              <CompensatingVerification>pkid:evidence:consumer:establishment</CompensatingVerification>
              <ActivatedAt>{{activated:O}}</ActivatedAt>
              <ExpiresAt>{{expires:O}}</ExpiresAt>
              <MaximumUses>1</MaximumUses>
              <ObservedUses>0</ObservedUses>
              <ConditionKind>gate-establishment-boundary</ConditionKind>
              <RequiredBoundary>gate-establishment</RequiredBoundary>
            </ProgramKitCSharpGateTemporaryException>
            """;

    private static (int ExitCode, string Output) Run(
        string workingDirectory,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start dotnet.");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        process.WaitForExit();
        Task.WaitAll(output, error);
        return (
            process.ExitCode,
            string.Concat(output.Result, Environment.NewLine, error.Result));
    }

    private static string FileDigest(string path) =>
        File.Exists(path)
            ? Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)))
            : new string('0', 64);

    private static string Xml(string value) =>
        SecurityElement.Escape(value) ??
        throw new InvalidOperationException("Could not XML-escape a path.");

    private static readonly Lazy<string> ProvisionedTaskAssembly = new(() =>
        BuildDebugAssembly(
            BuildProjectPath(),
            Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                "src",
                "Orbyss.ProgramKit.CSharpBuildGates.Build",
                "bin",
                "Debug",
                "net10.0",
                "Orbyss.ProgramKit.CSharpBuildGates.Build.dll")));

    private static readonly Lazy<string> ProvisionedPrivateAnalyzer = new(() =>
        BuildDebugAssembly(
            Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                "tools",
                "Orbyss.ProgramKit.CSharpGate",
                "Orbyss.ProgramKit.CSharpGate.csproj"),
            Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                "tools",
                "Orbyss.ProgramKit.CSharpGate",
                "bin",
                "Debug",
                "net10.0",
                "Orbyss.ProgramKit.CSharpGate.dll")));

    private static string TaskAssemblyPath() => ProvisionedTaskAssembly.Value;

    private static string PrivateAnalyzerPath() => ProvisionedPrivateAnalyzer.Value;

    private static string BuildDebugAssembly(string project, string assembly)
    {
        var build = Run(
            ConformanceInputs.ProgramKitRoot,
            "build",
            project,
            "--configuration",
            "Debug",
            "--no-restore",
            "--nologo");
        Assert.AreEqual(0, build.ExitCode, build.Output);
        Assert.IsTrue(File.Exists(assembly), assembly);
        return assembly;
    }

    private static string BuildProjectPath() =>
        Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "src",
            "Orbyss.ProgramKit.CSharpBuildGates.Build",
            "Orbyss.ProgramKit.CSharpBuildGates.Build.csproj");

    private static string BuildPropsPath() =>
        Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "src",
            "Orbyss.ProgramKit.CSharpBuildGates.Build",
            "build",
            "Orbyss.ProgramKit.CSharpBuildGates.Build.props");

    private static string BuildTargetsPath() =>
        Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "src",
            "Orbyss.ProgramKit.CSharpBuildGates.Build",
            "build",
            "Orbyss.ProgramKit.CSharpBuildGates.Build.targets");
}
