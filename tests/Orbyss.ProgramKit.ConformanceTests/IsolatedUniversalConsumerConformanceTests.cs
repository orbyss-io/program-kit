using System.Collections.Immutable;
using System.Reflection;
using System.Runtime.Versioning;
using System.Xml.Linq;
using Orbyss.ProgramKit.UniversalContractConsumerFixture;

namespace Orbyss.ProgramKit.ConformanceTests;

[TestClass]
public sealed class IsolatedUniversalConsumerConformanceTests
{
    private static readonly ImmutableHashSet<string> UniversalAssemblies =
    [
        "Orbyss.ProgramKit.Architecture",
        "Orbyss.ProgramKit.Artifacts",
        "Orbyss.ProgramKit.Development",
        "Orbyss.ProgramKit.Planning",
        "Orbyss.ProgramKit.Quality",
    ];

    [TestMethod]
    public void IsolatedNet10ConsumerCompilesAgainstExactlyTheUniversalContractClosure()
    {
        var consumerAssembly = typeof(UniversalContractConsumer).Assembly;
        var targetFramework = consumerAssembly
            .GetCustomAttribute<TargetFrameworkAttribute>()?
            .FrameworkName;

        Assert.AreEqual(".NETCoreApp,Version=v10.0", targetFramework);

        var directProgramKitReferences = consumerAssembly
            .GetReferencedAssemblies()
            .Select(reference => reference.Name)
            .Where(name => name is not null
                && name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
            .Cast<string>()
            .ToImmutableHashSet(StringComparer.Ordinal);

        Assert.IsTrue(
            UniversalAssemblies.SetEquals(directProgramKitReferences),
            $"Expected [{string.Join(", ", UniversalAssemblies)}], observed " +
            $"[{string.Join(", ", directProgramKitReferences)}].");

        var assembliesToInspect = UniversalAssemblies
            .Select(Assembly.Load)
            .Prepend(consumerAssembly);

        foreach (var assembly in assembliesToInspect)
        {
            foreach (var reference in assembly.GetReferencedAssemblies())
            {
                var name = reference.Name
                    ?? throw new AssertFailedException(
                        $"{assembly.GetName().Name} has an unnamed assembly reference.");

                Assert.IsFalse(
                    name.StartsWith("Orbyss.", StringComparison.Ordinal)
                    && !UniversalAssemblies.Contains(name),
                    $"{assembly.GetName().Name} references excluded first-party assembly {name}.");
                Assert.IsFalse(
                    name.StartsWith("CShells", StringComparison.Ordinal)
                    || name.StartsWith("Microsoft.Extensions.Hosting", StringComparison.Ordinal)
                    || name.StartsWith("Newtonsoft", StringComparison.Ordinal)
                    || name.StartsWith("Cronos", StringComparison.Ordinal),
                    $"{assembly.GetName().Name} references excluded dependency {name}.");
            }
        }
    }

    [TestMethod]
    public void IsolatedConsumerProjectDeclaresOnlyTheFiveUniversalProjects()
    {
        var project = XDocument.Parse(
            ConformanceInputs.Read(
                "UniversalContractConsumer/UniversalContractConsumer.csproj"));
        var projectReferences = project
            .Descendants("ProjectReference")
            .Select(reference => reference.Attribute("Include")?.Value
                ?? throw new AssertFailedException("ProjectReference is missing Include."))
            .Select(reference => Path.GetFileNameWithoutExtension(reference)
                ?? throw new AssertFailedException(
                    $"Could not derive a project name from {reference}."))
            .ToImmutableHashSet(StringComparer.Ordinal);

        Assert.IsTrue(
            UniversalAssemblies.SetEquals(projectReferences),
            $"Expected [{string.Join(", ", UniversalAssemblies)}], observed " +
            $"[{string.Join(", ", projectReferences)}].");
        Assert.IsFalse(project.Descendants("PackageReference").Any());
        Assert.IsFalse(project.Descendants("FrameworkReference").Any());
        Assert.IsFalse(project.Descendants("TargetFramework").Any());
        Assert.IsFalse(project.Descendants("TargetFrameworks").Any());

        var projectAndSource = project
            + ConformanceInputs.Read(
                "UniversalContractConsumer/UniversalContractConsumer.cs");
        var forbiddenTokens = new[]
        {
            "CShells",
            "DomainSemanticEngine",
            "Microsoft.Extensions.Hosting",
            "Orbyss.ProgramKit.Cli",
            "Orbyss.ProgramKit.Hosting",
            "Orbyss.ProgramKit.Tasks",
            "Orbyss.ProgramKit.Workbench",
            "ReleaseCycle",
        };

        foreach (var token in forbiddenTokens)
        {
            Assert.IsFalse(
                projectAndSource.Contains(token, StringComparison.Ordinal),
                $"The isolated consumer contains excluded token {token}.");
        }
    }
}
