using System.IO;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class WorkspaceBootstrapNegativeAcceptanceTests
{
    [TestMethod]
    public void Conflicting_consumer_manifest_blocks_init_without_partial_bootstrap_state()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            File.WriteAllText(Path.Combine(workspace, "program-kit.yaml"), "consumer-owned: true");
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "init.json", WorkspaceBootstrapFixture.InitRequest());
            var result = TestRepository.RunCli("init", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(3, result.ExitCode, result.StandardOutput + result.StandardError);
            Assert.AreEqual("consumer-owned: true", File.ReadAllText(Path.Combine(workspace, "program-kit.yaml")));
            Assert.IsFalse(File.Exists(Path.Combine(workspace, ".program-kit", "bootstrap-evidence.json")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Range_like_release_and_remote_source_are_rejected_before_lock_publication()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            File.WriteAllBytes(Path.Combine(workspace, "program-kit.yaml"), CanonicalJson.Encode(new System.Text.Json.Nodes.JsonObject
            {
                ["schema"] = "program-kit.workspace/v1",
                ["distribution"] = WorkspaceBootstrapFixture.DistributionBinding(),
                ["factory"] = new System.Text.Json.Nodes.JsonObject { ["selections"] = new System.Text.Json.Nodes.JsonArray() },
            }));
            var requestDocument = WorkspaceBootstrapFixture.RestoreRequest("base");
            requestDocument["distributionBinding"]!["packageVersion"] = ">=1.0.0";
            requestDocument["allowedSources"]!.AsArray().Add("https://example.invalid/package");
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore.json", requestDocument);
            var result = TestRepository.RunCli("restore", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(3, result.ExitCode);
            Assert.IsFalse(File.Exists(Path.Combine(workspace, "program-kit.lock.json")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }
}
