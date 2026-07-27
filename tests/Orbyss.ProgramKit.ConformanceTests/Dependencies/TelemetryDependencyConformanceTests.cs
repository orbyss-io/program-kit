using Orbyss.ProgramKit.TelemetryConsumerFixture.Hosting;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class TelemetryDependencyConformanceTests
{
    [TestMethod]
    public void IsolatedGeneratedTelemetryConsumerUsesNoProgramKitRuntime()
    {
        var references = typeof(TelemetryComposition).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name =>
                name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(references);
    }
}
