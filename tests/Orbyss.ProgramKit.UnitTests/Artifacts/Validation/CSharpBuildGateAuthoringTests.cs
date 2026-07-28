using System.Collections.Immutable;
using System.Diagnostics;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Composition.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Selections;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Operations.Scaffolding;
using Orbyss.ProgramKit.UnitTests.Artifacts.Validation.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

[TestClass]
public sealed class CSharpBuildGateAuthoringTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void RecipeBindingRequiresConsumerOwnedSemanticInputs()
    {
        var recipe = CSharpRuleRecipeCatalog.ForbidTypeNameSuffix;
        var valid = CreateRequest().RecipeBinding;

        Assert.IsEmpty(CSharpRuleRecipeBindingValidator.Validate(recipe, valid));

        var invalid = valid with
        {
            DiagnosticId = "PKCC001",
            Parameters = ImmutableSortedDictionary<string, string>.Empty,
            ApplicabilityProfiles = [],
            FixtureIds = [],
            CompatibilityClaims = [],
            SuppressionPolicy = string.Empty,
        };
        var errors = CSharpRuleRecipeBindingValidator.Validate(recipe, invalid);
        Assert.IsGreaterThanOrEqualTo(6, errors.Length);
        Assert.IsTrue(errors.Any(error =>
            error.Contains("Program Kit-reserved", StringComparison.Ordinal)));
        Assert.IsTrue(errors.Any(error =>
            error.Contains("Recipe parameters", StringComparison.Ordinal)));
    }

    [TestMethod]
    public void PlannerProducesGoldenStableBytesAndKeepsPublicOwnershipSeparate()
    {
        var first = ConsumerAnalyzerScaffoldPlanner.Plan(CreateRequest());
        var second = ConsumerAnalyzerScaffoldPlanner.Plan(CreateRequest());

        Assert.HasCount(7, first.Files);
        Assert.AreSequenceEqual(
            first.Files.Select(file => file.RelativePath),
            second.Files.Select(file => file.RelativePath));
        for (var index = 0; index < first.Files.Length; index++)
        {
            Assert.IsTrue(first.Files[index].Content.Span.SequenceEqual(
                second.Files[index].Content.Span));
        }

        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var file in first.Files)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(file.RelativePath));
            hash.AppendData([0]);
            hash.AppendData(file.Content.Span);
            hash.AppendData([0]);
        }

        Assert.AreEqual(
            "sha256:8bfba8e6e9c41cedf6b6f3109d37cf6655f3a818e536ce107a25bc66a8f89863",
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(hash.GetHashAndReset())));

        var analyzer = Read(first, "Rules/ACME0001Analyzer.cs");
        var receipt = Read(
            first,
            "Generation/Acme.Quality.AnalyzersParticipationReceiptGenerator.cs");
        var ownership = Read(first, "gate/ownership-manifest.json");
        var publicSelections = Read(first, "gate/public-analyzer-selections.json");
        Assert.Contains("ACME0001", analyzer);
        Assert.DoesNotContain("PKCC", analyzer);
        Assert.DoesNotContain("PKCS", analyzer);
        Assert.Contains("IIncrementalGenerator", receipt);
        Assert.Contains("pkid:owner:acme:quality", ownership);
        Assert.Contains("\"diagnosticId\": \"ACME0001\"", ownership);
        Assert.Contains("\"PKCC001\"", publicSelections);
        Assert.Contains(
            "pkid:domain:program-kit:generated-source-contract",
            publicSelections);
        Assert.DoesNotContain("ACME0001", publicSelections);
    }

    [TestMethod]
    public void PlannerRejectsTraversalAndPublicDiagnosticCollisions()
    {
        var request = CreateRequest();
        var traversal = request with
        {
            ProjectName = "../escape",
        };
        var duplicate = request with
        {
            PublicAnalyzerSelections =
            [
                request.PublicAnalyzerSelections[0],
                request.PublicAnalyzerSelections[0],
            ],
        };

        Assert.ThrowsExactly<ArgumentException>(() =>
            ConsumerAnalyzerScaffoldPlanner.Plan(traversal));
        var collision = Assert.ThrowsExactly<ArgumentException>(() =>
            ConsumerAnalyzerScaffoldPlanner.Plan(duplicate));
        Assert.Contains("selected more than once", collision.Message);
    }

    [TestMethod]
    public async Task FileSystemScaffoldIsTransactionalAndRefusesExistingOutput()
    {
        using var temporary = new AuthoringTemporaryDirectory();
        var output = Path.Combine(temporary.Path, "generated-analyzer");
        var service = new ConsumerAnalyzerScaffoldingService(
            new FileSystemConsumerAnalyzerScaffoldWorkspace());

        var plan = await service.ScaffoldAsync(
            CreateRequest(),
            output,
            TestContext.CancellationToken);

        Assert.HasCount(7, plan.Files);
        Assert.IsTrue(File.Exists(Path.Combine(
            output,
            "Rules",
            "ACME0001Analyzer.cs")));
        await Assert.ThrowsExactlyAsync<IOException>(async () =>
            await service.ScaffoldAsync(
                CreateRequest(),
                output,
                TestContext.CancellationToken));
    }

    [TestMethod]
    public async Task FailureAndCancellationRollbackEveryStagedFile()
    {
        var failedTransaction = new RecordingScaffoldTransaction(failWriteAt: 2);
        var failedService = new ConsumerAnalyzerScaffoldingService(
            new RecordingScaffoldWorkspace(failedTransaction));

        await Assert.ThrowsExactlyAsync<IOException>(async () =>
            await failedService.ScaffoldAsync(
                CreateRequest(),
                "unused",
                TestContext.CancellationToken));
        Assert.IsTrue(failedTransaction.RolledBack);
        Assert.IsFalse(failedTransaction.Committed);

        using var cancellation = new CancellationTokenSource();
        var cancelledTransaction = new RecordingScaffoldTransaction(
            cancelAfterFirstWrite: cancellation);
        var cancelledService = new ConsumerAnalyzerScaffoldingService(
            new RecordingScaffoldWorkspace(cancelledTransaction));
        await Assert.ThrowsExactlyAsync<OperationCanceledException>(async () =>
            await cancelledService.ScaffoldAsync(
                CreateRequest(),
                "unused",
                cancellation.Token));
        Assert.IsTrue(cancelledTransaction.RolledBack);
        Assert.IsFalse(cancelledTransaction.Committed);
    }

    [TestMethod]
    public void AuthoringAssemblyContainsNoAnalyzerOrGeneratorRegistration()
    {
        var assemblyPath = typeof(ConsumerAnalyzerScaffoldPlanner)
            .Assembly
            .Location;
        using var stream = File.OpenRead(assemblyPath);
        using var peReader = new PEReader(stream);
        var metadata = peReader.GetMetadataReader();
        var forbidden = new HashSet<string>(StringComparer.Ordinal)
        {
            "Microsoft.CodeAnalysis.Diagnostics.DiagnosticAnalyzer",
            "Microsoft.CodeAnalysis.IIncrementalGenerator",
            "Microsoft.CodeAnalysis.ISourceGenerator",
        };

        foreach (var handle in metadata.TypeDefinitions)
        {
            var definition = metadata.GetTypeDefinition(handle);
            Assert.DoesNotContain(
                ResolveTypeName(metadata, definition.BaseType) ?? string.Empty,
                forbidden);
            foreach (var implementationHandle in definition.GetInterfaceImplementations())
            {
                var implementation = metadata.GetInterfaceImplementation(
                    implementationHandle);
                Assert.DoesNotContain(
                    ResolveTypeName(
                        metadata,
                        implementation.Interface) ?? string.Empty,
                    forbidden);
            }
        }
    }

    [TestMethod]
    public void AuthoringManifestBindsTheExactStableSourceInventory()
    {
        var root = FindProgramKitRoot();
        using var document = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            root.FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "authoring-package-manifest.json")));
        var inventory = document.RootElement.GetProperty("sourceInventory");
        var paths = inventory.GetProperty("paths")
            .EnumerateArray()
            .Select(item => item.GetString()!)
            .ToArray();
        Assert.AreSequenceEqual(
            paths.Order(StringComparer.Ordinal),
            paths);
        Assert.HasCount(
            paths.Length,
            paths.Distinct(StringComparer.Ordinal));

        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var path in paths)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(path));
            hash.AppendData([0]);
            hash.AppendData(File.ReadAllBytes(Path.Combine(root.FullName, path)));
            hash.AppendData([0]);
        }

        var actual = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(hash.GetHashAndReset()));
        Assert.AreEqual(
            inventory.GetProperty("digest").GetString(),
            actual);
    }

    [TestMethod]
    public void AuthoringPackageDeclaresHelpersAndInertAssetsOnly()
    {
        var root = FindProgramKitRoot();
        var project = File.ReadAllText(Path.Combine(
            root.FullName,
            "src",
            "Orbyss.ProgramKit.CSharpBuildGates.Authoring",
            "Orbyss.ProgramKit.CSharpBuildGates.Authoring.csproj"));
        Assert.Contains("<DevelopmentDependency>true</DevelopmentDependency>", project);
        Assert.Contains("PackagePath=\"recipes/\"", project);
        Assert.Contains("PackagePath=\"templates/\"", project);
        Assert.DoesNotContain("PackagePath=\"analyzers/", project);
        Assert.DoesNotContain("PackagePath=\"build/", project);
        Assert.DoesNotContain("PackagePath=\"buildTransitive/", project);
    }

    [TestMethod]
    public async Task GeneratedConsumerOwnedAnalyzerCompilesOutsideProgramKit()
    {
        using var temporary = new AuthoringTemporaryDirectory();
        var output = Path.Combine(temporary.Path, "generated-analyzer");
        var service = new ConsumerAnalyzerScaffoldingService(
            new FileSystemConsumerAnalyzerScaffoldWorkspace());
        await service.ScaffoldAsync(
            CreateRequest(),
            output,
            TestContext.CancellationToken);

        using var process = Process.Start(new ProcessStartInfo
        {
            FileName = "dotnet",
            Arguments =
                "build Acme.Quality.Analyzers.csproj --nologo --verbosity quiet",
            WorkingDirectory = output,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        }) ?? throw new AssertFailedException("Could not start dotnet build.");
        var outputText = await process.StandardOutput.ReadToEndAsync(
            TestContext.CancellationToken);
        var errorText = await process.StandardError.ReadToEndAsync(
            TestContext.CancellationToken);
        await process.WaitForExitAsync(TestContext.CancellationToken);

        Assert.AreEqual(
            0,
            process.ExitCode,
            string.Concat(outputText, Environment.NewLine, errorText));
    }

    private static ConsumerAnalyzerScaffoldRequest CreateRequest()
    {
        return new ConsumerAnalyzerScaffoldRequest(
            "Acme.Quality.Analyzers",
            "Acme.Quality.Analyzers",
            new CSharpRuleRecipeBinding(
                CSharpRuleRecipeCatalog.ForbidTypeNameSuffix.Identity,
                CSharpRuleRecipeCatalog.ForbidTypeNameSuffix.Version,
                "pkid:owner:acme:quality",
                "pkid:rule:acme:forbid-service-suffix",
                "1.0.0",
                "ACME0001",
                "1.0.0",
                "Service suffix is forbidden",
                "Type name must not end with the consumer-selected suffix",
                ImmutableSortedDictionary<string, string>.Empty
                    .Add("forbiddenSuffix", "Service"),
                ["focused", "work-unit"],
                ["positive-type-name", "negative-service-name"],
                ["sdk:10.0.302", "roslyn:5.0.0", "language:14.0"],
                "source-local-ledger"),
            [
                new CSharpPublicAnalyzerSelectionProjection(
                    "pkid:analyzer:program-kit:generated-source-contract",
                    "pkid:domain:program-kit:generated-source-contract",
                    "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers",
                    "0.1.0-alpha.2",
                    new string('a', 64),
                    "analyzers/dotnet/cs/Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll",
                    new string('b', 64),
                    "pkid:contract:program-kit:generated-source-convention",
                    "1.0.0",
                    ["PKCC001"]),
            ]);
    }

    private static string Read(
        ConsumerAnalyzerScaffoldPlan plan,
        string relativePath)
    {
        var file = plan.Files.Single(candidate => string.Equals(
            candidate.RelativePath,
            relativePath,
            StringComparison.Ordinal));
        return Encoding.UTF8.GetString(file.Content.Span);
    }

    private static string? ResolveTypeName(
        MetadataReader metadata,
        EntityHandle handle)
    {
        if (handle.IsNil)
        {
            return null;
        }

        return handle.Kind switch
        {
            HandleKind.TypeDefinition => Name(
                metadata,
                metadata.GetTypeDefinition((TypeDefinitionHandle)handle)),
            HandleKind.TypeReference => Name(
                metadata,
                metadata.GetTypeReference((TypeReferenceHandle)handle)),
            _ => null,
        };
    }

    private static string Name(MetadataReader metadata, TypeDefinition definition)
    {
        return string.Concat(
            metadata.GetString(definition.Namespace),
            ".",
            metadata.GetString(definition.Name));
    }

    private static string Name(MetadataReader metadata, TypeReference reference)
    {
        return string.Concat(
            metadata.GetString(reference.Namespace),
            ".",
            metadata.GetString(reference.Name));
    }

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
            "Unable to locate the Program Kit repository root.");
    }
}
