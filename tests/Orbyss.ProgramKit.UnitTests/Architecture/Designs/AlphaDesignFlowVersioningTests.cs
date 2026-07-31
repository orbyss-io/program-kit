using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Migrations;
using Orbyss.ProgramKit.Artifacts.Versioning;

namespace Orbyss.ProgramKit.UnitTests.Architecture.Designs;

[TestClass]
public sealed class AlphaDesignFlowVersioningTests
{
    [TestMethod]
    public void ExactMapAndMigrationsCloseTheAlphaDesignFlow()
    {
        var root = FindProgramKitRoot();
        var transitionRoot = Path.Combine(
            root.FullName,
            ".review-sets",
            "alpha-version-transition");
        using var mapJson = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            transitionRoot,
            "design-flow-version-map.json")));
        var map = ReadVersionMap(mapJson.RootElement);
        var migrations = new[]
        {
            ReadMigration(
                transitionRoot,
                "architecture-design-v2-to-alpha2.migration.json"),
            ReadMigration(
                transitionRoot,
                "static-conformance-disposition-v1-to-alpha1.migration.json"),
            ReadMigration(
                transitionRoot,
                "implementation-plan-v3-to-alpha3.migration.json"),
        };
        VersionMapDocumentValidator mapValidator =
            new(new DefaultArtifactEnvelopeValidator());
        MigrationDefinitionValidator migrationValidator =
            new(new DefaultArtifactEnvelopeValidator());

        var mapResult = mapValidator.Validate(map);

        Assert.IsTrue(mapResult.IsValid, Format(mapResult));
        Assert.HasCount(6, map.Nodes);
        Assert.HasCount(7, map.Edges);
        Assert.AreSequenceEqual(
            ["0.1.0-alpha.1", "0.1.0-alpha.2", "0.1.0-alpha.3"],
            migrations
                .Select(static migration => migration.Target.Version.Value)
                .OrderBy(static version => version, StringComparer.Ordinal));
        foreach (var migration in migrations)
        {
            var migrationResult = migrationValidator.Validate(migration);
            Assert.IsTrue(migrationResult.IsValid, Format(migrationResult));
            Assert.AreEqual(
                MigrationLossPolicy.RejectLoss,
                migration.LossPolicy);
            Assert.IsTrue(migration.IsDeterministic);
            Assert.IsTrue(migration.IsIdempotent);
        }

        Assert.AreEqual(
            "sha256:2698ce65a29cb0d5007b2ab1773d7e387385df7c8b72495804b292b6af696198",
            Digest(Path.Combine(
                root.FullName,
                "schemas",
                "architecture",
                "architecture-design-2.0.0.schema.json")));
        Assert.AreEqual(
            "sha256:834902de4706a7c6859390bd7ee5e4fd6a3e7e455486348c02a1cb84604d15bd",
            Digest(Path.Combine(
                root.FullName,
                "schemas",
                "architecture",
                "static-conformance-disposition.schema.json")));
        Assert.AreEqual(
            "sha256:0f3b8f524b29ec7b5871ce411f06852e1b06326a5e1da616184627df0b5ea1b6",
            Digest(Path.Combine(
                root.FullName,
                "schemas",
                "planning",
                "implementation-plan-3.0.0.schema.json")));

        Assert.AreEqual(
            migrations[0].ImplementationReference.Digest.Value,
            Digest(Path.Combine(
                root.FullName,
                "src",
                "Orbyss.ProgramKit.Architecture",
                "Designs",
                "ArchitectureDesignV2ToAlpha2Migration.cs")));
        Assert.AreEqual(
            migrations[1].ImplementationReference.Digest.Value,
            Digest(Path.Combine(
                root.FullName,
                "src",
                "Orbyss.ProgramKit.Architecture",
                "Designs",
                "StaticConformanceDispositionV1ToAlpha1Migration.cs")));
        Assert.AreEqual(
            migrations[2].ImplementationReference.Digest.Value,
            Digest(Path.Combine(
                root.FullName,
                "src",
                "Orbyss.ProgramKit.Planning",
                "Plans",
                "ImplementationPlanV3ToAlpha3Migration.cs")));

        var fixtureNames = new[]
        {
            "architecture-design-v2-to-alpha2.fixture.json",
            "static-conformance-disposition-v1-to-alpha1.fixture.json",
            "implementation-plan-v3-to-alpha3.fixture.json",
        };
        for (var index = 0; index < migrations.Length; index++)
        {
            Assert.AreEqual(
                migrations[index].FixtureReferences.Single().Digest.Value,
                Digest(Path.Combine(
                    transitionRoot,
                    "migrations",
                    "fixtures",
                    fixtureNames[index])));
        }

        var approvalDigest = Digest(Path.Combine(
            transitionRoot,
            "design-plan-approval.json"));
        Assert.IsTrue(migrations.All(migration =>
            migration.Preconditions.Single()
                .EvidenceReferences.Single().Digest.Value == approvalDigest));
    }

    private static MigrationDefinition ReadMigration(
        string transitionRoot,
        string fileName)
    {
        using var json = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            transitionRoot,
            "migrations",
            fileName)));
        return ReadMigration(json.RootElement);
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
