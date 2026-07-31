using System.Security.Cryptography;
using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Schemas;

[TestClass]
public sealed class CurrentDesignFlowMigrationConformanceTests
{
    [TestMethod]
    public void CurrentDesignFlowMigrationsAreLossRejectingAndDigestBound()
    {
        var root = ConformanceInputs.RepositoryRoot;
        var migrationRoot = Path.Combine(
            root,
            ".review-sets",
            "consumer-cli-journey-completeness",
            "amendments",
            "consumer-contract-surface-hardening",
            "migrations");
        var rows = new[]
        {
            new
            {
                Definition = "architecture-design-alpha2-to-alpha3.migration.json",
                Implementation = Path.Combine(
                    root,
                    "src",
                    "Orbyss.ProgramKit.Architecture",
                    "Designs",
                    "ArchitectureDesignAlpha2ToAlpha3Migration.cs"),
                Fixture = "architecture-design-alpha2-to-alpha3.fixture.json",
            },
            new
            {
                Definition = "static-conformance-disposition-alpha1-to-alpha2.migration.json",
                Implementation = Path.Combine(
                    root,
                    "src",
                    "Orbyss.ProgramKit.Architecture",
                    "Designs",
                    "StaticConformanceDispositionAlpha1ToAlpha2Migration.cs"),
                Fixture = "static-conformance-disposition-alpha1-to-alpha2.fixture.json",
            },
            new
            {
                Definition = "implementation-plan-alpha3-to-alpha4.migration.json",
                Implementation = Path.Combine(
                    root,
                    "src",
                    "Orbyss.ProgramKit.Planning",
                    "Plans",
                    "ImplementationPlanAlpha3ToAlpha4Migration.cs"),
                Fixture = "implementation-plan-alpha3-to-alpha4.fixture.json",
            },
        };

        foreach (var row in rows)
        {
            using var definition = JsonDocument.Parse(
                File.ReadAllBytes(Path.Combine(migrationRoot, row.Definition)));
            var value = definition.RootElement;
            Assert.AreEqual("reject-loss", value.GetProperty("lossPolicy").GetString());
            Assert.IsTrue(value.GetProperty("isDeterministic").GetBoolean());
            Assert.IsTrue(value.GetProperty("isIdempotent").GetBoolean());
            Assert.AreEqual(
                Digest(row.Implementation),
                value.GetProperty("implementationReference")
                    .GetProperty("digest")
                    .GetString());
            Assert.AreEqual(
                Digest(Path.Combine(migrationRoot, "fixtures", row.Fixture)),
                value.GetProperty("fixtureReferences")[0]
                    .GetProperty("digest")
                    .GetString());
        }
    }

    private static string Digest(string path) =>
        string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path))));
}
