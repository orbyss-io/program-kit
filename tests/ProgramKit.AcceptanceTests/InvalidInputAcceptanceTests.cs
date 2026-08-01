using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class InvalidInputAcceptanceTests
{
    [TestMethod]
    [DataRow("MissingSelection")]
    [DataRow("AmbiguousSelection")]
    [DataRow("ConflictingIdentity")]
    [DataRow("IncompatibleContract")]
    [DataRow("UnavailableInput")]
    [DataRow("DuplicateKey")]
    [DataRow("RestrictedYaml")]
    [DataRow("UnsafeDisclosure")]
    public void Invalid_fixture_returns_its_stable_diagnostic_without_workspace_effect(string fixtureName)
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            JsonObject fixture = JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture($"Invalid/{fixtureName}/fixture.json")))!.AsObject();
            string request = ApplyMutation(workspace, fixture["mutation"]!.GetValue<string>());
            string before = TestRepository.DigestTree(workspace);

            var execution = TestRepository.RunCli(
                "explain", "--workspace", workspace,
                "--request", request,
                "--format", "json");

            Assert.AreNotEqual(0, execution.ExitCode, fixtureName);
            Assert.AreEqual(string.Empty, execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            string[] diagnostics = result["diagnostics"]!["items"]!.AsArray()
                .Select(static item => item!["id"]!.GetValue<string>())
                .ToArray();
            CollectionAssert.Contains(diagnostics, fixture["expectedDiagnostic"]!.GetValue<string>(), fixtureName);
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
            Assert.AreEqual(before, TestRepository.DigestTree(workspace), fixtureName);
            Assert.IsFalse(execution.StandardOutput.Contains("hunter2", StringComparison.OrdinalIgnoreCase));
            Assert.IsFalse(execution.StandardOutput.Contains("password=", StringComparison.OrdinalIgnoreCase));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static string ApplyMutation(string workspace, string mutation)
    {
        string request = Path.Combine(workspace, "requests", "invalid.json");
        string source = Path.Combine(workspace, "requests", "explain.json");
        JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(source)).AsObject();
        switch (mutation)
        {
            case "remove-selection:evaluation":
                RemoveSelection(document, "evaluation");
                break;
            case "duplicate-selection:evaluation":
                JsonObject evaluation = document["selections"]!.AsArray().OfType<JsonObject>()
                    .Single(static item => item["role"]!.GetValue<string>() == "evaluation");
                document["selections"]!.AsArray().Add(evaluation.DeepClone());
                break;
            case "replace-root-identity-digest":
                document["rootBundle"]!["identity"]!["digest"] = $"sha256:{new string('0', 64)}";
                break;
            case "replace-target-profile":
                JsonObject profile = document["selections"]!.AsArray().OfType<JsonObject>()
                    .Single(static item => item["role"]!.GetValue<string>() == "target-profile");
                profile["selected"]!["name"] = "unsupported-profile";
                profile["selected"]!["digest"] = $"sha256:{new string('9', 64)}";
                break;
            case "replace-root-logical-path":
                document["rootBundle"]!["logicalPath"] = "definitions/missing-bundle.json";
                break;
            case "duplicate-json-operation-key":
                string json = Encoding.UTF8.GetString(CanonicalJson.Encode(document));
                File.WriteAllText(request, $"{{\"operation\":\"explain\",{json[1..]}", new UTF8Encoding(false));
                return request;
            case "yaml-anchor-alias":
                request = Path.Combine(workspace, "requests", "invalid.yaml");
                File.WriteAllText(request, "schema: &schema program-kit.factory-request/v1\ncopy: *schema\n", new UTF8Encoding(false));
                return request;
            case "inject-secret-marker":
                document["unexpectedSecret"] = "password=hunter2";
                break;
            default:
                throw new InvalidOperationException($"Unsupported invalid-fixture mutation: {mutation}");
        }

        File.WriteAllBytes(request, CanonicalJson.Encode(document));
        return request;
    }

    private static void RemoveSelection(JsonObject document, string role)
    {
        JsonArray selections = document["selections"]!.AsArray();
        int index = selections.Select(static (item, index) => (item, index))
            .Single(item => item.item!["role"]!.GetValue<string>() == role).index;
        selections.RemoveAt(index);
    }
}
