using System;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionIntegrationSchemaContractTests
{
    private static readonly string[] Expected =
    {
        "https://schemas.program-kit.dev/v1/session-integration-definition.schema.json",
        "https://schemas.program-kit.dev/v1/session-provider-manifest.schema.json",
        "https://schemas.program-kit.dev/v1/session-integration-request.schema.json",
        "https://schemas.program-kit.dev/v1/session-installation-record.schema.json",
    };

    [TestMethod]
    public void Session_schemas_are_offline_registered_and_canonically_stable()
    {
        SchemaRegistry registry = new();
        foreach (string id in Expected)
        {
            JsonNode schema = registry.Get(id);
            Assert.AreEqual(id, schema["$id"]!.GetValue<string>());
            byte[] canonical = CanonicalJson.Encode(schema);
            CollectionAssert.AreEqual(canonical, CanonicalJson.Encode(CanonicalJson.Parse(canonical)));
            StringAssert.StartsWith(ContractSchemaResources.ReadById(id), "{");
        }

        Assert.AreEqual(Expected.Length, Expected.Count(id => registry.Digests.ContainsKey(id)));
    }

    [TestMethod]
    public void Session_schemas_are_provider_neutral_and_reference_canonical_common_types()
    {
        foreach (string id in Expected)
        {
            string schema = ContractSchemaResources.ReadById(id);
            StringAssert.Contains(schema, "program-kit.dev/v1/common.schema.json");
            Assert.IsFalse(schema.Contains(".agents/", StringComparison.OrdinalIgnoreCase));
            Assert.IsFalse(schema.Contains("codex", StringComparison.OrdinalIgnoreCase));
            _ = CanonicalJson.Parse(Encoding.UTF8.GetBytes(schema));
        }
    }
}
