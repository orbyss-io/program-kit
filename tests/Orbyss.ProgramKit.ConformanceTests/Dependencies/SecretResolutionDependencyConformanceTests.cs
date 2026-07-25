using Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class SecretResolutionDependencyConformanceTests
{
    private static readonly string[] ExpectedRuntimeReferences =
    [
        "Orbyss.ProgramKit.Artifacts",
        "Orbyss.ProgramKit.SecretResolution",
    ];

    [TestMethod]
    public void IsolatedGeneratedConsumerUsesOnlyRuntimeContractPackages()
    {
        var references = typeof(FixtureSecretSubscription).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name =>
                name.StartsWith("Orbyss.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(ExpectedRuntimeReferences, references);
    }

    [TestMethod]
    public void ContractPackagePreservesOneVersionedSchemaPath()
    {
        var project = File.ReadAllText(
            ConformanceInputs
                .Files(
                    "Projects",
                    "Orbyss.ProgramKit.SecretResolution.csproj")
                .Single());

        Assert.Contains(
            "PackagePath=\"schemas/secret-resolution/\"",
            project);
        Assert.DoesNotContain(
            "PackagePath=\"schemas/secret-resolution/%(RecursiveDir)\"",
            project);
        Assert.Contains(
            "LogicalName=\"Orbyss.ProgramKit.SecretResolution.Schemas.v1_0_0.%(Filename)%(Extension)\"",
            project);
    }
}
