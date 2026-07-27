using System.Xml.Linq;

namespace Orbyss.ProgramKit.ConformanceTests.Modularity.Dependencies;

[TestClass]
public sealed class ModularityDependencyConformanceTests
{
    [TestMethod]
    public void ModularityProjectsHaveTheExactApprovedReferenceGraph()
    {
        AssertProjectReferences(
            "Orbyss.ProgramKit.Modularity",
            ["Orbyss.ProgramKit.Artifacts"]);
        AssertProjectReferences(
            "Orbyss.ProgramKit.Modularity.InProcess",
            ["Orbyss.ProgramKit.Modularity"]);
    }

    [TestMethod]
    public void ModularitySourceHasNoDeferredRuntimeOrHostDependencies()
    {
        var files = ConformanceInputs
            .Files("Source", "*.cs")
            .Where(path =>
                path.Contains(
                    "Orbyss.ProgramKit.Modularity",
                    StringComparison.Ordinal))
            .ToArray();
        string[] forbidden =
        [
            "using CShells",
            "using Microsoft.Extensions",
            "using Orbyss.ProgramKit.Tasks",
            "using System.Net",
            "using System.Threading.Channels",
            "using System.Transactions",
            "JsonElement",
            "JsonNode",
            "JsonDocument",
            "JsonSerializer",
        ];

        Assert.IsNotEmpty(files);
        foreach (var file in files)
        {
            var source = File.ReadAllText(file);
            foreach (var token in forbidden)
            {
                Assert.DoesNotContain(
                    token,
                    source,
                    StringComparison.Ordinal,
                    $"Forbidden dependency token '{token}' found in {file}.");
            }
        }
    }

    private static void AssertProjectReferences(
        string projectName,
        string[] expectedReferences)
    {
        var projectPath = ConformanceInputs
            .Files("Projects", string.Concat(projectName, ".csproj"))
            .Single(path =>
                string.Equals(
                    Path.GetFileNameWithoutExtension(path),
                    projectName,
                    StringComparison.Ordinal));
        var document = XDocument.Load(projectPath);
        var references = document
            .Descendants("ProjectReference")
            .Select(element =>
                Path.GetFileNameWithoutExtension(
                    element.Attribute("Include")?.Value))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(
            expectedReferences.Order(StringComparer.Ordinal).ToArray(),
            references);
        Assert.IsEmpty(document.Descendants("PackageReference"));
        Assert.IsEmpty(document.Descendants("FrameworkReference"));
    }
}
