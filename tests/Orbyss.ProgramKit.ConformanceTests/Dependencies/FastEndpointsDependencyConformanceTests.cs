using System.Text.Json;
using System.Xml.Linq;
using GeneratedHost.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class FastEndpointsDependencyConformanceTests
{
    private static readonly string[] FixturePackages =
    [
        "CShells.FastEndpoints",
        "FastEndpoints",
        "Microsoft.AspNetCore.TestHost",
    ];

    [TestMethod]
    public void IsolatedGeneratedFastEndpointsConsumerUsesNoProgramKitRuntime()
    {
        var references = typeof(FastEndpointsHarness).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Where(static name =>
                name.StartsWith(
                    "Orbyss.ProgramKit.",
                    StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(references);
    }

    [TestMethod]
    public void FixtureDeclaresExactAdapterAndTestTransportPackagesOnly()
    {
        var fixtureRoot = FixtureRoot();
        var project = XDocument.Load(Path.Combine(
            fixtureRoot,
            "FastEndpointsConsumer.csproj"));
        var projectReferences = project
            .Descendants("ProjectReference")
            .ToArray();
        var packages = project
            .Descendants("PackageReference")
            .Select(static item => item.Attribute("Include")!.Value)
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.IsEmpty(projectReferences);
        Assert.AreSequenceEqual(
            FixturePackages,
            packages);
    }

    [TestMethod]
    public void LockedAdapterDependencyGraphIsCompleteAndRevisionCoherent()
    {
        using var document = JsonDocument.Parse(File.ReadAllBytes(
            Path.Combine(FixtureRoot(), "packages.lock.json")));
        var dependencies = document.RootElement
            .GetProperty("dependencies")
            .GetProperty("net10.0");
        var entries = dependencies
            .EnumerateObject()
            .ToDictionary(
                static item => item.Name,
                static item => item.Value,
                StringComparer.Ordinal);

        Assert.AreEqual(
            "0.0.28",
            entries["CShells.FastEndpoints"]
                .GetProperty("resolved")
                .GetString());
        Assert.AreEqual(
            "7.2.0",
            entries["FastEndpoints"]
                .GetProperty("resolved")
                .GetString());
        Assert.AreEqual(
            "10.0.10",
            entries["Microsoft.AspNetCore.TestHost"]
                .GetProperty("resolved")
                .GetString());
        foreach (var entry in entries)
        {
            if (entry.Value.TryGetProperty(
                    "dependencies",
                    out var transitive))
            {
                foreach (var required in transitive.EnumerateObject())
                {
                    Assert.IsTrue(
                        entries.ContainsKey(required.Name),
                        string.Concat(
                            entry.Key,
                            " -> ",
                            required.Name));
                }
            }

            var resolved = entry.Value
                .GetProperty("resolved")
                .GetString();
            if (entry.Key.StartsWith(
                    "CShells",
                    StringComparison.Ordinal))
            {
                Assert.AreEqual("0.0.28", resolved, entry.Key);
            }

            if (entry.Key.StartsWith(
                    "FastEndpoints",
                    StringComparison.Ordinal))
            {
                Assert.AreEqual("7.2.0", resolved, entry.Key);
            }
        }
    }

    private static string FixtureRoot() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "FastEndpointsConsumer");
}
