using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Migrations;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.DotNet.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Versioning;

[TestClass]
public sealed class HostToolingOperationConvergenceVersionTests
{
    [TestMethod]
    public void VersionMapAndMigrationBindExactV1V2AndOperationsRevisions()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        using var mapJson = JsonDocument.Parse(File.ReadAllBytes(
            Path.Combine(extensionRoot, "operation-convergence-version-map.json")));
        using var migrationJson = JsonDocument.Parse(File.ReadAllBytes(
            Path.Combine(
                extensionRoot,
                "migrations",
                "dotnet-operation-binding-v1-to-v2.migration.json")));
        var map = ReadVersionMap(mapJson.RootElement);
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        VersionMapDocumentValidator mapValidator =
            new(envelopeValidator);
        MigrationDefinitionValidator migrationValidator =
            new(envelopeValidator);

        var mapValidation = mapValidator.Validate(map);
        var migrationValidation = migrationValidator.Validate(migration);

        Assert.IsTrue(mapValidation.IsValid, Format(mapValidation));
        Assert.IsTrue(migrationValidation.IsValid, Format(migrationValidation));
        Assert.HasCount(5, map.Nodes);
        Assert.HasCount(3, map.Edges);
        Assert.AreEqual(
            MigrationLossPolicy.RejectLoss,
            migration.LossPolicy);
        Assert.IsTrue(migration.IsDeterministic);
        Assert.IsTrue(migration.IsIdempotent);

        var dotNetSchemas = new DotNetSchemaModule(
            new OperationsSchemaModule());
        var dotNetV1 = dotNetSchemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "1.0.0");
        var dotNetV2 = dotNetSchemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "2.0.0");
        Assert.AreEqual(
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell.schema.json")),
            dotNetV1.SchemaReference.Digest.Value);
        Assert.AreEqual(
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-2.0.0.schema.json")),
            dotNetV2.SchemaReference.Digest.Value);
        Assert.AreEqual(dotNetV2.SchemaReference, migration.Target);
        Assert.IsTrue(dotNetV2.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-operation-binding-v1-to-v2" &&
                reference.Digest.Value ==
                    string.Concat(
                        "sha256:",
                        HashRaw(Path.Combine(
                            extensionRoot,
                            "migrations",
                            "dotnet-operation-binding-v1-to-v2.migration.json")))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }

        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "migrations",
                    "dotnet-operation-binding-v1-to-v2.md"))));
    }

    private static VersionMapDocument ReadVersionMap(JsonElement root) =>
        new(
            root.GetProperty("nodes")
                .EnumerateArray()
                .Select(ReadNode)
                .ToImmutableArray(),
            root.GetProperty("edges")
                .EnumerateArray()
                .Select(ReadEdge)
                .ToImmutableArray());

    private static VersionRevisionNode ReadNode(JsonElement value) =>
        new(
            ReadReference(value.GetProperty("revision")),
            ReadBoundaryKind(value.GetProperty("kind").GetString()!),
            new ProgramKitIdentifier(value.GetProperty("ownerId").GetString()!),
            value.GetProperty("evidenceReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static VersionDependencyEdge ReadEdge(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("id").GetString()!),
            ReadReference(value.GetProperty("source")),
            new ProgramKitIdentifier(
                value.GetProperty("targetIdentity").GetString()!),
            ReadDependencyKind(value.GetProperty("kind").GetString()!),
            new SemanticVersionRange(
                value.GetProperty("acceptedRange").GetString()!),
            ReadReference(value.GetProperty("resolution")),
            value.GetProperty("exposure").GetString() == "public"
                ? DependencyExposure.Public
                : DependencyExposure.Private,
            value.GetProperty("compatibilityDimensions")
                .EnumerateArray()
                .Select(static item => item.GetString() switch
                {
                    "wire-read" => CompatibilityDimension.WireRead,
                    "wire-write" => CompatibilityDimension.WireWrite,
                    "source-api" => CompatibilityDimension.SourceApi,
                    _ => throw new InvalidDataException(
                        "Unexpected compatibility dimension."),
                })
                .ToImmutableArray(),
            value.GetProperty("evidenceReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static MigrationDefinition ReadMigration(JsonElement value) =>
        new(
            new ProgramKitIdentifier(
                value.GetProperty("sourceIdentity").GetString()!),
            new SemanticVersionRange(
                value.GetProperty("sourceRange").GetString()!),
            ReadReference(value.GetProperty("target")),
            MigrationMode.SourceGuidance,
            value.GetProperty("preconditions")
                .EnumerateArray()
                .Select(static precondition => new MigrationPrecondition(
                    precondition.GetProperty("code").GetString()!,
                    precondition.GetProperty("description").GetString()!,
                    precondition.GetProperty("evidenceReferences")
                        .EnumerateArray()
                        .Select(ReadReference)
                        .ToImmutableArray()))
                .ToImmutableArray(),
            MigrationLossPolicy.RejectLoss,
            value.GetProperty("isDeterministic").GetBoolean(),
            value.GetProperty("isIdempotent").GetBoolean(),
            MigrationFailurePolicy.PreserveSourceAndReport,
            ReadReference(value.GetProperty("implementationReference")),
            value.GetProperty("fixtureReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static ArtifactReference ReadReference(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("identity").GetString()!),
            new SemanticVersion(value.GetProperty("version").GetString()!),
            new Sha256Digest(value.GetProperty("digest").GetString()!));

    private static VersionBoundaryKind ReadBoundaryKind(string value) =>
        value switch
        {
            "schema" => VersionBoundaryKind.Schema,
            _ => throw new InvalidDataException("Unexpected boundary kind."),
        };

    private static VersionDependencyKind ReadDependencyKind(string value) =>
        value switch
        {
            "migrates" => VersionDependencyKind.Migrates,
            "uses-contract" => VersionDependencyKind.UsesContract,
            _ => throw new InvalidDataException("Unexpected dependency kind."),
        };

    private static string Hash(string path) =>
        string.Concat("sha256:", HashRaw(path));

    private static string HashRaw(string path) =>
        Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(path)))
            .ToLowerInvariant();

    private static string FindProgramKitRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current.FullName;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException(
            "The Program Kit repository root could not be found.");
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                string.Concat(
                    diagnostic.Id,
                    " ",
                    diagnostic.Path,
                    " ",
                    diagnostic.Message)));
}
