using GeneratedHost.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class TransportFailureDependencyConformanceTests
{
    [TestMethod]
    public void IsolatedGeneratedTransportFailureConsumerUsesNoProgramKitRuntime()
    {
        var references = typeof(TransportFailureHarness).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name =>
                name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(references);
    }
}
