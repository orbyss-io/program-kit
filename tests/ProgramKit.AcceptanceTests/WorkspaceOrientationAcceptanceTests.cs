using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class WorkspaceOrientationAcceptanceTests
{
    [TestMethod]
    public void Fresh_session_can_navigate_authority_and_custom_source_from_snapshot_only()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            var construct = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"),
                "--format", "json");
            Assert.AreEqual(0, construct.ExitCode, construct.StandardOutput + construct.StandardError);

            string snapshotPath = Path.Combine(workspace, ".program-kit", "workspace.snapshot.json");
            JsonObject snapshot = ContractAssertions.ReadAndValidate(ContractAssertions.WorkspaceSnapshot, snapshotPath);
            VerifyArtifact(workspace, snapshot["rootBundle"]!.AsObject());
            foreach (JsonObject provenance in snapshot["provenance"]!.AsArray().OfType<JsonObject>()) VerifyArtifact(workspace, provenance);
            foreach (JsonObject receipt in snapshot["receipts"]!.AsArray().OfType<JsonObject>()) VerifyArtifact(workspace, receipt);
            foreach (JsonObject evidence in snapshot["evidence"]!.AsArray().OfType<JsonObject>()) VerifyArtifact(workspace, evidence["artifact"]!.AsObject());
            foreach (JsonObject artifact in snapshot["artifacts"]!.AsArray().OfType<JsonObject>()) VerifyArtifact(workspace, artifact["artifact"]!.AsObject());

            JsonObject custom = snapshot["artifacts"]!.AsArray().OfType<JsonObject>()
                .Single(static item => item["artifact"]!["ownership"]!.GetValue<string>() == "seeded-handoff");
            string customPath = Resolve(workspace, custom["artifact"]!["logicalPath"]!.GetValue<string>());
            StringAssert.Contains(File.ReadAllText(customPath), "operational");

            string evidencePath = Path.Combine(workspace, ".program-kit", "provider-evidence.json");
            File.AppendAllText(evidencePath, " ");
            string before = TestRepository.DigestTree(workspace);
            var evaluate = TestRepository.RunCli(
                "evaluate", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "evaluate.json"),
                "--format", "json");
            Assert.AreNotEqual(0, evaluate.ExitCode);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, evaluate.StandardOutput);
            string[] ids = result["diagnostics"]!["items"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray();
            Assert.IsTrue(ids.Contains("program-kit.kernel/PKWSP0001", StringComparer.Ordinal)
                || ids.Contains("program-kit.kernel/PKWSP0004", StringComparer.Ordinal),
                string.Join(Environment.NewLine, ids));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void VerifyArtifact(string workspace, JsonObject artifact)
    {
        string path = Resolve(workspace, artifact["logicalPath"]!.GetValue<string>());
        Assert.IsTrue(File.Exists(path), path);
        string digest = $"sha256:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant()}";
        Assert.AreEqual(artifact["digest"]!.GetValue<string>(), digest, path);
    }

    private static string Resolve(string workspace, string logicalPath)
    {
        string root = Path.GetFullPath(workspace).TrimEnd(Path.DirectorySeparatorChar);
        string path = Path.GetFullPath(Path.Combine(root, logicalPath.Replace('/', Path.DirectorySeparatorChar)));
        Assert.IsTrue(path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase));
        return path;
    }
}
