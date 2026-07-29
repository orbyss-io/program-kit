using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetConsoleIntegrationAssemblyInspectorTests
{
    [TestMethod]
    public void AcceptsUniqueImplementationsAndExactScopedRegistrations()
    {
        var shell = DotNetTestContractFactory.Shell();
        var document = DotNetTestContractFactory.JTestConsoleDocument(shell);
        var binding = DotNetConsoleBindingTestFactory
            .JTestGenerationInput(
                document,
                DotNetTestContractFactory.Ref(
                    "document",
                    "jtest-console",
                    '1'))
            .Binding;
        DotNetConsoleIntegrationAssemblyInspector sut = new();

        var result = sut.Inspect(
            binding,
            typeof(JTestRunRequest).Assembly.Location);

        Assert.IsTrue(result.IsValid);
    }

    [TestMethod]
    public void RejectsAFeatureWithoutExactHandlerRegistrations()
    {
        var shell = DotNetTestContractFactory.Shell();
        var document = DotNetTestContractFactory.JTestConsoleDocument(shell);
        var binding = DotNetConsoleBindingTestFactory
            .JTestGenerationInput(
                document,
                DotNetTestContractFactory.Ref(
                    "document",
                    "jtest-console",
                    '1'))
            .Binding with
        {
            FeatureType = DotNetConsoleBindingTestFactory.Type(
                    typeof(WrongLifetimeMetadataFixtureFeature).FullName ??
                    throw new InvalidOperationException()),
        };
        DotNetConsoleIntegrationAssemblyInspector sut = new();

        var result = sut.Inspect(
            binding,
            typeof(JTestRunRequest).Assembly.Location);

        Assert.IsFalse(result.IsValid);
        Assert.IsNotEmpty(
            result.Diagnostics.Where(static diagnostic =>
                diagnostic.Message.Contains(
                "exactly one direct unkeyed scoped",
                StringComparison.Ordinal)));
    }
}
