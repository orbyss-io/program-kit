using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
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
}
