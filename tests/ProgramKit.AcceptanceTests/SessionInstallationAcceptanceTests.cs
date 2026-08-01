using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionInstallationAcceptanceTests
{
    [TestMethod]
    public void Explain_install_and_verify_are_deterministic_across_ten_fresh_workspaces()
    {
        string? expectedSkillDigest = null;
        for (int trial = 0; trial < 10; trial++)
        {
            using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
            SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);

            (int explainExit, string explain, _) = TestRepository.RunCli("session", "explain", "--workspace", workspace.Root, "--request", requests.Explain, "--format", "json");
            Assert.AreEqual(0, explainExit, explain);
            JsonObject explainResult = JsonNode.Parse(explain)!.AsObject();
            Assert.AreEqual("none", explainResult["effectState"]!.GetValue<string>());

            (int installExit, string install, _) = TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json");
            Assert.AreEqual(0, installExit, install);
            Assert.AreEqual("committed", JsonNode.Parse(install)!["effectState"]!.GetValue<string>());

            (int verifyExit, string verify, _) = TestRepository.RunCli("session", "verify", "--workspace", workspace.Root, "--request", requests.Verify, "--format", "json");
            Assert.AreEqual(0, verifyExit, verify);
            JsonNode verification = JsonNode.Parse(verify)!;
            Assert.AreEqual("exact", verification["session"]!["state"]!.GetValue<string>());
            Assert.AreEqual("reload-required", verification["session"]!["sessionAvailability"]!.GetValue<string>());

            string observed = workspace.Fingerprint(".agents/skills/program-kit/SKILL.md");
            expectedSkillDigest ??= observed;
            Assert.AreEqual(expectedSkillDigest, observed);
        }
    }
}
