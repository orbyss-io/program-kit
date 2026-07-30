using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

[TestClass]
public sealed class CSharpGateSelectionLockProjectorTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void ExactNamedStateProducesDeterministicRequestAndRecomputedLock()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-gate-lock-projector-");
        var serializer = CreateSerializer();
        var definition = PrepareDefinition(temporary.FullName, serializer);
        var intent = Intent(definition);
        var sut = Projector(serializer);

        var first = sut.Scaffold(
            definition,
            "gate-definition.json",
            intent,
            temporary.FullName);
        var second = sut.Scaffold(
            definition,
            "gate-definition.json",
            intent,
            temporary.FullName);
        var firstBytes = serializer.Write(
            first,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        var secondBytes = serializer.Write(
            second,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        var boundBytes = serializer.Write(
            sut.Bind(first),
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        var candidateBytes = serializer.Write(
            first.CandidateLock,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);

        Assert.AreSequenceEqual(firstBytes.ToArray(), secondBytes.ToArray());
        Assert.AreSequenceEqual(
            candidateBytes.ToArray(),
            boundBytes.ToArray());
        Assert.HasCount(5, first.LocalAssets);
        Assert.HasCount(1, first.CandidateLock.ExpectedReceipts);
        Assert.AreEqual(
            "pkid:receipt:consumer:gate.project.boundary.work-unit",
            first.CandidateLock.ExpectedReceipts[0].ReceiptIdentity.Value);
    }

    [TestMethod]
    public void BindRejectsTamperedDigestAndChangedNamedAsset()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-gate-lock-tamper-");
        var serializer = CreateSerializer();
        var definition = PrepareDefinition(temporary.FullName, serializer);
        var sut = Projector(serializer);
        var request = sut.Scaffold(
            definition,
            "gate-definition.json",
            Intent(definition),
            temporary.FullName);
        var tampered = request with
        {
            CandidateLock = request.CandidateLock with
            {
                OutputDigest = Digest('f'),
            },
        };

        _ = Assert.ThrowsExactly<CSharpBuildGateOperationException>(
            () => sut.Bind(tampered));
        File.WriteAllText(
            Path.Combine(
                temporary.FullName,
                "src",
                "Consumer",
                "Service.cs"),
            "changed",
            new UTF8Encoding(false));
        _ = Assert.ThrowsExactly<CSharpBuildGateOperationException>(
            () => sut.Bind(request));
    }

    [TestMethod]
    public void ScaffoldRejectsDuplicateAndEscapingExplicitAssets()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-gate-lock-invalid-");
        var serializer = CreateSerializer();
        var definition = PrepareDefinition(temporary.FullName, serializer);
        var sut = Projector(serializer);
        var intent = Intent(definition);

        _ = Assert.ThrowsExactly<CSharpBuildGateOperationException>(() =>
            sut.Scaffold(
                definition,
                "gate-definition.json",
                intent with
                {
                    LocalAssets =
                    [
                        .. intent.LocalAssets,
                        .. intent.LocalAssets,
                    ],
                },
                temporary.FullName));
        _ = Assert.ThrowsExactly<CSharpBuildGateOperationException>(() =>
            sut.Scaffold(
                definition,
                "gate-definition.json",
                intent with
                {
                    LocalAssets =
                    [
                        new CSharpGateLockLocalAssetIntent(
                            CSharpGateLockInventoryKind.Reference,
                            "../escape.dll"),
                    ],
                },
                temporary.FullName));
    }

    [TestMethod]
    public void ReversedPrefixActivationNamesExactAdjacentCompositeKeys()
    {
        var definition = ReadFixture(CreateSerializer());
        var originalProject = definition.Profiles.Projects[0];
        var source = definition.Profiles.Inputs[0];
        var component = definition.AnalyzerComponents[0].Identity;
        var cli = new ProgramKitIdentifier("pkid:profile:consumer:cli");
        var cliTests =
            new ProgramKitIdentifier("pkid:profile:consumer:cli-tests");
        var cliProject = originalProject with { Identity = cli };
        var cliTestsProject = originalProject with { Identity = cliTests };
        var first = new CSharpGateActivation(
            cli,
            source.Identity,
            CSharpGateCommand.Build,
            CSharpGateImplementationBoundary.WorkUnit,
            CSharpGateVerificationProfileKind.WorkUnit,
            [component]);
        var second = first with { ProjectProfileId = cliTests };
        var reversed = definition with
        {
            Profiles = definition.Profiles with
            {
                Projects = [cliProject, cliTestsProject],
            },
            ActivationMatrix = definition.ActivationMatrix with
            {
                Activations = [first, second],
            },
        };

        CSharpBuildGateDefinitionValidator validator = new();
        var result = validator.Validate(reversed);
        var ordering = result.Diagnostics.Single(diagnostic =>
            diagnostic.Message.Contains(
                "adjacent key",
                StringComparison.Ordinal));

        Assert.Contains("pkid:profile:consumer:cli|", ordering.Message);
        Assert.Contains(
            "pkid:profile:consumer:cli-tests|",
            ordering.Message);
        Assert.IsLessThan(
            0,
            string.CompareOrdinal(
                CSharpBuildGateOrdering.ActivationKey(second),
            CSharpBuildGateOrdering.ActivationKey(first)));
    }

    [TestMethod]
    public async Task CliScaffoldAndBindProduceOnlyExplicitNewOutputs()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-gate-lock-cli-");
        var serializer = CreateSerializer();
        var definition = PrepareDefinition(temporary.FullName, serializer);
        var intentBytes = serializer.Write(
            Intent(definition),
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        var intentPath = Path.Combine(
            temporary.FullName,
            "lock-intent.json");
        await File.WriteAllBytesAsync(
            intentPath,
            intentBytes.ToArray(),
            TestContext.CancellationToken);
        var bindRequestPath = Path.Combine(
            temporary.FullName,
            "bind-request.json");
        var selectionLockPath = Path.Combine(
            temporary.FullName,
            "selection-lock.json");
        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);

        var scaffoldExit = await application.RunAsync(
        [
            "csharp-gate",
            "scaffold-lock",
            "gate-definition.json",
            "lock-intent.json",
            "--repository-root",
            temporary.FullName,
            "--output",
            "bind-request.json",
        ],
        TestContext.CancellationToken);
        var bindExit = await application.RunAsync(
        [
            "csharp-gate",
            "bind",
            bindRequestPath,
            "--output",
            selectionLockPath,
        ],
        TestContext.CancellationToken);

        Assert.AreEqual(
            CommandExitCode.Success,
            scaffoldExit,
            Encoding.UTF8.GetString(console.StandardError));
        Assert.AreEqual(
            CommandExitCode.Success,
            bindExit,
            Encoding.UTF8.GetString(console.StandardError));
        Assert.IsTrue(File.Exists(bindRequestPath));
        Assert.IsTrue(File.Exists(selectionLockPath));
        Assert.IsFalse(File.Exists(
            string.Concat(bindRequestPath, ".program-kit-stage")));
        Assert.IsFalse(File.Exists(
            string.Concat(selectionLockPath, ".program-kit-stage")));
    }

    private static CSharpBuildGateDefinitionDocument PrepareDefinition(
        string root,
        ProgramKitJsonSerializer serializer)
    {
        Write(root, "src/Consumer/Consumer.csproj", "<Project />");
        Write(root, "src/Consumer/Service.cs", "namespace Consumer;");
        Write(
            root,
            "analyzers/Consumer.Analyzers/Consumer.Analyzers.csproj",
            "<Project />");
        Write(root, "artifacts/Consumer.Analyzers.dll", "analyzer");
        var sourceDigest = FileDigest(
            root,
            "src/Consumer/Service.cs");
        var assemblyDigest = FileDigest(
            root,
            "artifacts/Consumer.Analyzers.dll");
        var definition = ReadFixture(serializer);
        definition = definition with
        {
            AnalyzerComponents =
            [
                definition.AnalyzerComponents[0] with
                {
                    Artifact = definition.AnalyzerComponents[0].Artifact with
                    {
                        AssemblyDigest = assemblyDigest,
                    },
                },
            ],
            Profiles = definition.Profiles with
            {
                Inputs =
                [
                    definition.Profiles.Inputs[0] with
                    {
                        Inventory =
                        [
                            new CSharpGateContentItem(
                                "src/Consumer/Service.cs",
                                sourceDigest),
                        ],
                    },
                ],
            },
        };
        var bytes = serializer.Write(
            definition,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        File.WriteAllBytes(
            Path.Combine(root, "gate-definition.json"),
            bytes.ToArray());
        return definition;
    }

    private static CSharpBuildGateDefinitionDocument ReadFixture(
        ProgramKitJsonSerializer serializer)
    {
        var path = Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "fixtures",
            "consumer-owned-build-gate-definition.json");
        return serializer.Read<CSharpBuildGateDefinitionDocument>(
            File.ReadAllBytes(path),
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
    }

    private static CSharpGateLockIntent Intent(
        CSharpBuildGateDefinitionDocument definition) =>
        new(
            "pkid:schema:program-kit:csharp-gate-lock-intent@0.1.0-alpha.1",
            new SemanticVersion("0.1.0-alpha.1"),
            new ProgramKitIdentifier(
                "pkid:selection-lock:consumer:software"),
            definition.Disposition,
            [],
            [
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:operation:program-kit:csharp-gate-verify"),
                    new SemanticVersion("0.1.0-alpha.1"),
                    Digest('e')),
            ],
            new SemanticVersion("10.0.302"),
            new SemanticVersion("5.0.0"),
            new SemanticVersion("14.0.0"),
            "net10.0",
            new ProgramKitIdentifier("pkid:receipt:consumer:gate"),
            [
                new CSharpGateLockLocalAssetIntent(
                    CSharpGateLockInventoryKind.Reference,
                    "artifacts/Consumer.Analyzers.dll"),
            ]);

    private static CSharpGateSelectionLockProjector Projector(
        ProgramKitJsonSerializer serializer) =>
        new(
            serializer,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits,
            new CSharpBuildGateDefinitionValidator(),
            new CSharpBuildGateSelectionLockAlpha1Validator());

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder jsonBuilder = new(registryFactory);
        CSharpGateJsonProfileRegistration registration = new();
        registration.Register(jsonBuilder);
        return new ProgramKitJsonSerializer(
            jsonBuilder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

    private static void Write(string root, string relativePath, string value)
    {
        var path = Path.Combine(
            root,
            relativePath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, value, new UTF8Encoding(false));
    }

    private static Sha256Digest FileDigest(
        string root,
        string relativePath)
    {
        using var stream = File.OpenRead(Path.Combine(
            root,
            relativePath.Replace('/', Path.DirectorySeparatorChar)));
        return new Sha256Digest(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(
                    System.Security.Cryptography.SHA256.HashData(stream))));
    }

    private static Sha256Digest Digest(char value) =>
        new(string.Concat("sha256:", new string(value, 64)));

    private static DirectoryInfo FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException(
            "The Program Kit repository root was not found.");
    }
}
