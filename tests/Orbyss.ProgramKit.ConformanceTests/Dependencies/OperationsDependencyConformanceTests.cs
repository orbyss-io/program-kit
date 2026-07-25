using Orbyss.ProgramKit.OperationsConsumerFixture.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class OperationsDependencyConformanceTests
{
    [TestMethod]
    public void OperationsDependsOnlyOnArtifactsAndPlatformAssemblies()
    {
        var references = typeof(OperationContractCatalog).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name => name.StartsWith("Orbyss.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(["Orbyss.ProgramKit.Artifacts"], references);
    }

    [TestMethod]
    public void IsolatedOperationsConsumerUsesOnlyOperationsAndArtifacts()
    {
        Assert.IsTrue(OperationsConsumer.Validate());
        var references = typeof(OperationsConsumer).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name => name.StartsWith("Orbyss.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(
            [
                "Orbyss.ProgramKit.Artifacts",
                "Orbyss.ProgramKit.Operations",
            ],
            references);
    }

    [TestMethod]
    public void OperationsSurfaceContainsNoForbiddenRuntimeOwnership()
    {
        var assembly = typeof(OperationContractCatalog).Assembly;
        var forbidden = new[]
        {
            "AspNetCore",
            "Authorization",
            "CommandLine",
            "DomainSemanticEngine",
            "Hosting",
            "Identity",
            "Provider",
            "Tasks",
            "Transport",
        };
        var surface = assembly.GetExportedTypes()
            .Select(static type => type.FullName!)
            .ToArray();

        foreach (var token in forbidden)
        {
            Assert.DoesNotContain(
                value => value.Contains(token, StringComparison.Ordinal),
                surface,
                token);
        }
    }
}
