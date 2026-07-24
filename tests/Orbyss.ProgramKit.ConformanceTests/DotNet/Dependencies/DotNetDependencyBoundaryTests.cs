using System.Reflection;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Dependencies;

[TestClass]
public sealed class DotNetDependencyBoundaryTests
{
    [TestMethod]
    public void DotNetKitHasNoCshellsRoslynCommandParserOrNewtonsoftRuntimeReference()
    {
        var references = typeof(DotNetShellDocument).Assembly
            .GetReferencedAssemblies()
            .Select(static assembly => assembly.Name!)
            .ToArray();

        Assert.DoesNotContain(
            static name => name.StartsWith("CShells", StringComparison.Ordinal),
            references);
        Assert.DoesNotContain(
            static name => name.StartsWith("Microsoft.CodeAnalysis", StringComparison.Ordinal),
            references);
        Assert.DoesNotContain(
            static name => name.Contains("CommandLine", StringComparison.Ordinal),
            references);
        Assert.DoesNotContain(
            static name => name.StartsWith("Newtonsoft", StringComparison.Ordinal),
            references);
    }

    [TestMethod]
    public void CoreUniversalAndTaskContractsRemainCshellsFree()
    {
        Assembly[] assemblies =
        [
            typeof(ArtifactReference).Assembly,
            typeof(Orbyss.ProgramKit.Modularity.Ordering.IModularityRegistration).Assembly,
            typeof(TaskDefinition).Assembly,
            typeof(Orbyss.ProgramKit.Serialization.Json.Profiles.JsonSerializationProfile).Assembly,
            typeof(Orbyss.ProgramKit.Tasks.Schedules.Descriptors.FixedDelayScheduleDescriptor).Assembly,
        ];

        foreach (var assembly in assemblies)
        {
            Assert.DoesNotContain(
                static reference =>
                    reference.Name!.StartsWith("CShells", StringComparison.Ordinal),
                assembly.GetReferencedAssemblies(),
                assembly.GetName().Name);
        }
    }
}
