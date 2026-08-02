using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class HumanLedSessionWorkflowAcceptanceTests
{
    [TestMethod]
    public void Typed_factory_continuation_leads_through_explain_authorize_construct_and_evaluate()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            string incompletePath = Path.Combine(workspace, "requests", "incomplete-live-review.json");
            File.WriteAllText(incompletePath, "{\"schema\":\"program-kit.factory-request/v1\",\"canonicalProfile\":\"program-kit.canonical-json/v1\",\"operation\":\"explain\"}");
            (int incompleteExit, string incompleteOutput, _) = TestRepository.RunCli("explain", "--workspace", workspace, "--request", incompletePath, "--format", "json");
            Assert.AreEqual(2, incompleteExit);
            JsonObject incomplete = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, incompleteOutput);
            Assert.AreEqual("needs-input", incomplete["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", incomplete["effectState"]!.GetValue<string>());
            Assert.IsTrue(incomplete["continuation"]!["missingInputs"]!.AsArray().Count >= 5);

            (int explainExit, string explainOutput, _) = TestRepository.RunCli("explain", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "explain.json"), "--format", "json");
            Assert.AreEqual(0, explainExit, explainOutput);
            JsonObject explained = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, explainOutput);
            Assert.AreEqual("succeeded", explained["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", explained["effectState"]!.GetValue<string>());

            JsonObject noGrant = JsonNode.Parse(File.ReadAllText(Path.Combine(workspace, "requests", "construct.json")))!.AsObject();
            noGrant.Remove("authorityGrant");
            string noGrantPath = Path.Combine(workspace, "requests", "construct-without-grant.json");
            File.WriteAllText(noGrantPath, noGrant.ToJsonString());
            string beforeDecline = TestRepository.DigestTree(workspace);
            (int noGrantExit, string noGrantOutput, _) = TestRepository.RunCli("construct", "--workspace", workspace, "--request", noGrantPath, "--format", "json");
            Assert.AreEqual(2, noGrantExit);
            JsonObject missingAuthority = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, noGrantOutput);
            Assert.AreEqual("needs-input", missingAuthority["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", missingAuthority["effectState"]!.GetValue<string>());
            Assert.IsTrue(missingAuthority["continuation"]!["missingInputs"]!.AsArray().Any(static item => item!["identity"]!.GetValue<string>() == "authoritygrant"));
            Assert.AreEqual(beforeDecline, TestRepository.DigestTree(workspace), "Declining to provide authority must leave the workspace unchanged.");

            (int constructExit, string constructOutput, _) = TestRepository.RunCli("construct", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "construct.json"), "--format", "json");
            Assert.AreEqual(0, constructExit, constructOutput);
            JsonObject constructed = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, constructOutput);
            Assert.AreEqual("succeeded", constructed["outcome"]!.GetValue<string>());
            Assert.AreEqual("committed", constructed["effectState"]!.GetValue<string>());
            Assert.AreEqual("complete", constructed["primaryDisposition"]!.GetValue<string>());

            string beforeEvaluate = TestRepository.DigestTree(workspace);
            (int evaluateExit, string evaluateOutput, _) = TestRepository.RunCli("evaluate", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "evaluate.json"), "--format", "json");
            Assert.AreEqual(0, evaluateExit, evaluateOutput);
            JsonObject evaluated = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, evaluateOutput);
            Assert.AreEqual("succeeded", evaluated["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", evaluated["effectState"]!.GetValue<string>());
            Assert.AreEqual("complete", evaluated["primaryDisposition"]!.GetValue<string>());
            Assert.AreEqual(beforeEvaluate, TestRepository.DigestTree(workspace), "Evaluation must remain read-only.");
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Incomplete_authority_is_reported_then_exact_authorized_work_can_be_evaluated_read_only()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        JsonObject declined = JsonNode.Parse(File.ReadAllText(requests.Install))!.AsObject();
        declined.Remove("authorityGrant");
        string declinedPath = Path.Combine(workspace.Root, "requests", "session-install-declined.json");
        File.WriteAllText(declinedPath, declined.ToJsonString());

        (int declinedExit, string declinedResult, _) = TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", declinedPath, "--format", "json");
        Assert.AreEqual(3, declinedExit);
        Assert.AreEqual("request-approval", JsonNode.Parse(declinedResult)!["primaryDisposition"]!.GetValue<string>());

        Assert.AreEqual(0, TestRepository.RunCli("session", "explain", "--workspace", workspace.Root, "--request", requests.Explain, "--format", "json").ExitCode);
        Assert.AreEqual(0, TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json").ExitCode);
        string before = TestRepository.DigestTree(workspace.Root);
        (int verifyExit, string verifyResult, _) = TestRepository.RunCli("session", "verify", "--workspace", workspace.Root, "--request", requests.Verify, "--format", "json");
        Assert.AreEqual(0, verifyExit, verifyResult);
        Assert.AreEqual(before, TestRepository.DigestTree(workspace.Root));
    }
}
