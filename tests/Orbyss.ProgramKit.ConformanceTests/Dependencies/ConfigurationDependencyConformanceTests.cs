using Orbyss.ProgramKit.ConfigurationConsumerFixture.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class ConfigurationDependencyConformanceTests
{
    [TestMethod]
    public void IsolatedGeneratedConfigurationConsumerUsesNoProgramKitRuntime()
    {
        Assert.IsTrue(ConfigurationConsumer.Validate());
        var references = typeof(ConfigurationConsumer).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name =>
                name.StartsWith("Orbyss.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(references);
    }
}
