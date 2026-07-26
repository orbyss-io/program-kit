using GeneratedHost.Composition;
using GeneratedPublicBrowser.Operations;
using System.Xml.Linq;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class SecurityDependencyConformanceTests
{
    private static readonly string[] PublicBrowserPackages =
    [
        "Microsoft.AspNetCore.Components.WebAssembly",
        "Microsoft.AspNetCore.Components.WebAssembly.Authentication",
    ];

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

    [TestMethod]
    public void PublicBrowserVerifierUsesNoProgramKitRuntime()
    {
        var references = typeof(PublicBrowserProtocolProbe).Assembly
            .GetReferencedAssemblies()
            .Select(static assembly => assembly.Name!)
            .Where(static name =>
                name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(references);
    }

    [TestMethod]
    public void PublicBrowserConsumerDeclaresOnlyTheClosedFrameworkAdapter()
    {
        var projectPath = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "PublicBrowserConsumer",
            "PublicBrowserConsumer.csproj");
        var project = XDocument.Load(projectPath);
        var projectReferences = project.Descendants("ProjectReference").ToArray();
        var packages = project.Descendants("PackageReference")
            .Select(static item => item.Attribute("Include")!.Value)
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(projectReferences);
        Assert.AreSequenceEqual(
            PublicBrowserPackages,
            packages);
    }
}
