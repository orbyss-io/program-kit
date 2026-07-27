using System.Security.Cryptography;
using System.Text.Json;

namespace Orbyss.ProgramKit.UnitTests.Planning.Plans;

[TestClass]
public sealed class ImplementationPlanV3VersioningTests
{
    [TestMethod]
    public void VersionMapAndMigrationBindPlanningV2V3AndDispositionV1()
    {
        var extensionRoot = Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates");
        using var mapJson = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            extensionRoot,
            "planning-static-conformance-version-map.json")));
        using var migrationJson = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            extensionRoot,
            "migrations",
            "implementation-plan-v2-to-v3.migration.json")));
        var map = ReadVersionMap(mapJson.RootElement);
        var migration = ReadMigration(migrationJson.RootElement);
        VersionMapDocumentValidator mapValidator =
            new(new DefaultArtifactEnvelopeValidator());
        MigrationDefinitionValidator migrationValidator =
            new(new DefaultArtifactEnvelopeValidator());

        var mapResult = mapValidator.Validate(map);
        var migrationResult = migrationValidator.Validate(migration);

        Assert.IsTrue(mapResult.IsValid, Format(mapResult));
        Assert.IsTrue(migrationResult.IsValid, Format(migrationResult));
        Assert.AreEqual("3.0.0", migration.Target.Version.Value);
        Assert.AreEqual(MigrationLossPolicy.RejectLoss, migration.LossPolicy);
        Assert.IsTrue(migration.IsDeterministic);
        Assert.IsTrue(migration.IsIdempotent);
        Assert.IsTrue(map.Edges.Any(static edge =>
            edge.Kind == VersionDependencyKind.Migrates));
        Assert.IsTrue(map.Edges.Any(static edge =>
            edge.Kind == VersionDependencyKind.UsesContract &&
            edge.Resolution.Identity.Value ==
                "pkid:schema:program-kit:static-conformance-disposition"));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fileName = fixture.Version.Value == "2.0.0"
                ? "implementation-plan-v2-gate-establishment.json"
                : "implementation-plan-v3-gate-establishment.json";
            Assert.AreEqual(
                fixture.Digest.Value,
                Digest(Path.Combine(
                    extensionRoot,
                    "migrations",
                    "fixtures",
                    fileName)));
        }
    }

    private static VersionMapDocument ReadVersionMap(JsonElement value) =>
        new(
            value.GetProperty("nodes")
                .EnumerateArray()
                .Select(static node => new VersionRevisionNode(
                    ReadReference(node.GetProperty("revision")),
                    VersionBoundaryKind.Schema,
                    new ProgramKitIdentifier(
                        node.GetProperty("ownerId").GetString()!),
                    ReadReferences(node.GetProperty("evidenceReferences"))))
                .ToImmutableArray(),
            value.GetProperty("edges")
                .EnumerateArray()
                .Select(static edge => new VersionDependencyEdge(
                    new ProgramKitIdentifier(
                        edge.GetProperty("id").GetString()!),
                    ReadReference(edge.GetProperty("source")),
                    new ProgramKitIdentifier(
                        edge.GetProperty("targetIdentity").GetString()!),
                    edge.GetProperty("kind").GetString() == "migrates"
                        ? VersionDependencyKind.Migrates
                        : VersionDependencyKind.UsesContract,
                    new SemanticVersionRange(
                        edge.GetProperty("acceptedRange").GetString()!),
                    ReadReference(edge.GetProperty("resolution")),
                    DependencyExposure.Public,
                    edge.GetProperty("compatibilityDimensions")
                        .EnumerateArray()
                        .Select(static dimension =>
                            dimension.GetString() == "wire-read"
                                ? CompatibilityDimension.WireRead
                                : CompatibilityDimension.WireWrite)
                        .ToImmutableArray(),
                    ReadReferences(edge.GetProperty("evidenceReferences"))))
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
                    ReadReferences(
                        precondition.GetProperty("evidenceReferences"))))
                .ToImmutableArray(),
            MigrationLossPolicy.RejectLoss,
            value.GetProperty("isDeterministic").GetBoolean(),
            value.GetProperty("isIdempotent").GetBoolean(),
            MigrationFailurePolicy.PreserveSourceAndReport,
            ReadReference(value.GetProperty("implementationReference")),
            ReadReferences(value.GetProperty("fixtureReferences")));

    private static ImmutableArray<ArtifactReference> ReadReferences(
        JsonElement value) =>
        value.EnumerateArray()
            .Select(ReadReference)
            .ToImmutableArray();

    private static ArtifactReference ReadReference(JsonElement value) =>
        new(
            new ProgramKitIdentifier(
                value.GetProperty("identity").GetString()!),
            new SemanticVersion(
                value.GetProperty("version").GetString()!),
            new Sha256Digest(
                value.GetProperty("digest").GetString()!));

    private static DirectoryInfo FindProgramKitRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException("Program Kit root was not found.");
    }

    private static string Digest(string path) =>
        string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path))));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
