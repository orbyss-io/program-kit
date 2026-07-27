using System.Collections.Immutable;
using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.Operations.Contracts;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

[TestClass]
public sealed class ConsoleCommandDispatchConformanceTests
{
    private static readonly string[] ExpectedLifecycle =
    [
        "start",
        "stop|cancellable=true",
    ];

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task GeneratedConsumerDispatchesExactProcessCodesAndFailsClosed()
    {
        using TemporaryTestDirectory temporary = new(
            "program-kit-console-command-");
        var inputRoot = Directory.CreateDirectory(
            Path.Combine(temporary.FullName, "input")).FullName;
        var firstGeneration = Path.Combine(
            temporary.FullName,
            "generated-first");
        var secondGeneration = Path.Combine(
            temporary.FullName,
            "generated-second");
        var hostIdentity = await WriteGenerationInputsAsync(
            inputRoot,
            TestContext.CancellationToken);

        await GenerateAsync(
            inputRoot,
            firstGeneration,
            hostIdentity,
            TestContext.CancellationToken);
        await GenerateAsync(
            inputRoot,
            secondGeneration,
            hostIdentity,
            TestContext.CancellationToken);
        AssertGenerationTreesEqual(firstGeneration, secondGeneration);
        AssertGeneratedIntegrity(firstGeneration);

        CopyConsumerFixture(firstGeneration);
        var restore = await RunDotNetAsync(
            firstGeneration,
            TestContext.CancellationToken,
            "restore",
            "GeneratedHost.csproj",
            "--use-lock-file",
            "--nologo");
        AssertProcessSucceeded("generated consumer restore", restore);
        var build = await RunDotNetAsync(
            firstGeneration,
            TestContext.CancellationToken,
            "build",
            "GeneratedHost.csproj",
            "--configuration",
            "Release",
            "--no-restore",
            "--nologo");
        AssertProcessSucceeded("generated consumer build", build);

        var gateRestore = await RunDotNetAsync(
            firstGeneration,
            TestContext.CancellationToken,
            "restore",
            "ConsoleCommandConsumer.Gate.csproj",
            "--use-lock-file",
            "--nologo",
            string.Concat(
                "--property:ProgramKitBuildRoot=",
                ConformanceInputs.ProgramKitRoot));
        AssertProcessSucceeded("generated consumer source-gate restore", gateRestore);
        var gateBuild = await RunDotNetAsync(
            firstGeneration,
            TestContext.CancellationToken,
            "build",
            "ConsoleCommandConsumer.Gate.csproj",
            "--configuration",
            "Release",
            "--no-restore",
            "--nologo",
            string.Concat(
                "--property:ProgramKitBuildRoot=",
                ConformanceInputs.ProgramKitRoot));
        AssertProcessSucceeded("generated consumer source-gate build", gateBuild);

        var application = Path.Combine(
            firstGeneration,
            "bin",
            "Release",
            "net10.0",
            "GeneratedHost.dll");
        Assert.IsTrue(File.Exists(application), application);
        for (var exitCode = 0; exitCode <= 3; exitCode++)
        {
            var lifecyclePath = LifecyclePath(
                temporary,
                string.Concat("return-", exitCode.ToString(
                    CultureInfo.InvariantCulture)));
            var result = await RunGeneratedAsync(
                application,
                firstGeneration,
                lifecyclePath,
                "single",
                TestContext.CancellationToken,
                "probe",
                "run",
                exitCode.ToString(CultureInfo.InvariantCulture),
                "--mode=return",
                "--value=canonical-value");

            Assert.AreEqual(exitCode, result.ExitCode, result.Output);
            Assert.Contains(
                string.Concat(
                    "dispatch|command=probe run|argument=",
                    exitCode.ToString(CultureInfo.InvariantCulture),
                    "|mode=return|value=canonical-value|cancelled=false|" +
                    "service=constructor-injected"),
                result.Output);
            AssertLifecycleStartedAndStopped(lifecyclePath);
        }

        var invalidLifecycle = LifecyclePath(temporary, "invalid");
        var invalid = await RunGeneratedAsync(
            application,
            firstGeneration,
            invalidLifecycle,
            "missing",
            TestContext.CancellationToken,
            "probe",
            "run",
            "not-an-int");
        Assert.AreEqual(2, invalid.ExitCode, invalid.Output);
        Assert.Contains("PKNETC009", invalid.Output);
        Assert.IsFalse(File.Exists(invalidLifecycle));

        var helpLifecycle = LifecyclePath(temporary, "help");
        var help = await RunGeneratedAsync(
            application,
            firstGeneration,
            helpLifecycle,
            "missing",
            TestContext.CancellationToken,
            "--help");
        Assert.AreEqual(0, help.ExitCode, help.Output);
        Assert.Contains("probe run", help.Output);
        Assert.IsFalse(File.Exists(helpLifecycle));

        var completionLifecycle = LifecyclePath(temporary, "completion");
        var completion = await RunGeneratedAsync(
            application,
            firstGeneration,
            completionLifecycle,
            "missing",
            TestContext.CancellationToken,
            "--complete",
            "probe");
        Assert.AreEqual(0, completion.ExitCode, completion.Output);
        Assert.Contains("probe run", completion.Output);
        Assert.IsFalse(File.Exists(completionLifecycle));

        foreach (var registration in new[] { "missing", "duplicate" })
        {
            var lifecyclePath = LifecyclePath(
                temporary,
                registration);
            var result = await RunGeneratedAsync(
                application,
                firstGeneration,
                lifecyclePath,
                registration,
                TestContext.CancellationToken,
                "probe",
                "run",
                "0");

            Assert.AreNotEqual(0, result.ExitCode, result.Output);
            Assert.Contains(
                "Exactly one IProgramKitConsoleCommandDispatcher registration is required.",
                result.Output);
            Assert.IsFalse(
                File.Exists(lifecyclePath),
                string.Concat(
                    registration,
                    " registration started hosted behavior."));
        }

        var cancellationLifecycle = LifecyclePath(
            temporary,
            "cancellation");
        var cancellation = await RunGeneratedAsync(
            application,
            firstGeneration,
            cancellationLifecycle,
            "single",
            TestContext.CancellationToken,
            "probe",
            "run",
            "3",
            "--mode=cancel");
        Assert.AreEqual(3, cancellation.ExitCode, cancellation.Output);
        Assert.Contains("|cancelled=true|", cancellation.Output);
        AssertLifecycleStartedAndStopped(cancellationLifecycle);

        var failureLifecycle = LifecyclePath(
            temporary,
            "dispatcher-failure");
        var failure = await RunGeneratedAsync(
            application,
            firstGeneration,
            failureLifecycle,
            "single",
            TestContext.CancellationToken,
            "probe",
            "run",
            "3",
            "--mode=throw");
        Assert.AreNotEqual(0, failure.ExitCode, failure.Output);
        Assert.Contains(
            "Fixture dispatcher failure after host start.",
            failure.Output);
        AssertLifecycleStartedAndStopped(failureLifecycle);

        var dependencies = File.ReadAllText(
            Path.Combine(
                firstGeneration,
                "bin",
                "Release",
                "net10.0",
                "GeneratedHost.deps.json"));
        Assert.DoesNotContain("Orbyss.ProgramKit.", dependencies);
    }

    private static async Task<ProgramKitIdentifier> WriteGenerationInputsAsync(
        string inputRoot,
        CancellationToken cancellationToken)
    {
        var serializer = CreateSerializer();
        var limits = JsonSerializationLimits.Default;
        var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
        var versionInput = "{}"u8.ToArray();
        var versionMapRevision = new ArtifactReference(
            new ProgramKitIdentifier(
                "pkid:version-map:fixture:console-command-consumer"),
            new SemanticVersion("1.0.0"),
            Digest(versionInput));
        var versionSelectionRevision = new ArtifactReference(
            new ProgramKitIdentifier(
                "pkid:version-selection:fixture:console-command-consumer"),
            new SemanticVersion("1.0.0"),
            Digest(versionInput));
        var shellIdentity = new ProgramKitIdentifier(
            "pkid:shell:fixture:console-command-consumer");
        var hostIdentity = new ProgramKitIdentifier(
            "pkid:host:fixture:console-command-consumer");
        var operationRevision = Reference(
            "pkid:operation:fixture:console-command-probe",
            '1');
        var argumentSchema = Reference(
            "pkid:schema:fixture:console-command-exit-code",
            '2');
        var resultSchema = Reference(
            "pkid:schema:fixture:console-command-result",
            '3');
        var generatorRevision = Reference(
            "pkid:generator:fixture:console-command-host",
            '4');
        var compatibility = Compatibility();
        var operation = new OperationContractDescriptor(
            operationRevision,
            [argumentSchema],
            [
                new OperationResultContract(
                    resultSchema,
                    OperationResultDisposition.Terminal),
            ],
            [],
            [],
            [],
            null,
            null,
            OperationExpectedRevisionPolicy.Unsupported,
            OperationIdempotencyPolicy.Unsupported,
            OperationCancellationPolicy.Cooperative,
            OperationProgressPolicy.Unsupported,
            compatibility,
            new OperationDeprecation(false, null));
        var host = new DotNetHostDefinition(
            hostIdentity,
            new SemanticVersion("1.0.0"),
            DotNetHostKind.Console,
            Reference(
                "pkid:profile:fixture:dotnet-10",
                '5'),
            generatorRevision,
            [shellIdentity],
            [],
            [
                Package("CShells", "0.0.28", '6'),
                Package(
                    "Microsoft.Extensions.Hosting",
                    "10.0.10",
                    '7'),
            ],
            [
                new DotNetOperationBinding(
                    operation,
                    Reference(
                        "pkid:projection:fixture:console-command-probe",
                        '8')),
            ],
            [],
            [],
            [],
            null,
            compatibility);
        var shell = new DotNetShellDocument(
            "pkid:schema:program-kit:dotnet-shell@11.0.0",
            new SemanticVersion("11.0.0"),
            versionMapRevision,
            versionSelectionRevision,
            new DotNetShellComposition(
                "cshells",
                new SemanticVersion("0.0.28"),
                [
                    new DotNetShellSelection(
                        shellIdentity,
                        []),
                ]),
            [],
            new DotNetJsonSerializationSelection(
                ImmutableArray<JsonSerializationProfileRef>.Empty,
                ImmutableArray<JsonSerializationContributionRef>.Empty),
            [host],
            compatibility);
        var shellBytes = serializer.Write(
            shell,
            profile,
            limits).ToArray();
        var shellRevision = new ArtifactReference(
            new ProgramKitIdentifier(
                "pkid:shell-document:fixture:console-command-consumer"),
            new SemanticVersion("1.0.0"),
            Digest(shellBytes));
        var document = new OpenConsoleDocument(
            "pkid:schema:program-kit:open-console@1.0.0",
            new SemanticVersion("1.0.0"),
            new OpenConsoleInfo(
                "Console command consumer",
                "Exercises generated consumer dispatch.",
                new SemanticVersion("1.0.0")),
            new ArtifactReference(
                hostIdentity,
                host.Version,
                Digest('9')),
            new OpenConsoleParsing(
                true,
                "--",
                true,
                true,
                "invariant",
                "bounded-by-occurrence"),
            [],
            [
                new OpenConsoleCommand(
                    operationRevision,
                    ["probe", "run"],
                    [["execute"]],
                    "Returns the requested fixture exit code.",
                    [
                        new OpenConsoleArgument(
                            0,
                            "exit-code",
                            "int32",
                            new ConsoleValueArity(1, 1),
                            new ConsoleOccurrence(1, 1),
                            true,
                            null,
                            argumentSchema,
                            "Process exit code returned by the dispatcher."),
                    ],
                    [
                        ValueOption(
                            "mode",
                            "m",
                            "return",
                            "Fixture dispatch mode."),
                        ValueOption(
                            "value",
                            "v",
                            "fixture-value",
                            "Canonical value observed by the dispatcher."),
                    ],
                    null,
                    null,
                    null,
                    [
                        new OpenConsoleExitCode(0, "Fixture success.", []),
                        new OpenConsoleExitCode(1, "Fixture result one.", []),
                        new OpenConsoleExitCode(2, "Invalid invocation or fixture result two.", []),
                        new OpenConsoleExitCode(3, "Fixture result three.", []),
                    ],
                    Reference(
                        "pkid:authority:fixture:console-command-probe",
                        'a'),
                    [
                        new OpenConsoleExample(
                            [
                                "probe",
                                "run",
                                "3",
                                "--value=example",
                            ],
                            "Returns process code three."),
                    ],
                    null),
            ],
            new OpenConsoleHelp("help", "h", 0),
            new OpenConsoleCompletion("complete", true, true),
            compatibility,
            new OpenConsoleProvenance(
                shellRevision,
                generatorRevision,
                [operationRevision]));
        var documentBytes = serializer.Write(
            document,
            profile,
            limits).ToArray();
        var documentRevision = new ArtifactReference(
            new ProgramKitIdentifier(
                "pkid:document:fixture:console-command-consumer"),
            document.DocumentVersion,
            Digest(documentBytes));
        var manifest = new DotNetArtifactInputManifest(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            [
                new DotNetArtifactInputEntry(
                    versionMapRevision,
                    "inputs/version-map.json"),
                new DotNetArtifactInputEntry(
                    versionSelectionRevision,
                    "inputs/version-selection.json"),
                new DotNetArtifactInputEntry(
                    documentRevision,
                    "inputs/open-console.json"),
            ],
            [
                new DotNetHostDocumentInput(
                    hostIdentity,
                    documentRevision),
            ]);
        var inputs = Directory.CreateDirectory(
            Path.Combine(inputRoot, "inputs")).FullName;
        await File.WriteAllBytesAsync(
            Path.Combine(inputRoot, "shell.json"),
            shellBytes,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(inputs, "version-map.json"),
            versionInput,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(inputs, "version-selection.json"),
            versionInput,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(inputs, "open-console.json"),
            documentBytes,
            cancellationToken);
        await File.WriteAllBytesAsync(
            Path.Combine(inputRoot, "artifact-manifest.json"),
            serializer.Write(
                manifest,
                profile,
                limits).ToArray(),
            cancellationToken);
        return hostIdentity;
    }

    private static async Task GenerateAsync(
        string inputRoot,
        string outputRoot,
        ProgramKitIdentifier hostIdentity,
        CancellationToken cancellationToken)
    {
        RecordingCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);
        var exitCode = await application.RunAsync(
            [
                "dotnet",
                "generate-host",
                "console",
                "--shell",
                Path.Combine(inputRoot, "shell.json"),
                "--host",
                hostIdentity.Value,
                "--artifact-manifest",
                Path.Combine(inputRoot, "artifact-manifest.json"),
                "--output",
                outputRoot,
            ],
            cancellationToken);

        Assert.AreEqual(
            CommandExitCode.Success,
            exitCode,
            Encoding.UTF8.GetString(console.StandardError));
        Assert.IsEmpty(console.StandardError);
    }

    private static void AssertGenerationTreesEqual(
        string firstRoot,
        string secondRoot)
    {
        var first = RelativeFiles(firstRoot);
        var second = RelativeFiles(secondRoot);
        Assert.AreSequenceEqual(first, second);
        foreach (var relativePath in first)
        {
            Assert.AreSequenceEqual(
                File.ReadAllBytes(Path.Combine(firstRoot, relativePath)),
                File.ReadAllBytes(Path.Combine(secondRoot, relativePath)),
                relativePath);
        }
    }

    private static void AssertGeneratedIntegrity(string generationRoot)
    {
        var project = File.ReadAllText(
            Path.Combine(generationRoot, "GeneratedHost.csproj"));
        Assert.Contains(
            "PackageReference Include=\"CShells\" Version=\"[0.0.28]\"",
            project);
        Assert.Contains(
            "PackageReference Include=\"Microsoft.Extensions.Hosting\" " +
            "Version=\"[10.0.10]\"",
            project);
        Assert.DoesNotContain("CShells.", project);
        var generatedSources = Directory
            .EnumerateFiles(
                Path.Combine(generationRoot, "ProgramKitGenerated"),
                "*.cs",
                SearchOption.AllDirectories)
            .Select(File.ReadAllText)
            .ToArray();
        foreach (var generatedSource in generatedSources)
        {
            Assert.DoesNotContain(
                "Orbyss.ProgramKit.",
                generatedSource);
        }
        Assert.AreEqual(
            "sha256:0eb76edbb5379fae772be6b3df3f5db0659034bd7aecbe201727696f37109dbe",
            Digest(
                File.ReadAllBytes(
                    Path.Combine(
                        generationRoot,
                        "ProgramKitGenerated",
                        "Commands",
                        "GeneratedConsoleParser.cs"))).Value);
        Assert.AreEqual(
            "sha256:a95b7bf78aea54d000c580e033faca7638b66accbe87ee7e8a7e9ebc734d1f61",
            Digest(
                File.ReadAllBytes(
                    Path.Combine(
                        generationRoot,
                        "ProgramKitGenerated",
                        "Commands",
                        "GeneratedConsoleParseResult.cs"))).Value);
        var dispatchLock = File.ReadAllText(
            Path.Combine(
                generationRoot,
                "ProgramKitGenerated",
                "Commands",
                "console-command-dispatch.lock.json"));
        var evidence = File.ReadAllText(
            Path.Combine(
                generationRoot,
                "ProgramKitGenerated",
                "Evidence",
                "console-command-dispatch.evidence.json"));
        Assert.Contains(
            "\"dispatcherContractRevision\"",
            dispatchLock);
        Assert.Contains(
            "\"return-dispatcher-integer-unchanged\"",
            evidence);
    }

    private static void CopyConsumerFixture(string generationRoot)
    {
        var fixtureRoot = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "ConsoleCommandConsumer");
        var sourceRoot = Path.Combine(
            fixtureRoot,
            "ConsumerSource");
        foreach (var sourcePath in Directory.EnumerateFiles(
                     sourceRoot,
                     "*.cs",
                     SearchOption.AllDirectories))
        {
            var relativePath = Path.GetRelativePath(
                sourceRoot,
                sourcePath);
            var targetPath = Path.Combine(
                generationRoot,
                relativePath);
            Directory.CreateDirectory(
                Path.GetDirectoryName(targetPath)!);
            File.Copy(sourcePath, targetPath);
        }

        File.Copy(
            Path.Combine(
                fixtureRoot,
                "ConsoleCommandConsumer.Gate.csproj"),
            Path.Combine(
                generationRoot,
                "ConsoleCommandConsumer.Gate.csproj"));
        File.Copy(
            Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                "NuGet.Config"),
            Path.Combine(
                generationRoot,
                "NuGet.Config"));
    }

    private static async Task<ProcessResult> RunGeneratedAsync(
        string application,
        string workingDirectory,
        string lifecyclePath,
        string registration,
        CancellationToken cancellationToken,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new(
            Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
                ?? "dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        startInfo.ArgumentList.Add(application);
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        startInfo.Environment[
            "PROGRAM_KIT_CONSOLE_FIXTURE_REGISTRATION"] =
            registration;
        startInfo.Environment[
            "PROGRAM_KIT_CONSOLE_FIXTURE_LIFECYCLE"] =
            lifecyclePath;
        return await RunProcessAsync(
            startInfo,
            cancellationToken);
    }

    private static async Task<ProcessResult> RunDotNetAsync(
        string workingDirectory,
        CancellationToken cancellationToken,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new(
            Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
                ?? "dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        return await RunProcessAsync(
            startInfo,
            cancellationToken);
    }

    private static async Task<ProcessResult> RunProcessAsync(
        ProcessStartInfo startInfo,
        CancellationToken cancellationToken)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(45));
        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException(
                "The bounded fixture process did not start.");
        var standardOutput = process.StandardOutput.ReadToEndAsync(
            timeout.Token);
        var standardError = process.StandardError.ReadToEndAsync(
            timeout.Token);
        try
        {
            await process.WaitForExitAsync(timeout.Token);
        }
        catch (OperationCanceledException)
            when (!cancellationToken.IsCancellationRequested)
        {
            process.Kill(entireProcessTree: true);
            throw new TimeoutException(
                string.Concat(
                    "The fixture process exceeded its 45-second bound: ",
                    startInfo.FileName,
                    " ",
                    string.Join(" ", startInfo.ArgumentList)));
        }

        return new ProcessResult(
            process.ExitCode,
            string.Concat(
                await standardOutput,
                Environment.NewLine,
                await standardError));
    }

    private static void AssertProcessSucceeded(
        string operation,
        ProcessResult result) =>
        Assert.AreEqual(
            0,
            result.ExitCode,
            string.Concat(
                operation,
                Environment.NewLine,
                result.Output));

    private static void AssertLifecycleStartedAndStopped(
        string lifecyclePath)
    {
        Assert.IsTrue(File.Exists(lifecyclePath), lifecyclePath);
        var lifecycle = File.ReadAllLines(lifecyclePath);
        Assert.AreSequenceEqual(
            ExpectedLifecycle,
            lifecycle);
    }

    private static string LifecyclePath(
        TemporaryTestDirectory root,
        string name) =>
        Path.Combine(
            root.FullName,
            string.Concat("lifecycle-", name, ".txt"));

    private static ImmutableArray<string> RelativeFiles(
        string root) =>
        Directory
            .EnumerateFiles(
                root,
                "*",
                SearchOption.AllDirectories)
            .Select(path => Path.GetRelativePath(root, path))
            .Order(StringComparer.Ordinal)
            .ToImmutableArray();

    private static OpenConsoleOption ValueOption(
        string longName,
        string shortName,
        string defaultValue,
        string summary) =>
        new(
            longName,
            shortName,
            [],
            ConsoleOptionKind.Value,
            "string",
            new ConsoleValueArity(1, 1),
            new ConsoleOccurrence(0, 1),
            false,
            defaultValue,
            null,
            null,
            [],
            [],
            summary);

    private static ArtifactCompatibility Compatibility() =>
        new(
            new ProgramKitIdentifier(
                "pkid:policy:fixture:console-command-compatibility"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.Unknown,
                    []),
            ],
            new SemanticVersionRange("[1.0.0]"),
            new SemanticVersionRange("[1.0.0]"),
            []);

    private static DotNetPackageReference Package(
        string packageId,
        string version,
        char digest) =>
        new(
            packageId,
            new SemanticVersion(version),
            Digest(digest));

    private static ArtifactReference Reference(
        string identity,
        char digest) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            Digest(digest));

    private static Sha256Digest Digest(char value) =>
        new(string.Concat(
            "sha256:",
            new string(value, 64)));

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(content))));

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

}
