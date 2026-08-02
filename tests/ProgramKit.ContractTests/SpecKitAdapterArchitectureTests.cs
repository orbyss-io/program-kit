using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using System.Xml.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterArchitectureTests
{
    [TestMethod]
    public void Adapter_has_exactly_one_production_project_reference_to_public_contracts()
    {
        string projectPath = Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "ProgramKit.SpecKitAdapter.csproj");
        XDocument project = XDocument.Load(projectPath);
        string[] references = project.Descendants("ProjectReference").Select(static element => element.Attribute("Include")!.Value.Replace('\\', '/')).ToArray();
        CollectionAssert.AreEqual(new[] { "../ProgramKit.Contracts/ProgramKit.Contracts.csproj" }, references);
    }

    [TestMethod]
    public void Adapter_assets_and_source_contain_no_kernel_provider_session_test_eng_or_private_spec_kit_dependency()
    {
        string root = Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter");
        string assetsPath = Path.Combine(root, "obj", "project.assets.json");
        JsonObject assets = JsonNode.Parse(File.ReadAllText(assetsPath))!.AsObject();
        string[] projectLibraries = assets["libraries"]!.AsObject()
            .Where(static property => property.Value?["type"]?.GetValue<string>() == "project")
            .Select(static property => property.Key)
            .ToArray();
        CollectionAssert.AreEqual(new[] { "ProgramKit.Contracts/1.0.0" }, projectLibraries);

        foreach (string path in Directory.EnumerateFiles(root, "*.cs", SearchOption.AllDirectories).Where(static path => !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.Ordinal)))
        {
            string source = File.ReadAllText(path);
            Assert.IsFalse(source.Contains("ProgramKit.Kernel", StringComparison.Ordinal), path);
            Assert.IsFalse(source.Contains("ProgramKit.Providers", StringComparison.Ordinal), path);
            Assert.IsFalse(source.Contains("ProgramKit.SessionIntegration.Providers", StringComparison.Ordinal), path);
            Assert.IsFalse(source.Contains("Assembly.Load", StringComparison.Ordinal), path);
            Assert.IsFalse(source.Contains("HttpClient", StringComparison.Ordinal), path);
            Assert.IsFalse(source.Contains("System.Net", StringComparison.Ordinal), path);
        }
    }

    [TestMethod]
    public void Adapter_compatibility_is_an_exact_allowlist_not_a_range()
    {
        string content = File.ReadAllText(Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "Resources", "compatibility.json"));
        Assert.IsFalse(content.Contains('*'));
        Assert.IsFalse(content.Contains('>'));
        Assert.IsFalse(content.Contains('<'));
        StringAssert.Contains(content, "\"specKitVersions\": [\"0.15.1\"]");
        StringAssert.Contains(content, "\"programKitVersions\": [\"1.0.0-alpha.2\"]");
    }
}
