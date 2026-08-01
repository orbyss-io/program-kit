using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class HumanLedSessionWorkflowAcceptanceTests
{
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
