using GeneratedHost.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class SecurityDependencyConformanceTests
{
    [TestMethod]
    public void IsolatedGeneratedSecurityConsumerUsesNoProgramKitRuntime()
    {
        var references = typeof(SecurityHarness).Assembly
            .GetReferencedAssemblies()
            .Select(static assembly => assembly.Name!)
            .Where(static name =>
                name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(references);
    }
}
