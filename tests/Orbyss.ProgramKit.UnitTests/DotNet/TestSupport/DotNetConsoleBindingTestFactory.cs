using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

namespace Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

internal static class DotNetConsoleBindingTestFactory
{
    internal static DotNetConsoleBindingDocument Binding(
        OpenConsoleDocument openConsole)
    {
        var command = openConsole.Commands.Single();
        return new DotNetConsoleBindingDocument(
            "pkid:schema:program-kit:dotnet-console-binding@1.0.0",
            new SemanticVersion("1.0.0"),
            DotNetTestContractFactory.Ref("document", "open-console", '1'),
            new DotNetConsoleConsumerProject(
                DotNetTestContractFactory.Id("project", "sample-console"),
                "Sample.Console.Contracts",
                "src/Sample.Console.Contracts/Sample.Console.Contracts.csproj",
                "net10.0",
                "Sample.Console.Contracts",
                "artifacts/Sample.Console.Contracts/ref/net10.0/Sample.Console.Contracts.dll",
                DotNetTestContractFactory.Digest('2')),
            Type("Sample.Console.SampleConsoleFeature"),
            Type("Sample.Console.CommandValidationResult"),
            [
                new DotNetConsoleOperationBinding(
                    command.OperationRevision,
                    "ObserveRun",
                    Type("Sample.Console.ObserveRunRequest"),
                    Type("Sample.Console.IObserveRunHandler"),
                    Type("Sample.Console.IObserveRunValidator"),
                    [
                        Parameter(
                            0,
                            "target",
                            Type("System.String"),
                            DotNetConsoleBindingSourceKind.Argument,
                            "target",
                            DotNetConsoleDefaultKind.None,
                            null),
                        Parameter(
                            1,
                            "count",
                            Type(
                                "System.Int32",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "count",
                            DotNetConsoleDefaultKind.Canonical,
                            "1"),
                        Parameter(
                            2,
                            "force",
                            Type(
                                "System.Boolean",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "force",
                            DotNetConsoleDefaultKind.None,
                            null),
                        Parameter(
                            3,
                            "confirm",
                            Type(
                                "System.Boolean",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "confirm",
                            DotNetConsoleDefaultKind.None,
                            null),
                        Parameter(
                            4,
                            "total",
                            Type(
                                "System.Int64",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "total",
                            DotNetConsoleDefaultKind.Canonical,
                            "8"),
                        Parameter(
                            5,
                            "ratio",
                            Type(
                                "System.Decimal",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "ratio",
                            DotNetConsoleDefaultKind.Canonical,
                            "1.5"),
                        Parameter(
                            6,
                            "correlation",
                            Type(
                                "System.Guid",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "correlation",
                            DotNetConsoleDefaultKind.Canonical,
                            "d2719a8c-3ae5-49b1-a6ab-f57ad42f51ee"),
                        Parameter(
                            7,
                            "at",
                            Type(
                                "System.DateTimeOffset",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "at",
                            DotNetConsoleDefaultKind.Canonical,
                            "2026-01-01T00:00:00.0000000+00:00"),
                        Parameter(
                            8,
                            "tags",
                            new DotNetConsoleClrTypeDescriptor(
                                "System.Collections.Immutable.ImmutableArray`1",
                                [Type("System.String")],
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "tag",
                            DotNetConsoleDefaultKind.None,
                            null),
                    ]),
            ]);
    }

    internal static DotNetConsoleBindingDocument MetadataBinding(
        OpenConsoleDocument openConsole,
        string assemblyPath)
    {
        var binding = Binding(openConsole);
        var operation = binding.Operations[0];
        var digest = new Sha256Digest(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(
                    System.Security.Cryptography.SHA256.HashData(
                        File.ReadAllBytes(assemblyPath)))));
        return binding with
        {
            ConsumerProject = binding.ConsumerProject with
            {
                ReferenceAssemblyName =
                    typeof(MetadataFixtureRequest).Assembly.GetName().Name ??
                    throw new InvalidOperationException(
                        "The metadata fixture assembly has no name."),
                RelativeReferenceAssemblyPath =
                    "artifacts/Orbyss.ProgramKit.UnitTests.dll",
                ReferenceAssemblyDigest = digest,
            },
            FeatureType = Type(
                typeof(MetadataFixtureFeature).FullName ??
                throw new InvalidOperationException()),
            ValidationResultType = Type(
                typeof(MetadataFixtureValidationResult).FullName ??
                throw new InvalidOperationException()),
            Operations =
            [
                operation with
                {
                    RequestType = Type(
                        typeof(MetadataFixtureRequest).FullName ??
                        throw new InvalidOperationException()),
                    HandlerType = Type(
                        typeof(IMetadataFixtureHandler).FullName ??
                        throw new InvalidOperationException()),
                    ValidatorType = Type(
                        typeof(IMetadataFixtureValidator).FullName ??
                        throw new InvalidOperationException()),
                },
            ],
        };
    }

    internal static DotNetConsoleGenerationInput GenerationInput(
        OpenConsoleDocument openConsole,
        ArtifactReference documentRevision,
        System.Type? featureType = null)
    {
        var assemblyPath = typeof(MetadataFixtureRequest).Assembly.Location;
        var binding = MetadataBinding(openConsole, assemblyPath) with
        {
            OpenConsoleDocumentRevision = documentRevision,
            FeatureType = Type(
                (featureType ?? typeof(MetadataFixtureFeature)).FullName ??
                throw new InvalidOperationException(
                    "The fixture feature has no metadata name.")),
        };
        return GenerationInput(binding, assemblyPath);
    }

    internal static DotNetConsoleGenerationInput JTestGenerationInput(
        OpenConsoleDocument openConsole,
        ArtifactReference documentRevision)
    {
        var assemblyPath = typeof(JTestRunRequest).Assembly.Location;
        var digest = Digest(assemblyPath);
        var binding = new DotNetConsoleBindingDocument(
            "pkid:schema:program-kit:dotnet-console-binding@1.0.0",
            new SemanticVersion("1.0.0"),
            documentRevision,
            new DotNetConsoleConsumerProject(
                DotNetTestContractFactory.Id("project", "jtest-contracts"),
                "JTest.Contracts",
                "src/JTest.Contracts/JTest.Contracts.csproj",
                "net10.0",
                typeof(JTestRunRequest).Assembly.GetName().Name ??
                    throw new InvalidOperationException(),
                "artifacts/JTest.Contracts/ref/net10.0/JTest.Contracts.dll",
                digest),
            Type(
                typeof(JTestFixtureFeature).FullName ??
                    throw new InvalidOperationException()),
            Type(
                typeof(MetadataFixtureValidationResult).FullName ??
                    throw new InvalidOperationException()),
            [
                Operation(
                    openConsole,
                    "run",
                    "Run",
                    typeof(JTestRunRequest),
                    typeof(IJTestRunHandler),
                    typeof(IJTestRunValidator),
                    [
                        Parameter(
                            0,
                            "suite",
                            Type("System.String"),
                            DotNetConsoleBindingSourceKind.Argument,
                            "suite",
                            DotNetConsoleDefaultKind.None,
                            null),
                        Parameter(
                            1,
                            "maximumParallelism",
                            Type(
                                "System.Int32",
                                DotNetConsoleReferenceNullability.NotApplicable),
                            DotNetConsoleBindingSourceKind.Option,
                            "maximum-parallelism",
                            DotNetConsoleDefaultKind.Canonical,
                            "1"),
                    ]),
                Operation(
                    openConsole,
                    "validate",
                    "Validate",
                    typeof(JTestValidateRequest),
                    typeof(IJTestValidateHandler),
                    null,
                    [
                        Parameter(
                            0,
                            "path",
                            Type("System.String"),
                            DotNetConsoleBindingSourceKind.Argument,
                            "path",
                            DotNetConsoleDefaultKind.None,
                            null),
                    ]),
                Operation(
                    openConsole,
                    "describe",
                    "Describe",
                    typeof(JTestDescribeRequest),
                    typeof(IJTestDescribeHandler),
                    null,
                    [
                        Parameter(
                            0,
                            "suite",
                            Type("System.String"),
                            DotNetConsoleBindingSourceKind.Argument,
                            "suite",
                            DotNetConsoleDefaultKind.None,
                            null),
                    ]),
            ]);
        return GenerationInput(binding, assemblyPath);
    }

    private static DotNetConsoleOperationBinding Operation(
        OpenConsoleDocument document,
        string commandName,
        string generatedSymbol,
        Type requestType,
        Type handlerType,
        Type? validatorType,
        ImmutableArray<DotNetConsoleConstructorParameter> parameters)
    {
        var command = document.Commands.Single(item =>
            item.Path.SequenceEqual([commandName]));
        return new DotNetConsoleOperationBinding(
            command.OperationRevision,
            generatedSymbol,
            Type(
                requestType.FullName ??
                    throw new InvalidOperationException()),
            Type(
                handlerType.FullName ??
                    throw new InvalidOperationException()),
            validatorType is null
                ? null
                : Type(
                    validatorType.FullName ??
                        throw new InvalidOperationException()),
            parameters);
    }

    private static DotNetConsoleGenerationInput GenerationInput(
        DotNetConsoleBindingDocument binding,
        string assemblyPath)
    {
        var trustedPlatformAssemblies = (
            AppContext.GetData("TRUSTED_PLATFORM_ASSEMBLIES") as string ??
            string.Empty)
            .Split(
                Path.PathSeparator,
                StringSplitOptions.RemoveEmptyEntries);
        var outputAssemblies = Directory.GetFiles(
            AppContext.BaseDirectory,
            "*.dll",
            SearchOption.TopDirectoryOnly);
        var references = trustedPlatformAssemblies
            .Concat(outputAssemblies)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Order(StringComparer.Ordinal)
            .Select(static path => new DotNetConsoleCompilationReference(
                path,
                Digest(path)))
            .ToImmutableArray();
        return new DotNetConsoleGenerationInput(
            binding,
            assemblyPath,
            references);
    }

    internal static DotNetConsoleClrTypeDescriptor Type(
        string metadataName,
        DotNetConsoleReferenceNullability nullability =
            DotNetConsoleReferenceNullability.NotNull) =>
        new(metadataName, [], nullability);

    private static DotNetConsoleConstructorParameter Parameter(
        int position,
        string parameterName,
        DotNetConsoleClrTypeDescriptor clrType,
        DotNetConsoleBindingSourceKind sourceKind,
        string sourceName,
        DotNetConsoleDefaultKind defaultKind,
        string? canonicalDefault) =>
        new(
            position,
            parameterName,
            clrType,
            new DotNetConsoleParameterSource(sourceKind, sourceName),
            new DotNetConsoleDefaultDisposition(
                defaultKind,
                canonicalDefault));

    private static Sha256Digest Digest(string path) =>
        new(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(
                    System.Security.Cryptography.SHA256.HashData(
                        File.ReadAllBytes(path)))));
}
