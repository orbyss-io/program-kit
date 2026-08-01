using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Schemas;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeMachineReviewSchemaContractTests
{
    [TestMethod]
    public void Machine_review_schema_is_embedded_canonical_and_fail_closed_for_acceptance()
    {
        string text = ClaudeSchemaResources.ReadMachineReview();
        JsonNode schema = CanonicalJson.Parse(Encoding.UTF8.GetBytes(text));
        Assert.AreEqual(ClaudeSchemaResources.MachineReviewId, schema["$id"]!.GetValue<string>());
        CollectionAssert.AreEqual(CanonicalJson.Encode(schema), CanonicalJson.Encode(CanonicalJson.Parse(CanonicalJson.Encode(schema))));
        StringAssert.Contains(text, "\"humanDecision\"");
        StringAssert.Contains(text, "\"accepted\"");
        Assert.AreEqual(0, schema["allOf"]![0]!["then"]!["properties"]!["conformanceSummary"]!["properties"]!["notEvaluated"]!["const"]!.GetValue<int>());
        Assert.AreEqual(10, schema["properties"]!["liveTrials"]!["minItems"]!.GetValue<int>());
        Assert.AreEqual(10, schema["properties"]!["liveTrials"]!["maxItems"]!.GetValue<int>());
        Assert.IsFalse(schema["additionalProperties"]!.GetValue<bool>());
    }
}
