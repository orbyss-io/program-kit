using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterApplicabilityAcceptanceTests
{
    [TestMethod]
    public void Documentation_only_and_unactivated_assist_hooks_have_zero_factory_or_file_effects()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace(restoreFactory: false);
        try
        {
            JsonObject config = ReadConfig(workspace);
            config["activation"]!["features"]!["documentation-only"] = new JsonObject
            {
                ["mode"] = "required",
                ["applicability"] = "not-applicable",
                ["decisionSource"] = new JsonObject { ["kind"] = "human-decision", ["name"] = "documentation-review" },
            };
            WriteConfig(workspace, config);
            string preserved = Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "preserved-result.json");
            File.WriteAllText(preserved, "preserved factory feature state");

            RecordingInvoker invoker = new();
            JsonObject request = ForFeature("handoff", "documentation-only");
            string before = TestRepository.DigestTree(workspace);
            AssertOutcome(HandoffCommand.Execute(workspace, request), "not-applicable");
            request["operation"] = "validate";
            AssertOutcome(ValidateCommand.Execute(workspace, request), "not-applicable");
            request["operation"] = "prepare";
            AssertOutcome(new PrepareCommand(invoker).Execute(workspace, request), "not-applicable");
            Assert.AreEqual(0, invoker.InvocationCount);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "specs", "documentation-only", "program-kit")));
            Assert.IsTrue(File.Exists(preserved));

            JsonObject inheritedAssist = ForFeature("prepare", "unlisted-feature");
            before = TestRepository.DigestTree(workspace);
            JsonObject assistResult = new PrepareCommand(invoker).Execute(workspace, inheritedAssist);
            AssertOutcome(assistResult, "not-applicable");
            Assert.AreEqual(false, assistResult["payload"]!["blocking"]!.GetValue<bool>());
            Assert.AreEqual(0, invoker.InvocationCount);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));

            config["activation"]!["defaultMode"] = "required";
            WriteConfig(workspace, config);
            before = TestRepository.DigestTree(workspace);
            JsonObject requiredResult = new PrepareCommand(invoker).Execute(workspace, inheritedAssist);
            AssertOutcome(requiredResult, "needs-input");
            Assert.AreEqual(0, invoker.InvocationCount);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static JsonObject ForFeature(string operation, string featureKey)
    {
        JsonObject request = SpecKitAdapterFixture.AdapterRequest(operation);
        request["feature"]!["key"] = featureKey;
        request["handoff"]!["logicalPath"] = $"specs/{featureKey}/program-kit/handoff.yaml";
        request["review"]!["logicalPath"] = $"specs/{featureKey}/program-kit/handoff-review.json";
        request["outputRoot"] = $"specs/{featureKey}/program-kit/generated";
        return request;
    }

    private static JsonObject ReadConfig(string workspace)
    {
        string path = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
        return RestrictedYaml.Parse(File.ReadAllText(path));
    }

    private static void WriteConfig(string workspace, JsonObject config)
    {
        string path = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
        File.WriteAllBytes(path, CanonicalJson.Encode(config));
    }

    private static void AssertOutcome(JsonObject result, string expected)
    {
        AdapterSchemaValidator.Validate("adapter-result.schema.json", result);
        Assert.AreEqual(expected, result["outcome"]!.GetValue<string>());
        Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
    }

    private sealed class RecordingInvoker : IPublicProgramKitInvoker
    {
        public int InvocationCount { get; private set; }

        public JsonObject Invoke(string workspaceRoot, string operation, string requestLogicalPath)
        {
            InvocationCount++;
            throw new AssertFailedException("Inactive adapter work launched Program Kit.");
        }
    }
}
