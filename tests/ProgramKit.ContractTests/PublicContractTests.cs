using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;
using Orbyss.ProgramKit.Providers.DotNet.Templates;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class PublicContractTests
{
    [TestMethod]
    public void Embedded_schemas_are_unique_local_draft_2020_12_documents()
    {
        var schemas = ContractSchemaResources.ReadAll();
        Assert.AreEqual(12, schemas.Count);
        string[] ids = schemas.Values.Select(schema => JsonNode.Parse(schema)!["$id"]!.GetValue<string>()).ToArray();
        Assert.AreEqual(ids.Length, ids.Distinct(StringComparer.Ordinal).Count());
        foreach (string schema in schemas.Values)
        {
            using JsonDocument document = JsonDocument.Parse(schema);
            Assert.AreEqual("https://json-schema.org/draft/2020-12/schema", document.RootElement.GetProperty("$schema").GetString());
        }
    }

    [TestMethod]
    public void Dotnet_provider_is_exact_and_generated_host_uses_verified_cshells_abi()
    {
        var manifest = DotNetProviderManifest.Create();
        CollectionAssert.Contains(manifest.Profiles.ToArray(), "dotnet10-cshells-0.0.28");
        Assert.AreEqual(manifest.DiagnosticCatalog.Identity.Digest, manifest.DiagnosticCatalog.Digest);
        Assert.IsTrue(manifest.ConformanceEvidence.Count > 0);
        JsonObject component = new() { ["namespace"] = "Consumer.Feature", ["featureClass"] = "Feature" };
        string source = DotNetTemplates.ProgramSource(component);
        StringAssert.Contains(source, "WithAssemblies(typeof(Feature).Assembly)");
        StringAssert.Contains(source, "app.MapShells()");
        Assert.IsFalse(source.Contains("FromHostAssemblies", StringComparison.Ordinal));
    }

    [TestMethod]
    public void Production_kernel_and_contracts_do_not_contain_consumer_status_semantics()
    {
        foreach (string root in new[] { Path.Combine(TestRepository.Root, "src", "ProgramKit.Contracts"), Path.Combine(TestRepository.Root, "src", "ProgramKit.Kernel") })
        {
            foreach (string path in Directory.EnumerateFiles(root, "*.cs", SearchOption.AllDirectories))
                Assert.IsFalse(File.ReadAllText(path).Contains("Reference.Status", StringComparison.Ordinal), path);
        }
    }

    [TestMethod]
    public void Generated_projects_have_no_program_kit_spec_kit_or_ai_runtime_reference()
    {
        JsonObject component = new() { ["packageId"] = "Consumer.Feature", ["version"] = "1.0.0" };
        JsonObject application = new() { ["name"] = "Consumer.Api" };
        string projects = DotNetTemplates.ComponentProject(component) + DotNetTemplates.ApplicationProject(application, component);
        Assert.IsFalse(projects.Contains("PackageReference Include=\"ProgramKit", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(projects.Contains("SpecKit", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(projects.Contains("OpenAI", StringComparison.OrdinalIgnoreCase));
    }
}
