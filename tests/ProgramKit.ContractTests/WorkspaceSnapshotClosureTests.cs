using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Evidence;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class WorkspaceSnapshotClosureTests
{
    [TestMethod]
    public void Admitted_snapshot_is_canonical_trace_complete_and_matches_its_golden_digest()
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
            byte[] bytes = File.ReadAllBytes(snapshotPath);
            JsonObject snapshot = ContractAssertions.ParseAndValidate(ContractAssertions.WorkspaceSnapshot, System.Text.Encoding.UTF8.GetString(bytes));
            CollectionAssert.AreEqual(bytes, CanonicalJson.Encode(snapshot));

            JsonObject golden = JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture("Golden/snapshot/expected.json")))!.AsObject();
            Assert.AreEqual(golden["canonicalProfile"]!.GetValue<string>(), snapshot["canonicalProfile"]!.GetValue<string>());
            Assert.AreEqual(golden["freshness"]!.GetValue<string>(), snapshot["freshness"]!.GetValue<string>());
            foreach ((string name, JsonNode? minimum) in golden["minimumCollectionCounts"]!.AsObject())
            {
                Assert.IsTrue(snapshot[name]!.AsArray().Count >= minimum!.GetValue<int>(), name);
            }

            string[] artifactPaths = snapshot["artifacts"]!.AsArray()
                .Select(static item => item!["artifact"]!["logicalPath"]!.GetValue<string>())
                .ToArray();
            CollectionAssert.AreEqual(artifactPaths.OrderBy(static item => item, StringComparer.Ordinal).ToArray(), artifactPaths);
            Assert.IsTrue(snapshot["artifacts"]!.AsArray().All(static item => item!["trace"] is JsonObject));
            Assert.IsTrue(snapshot["relationships"]!.AsArray().All(static item => item!["trace"]!.AsArray().Count > 0));
            Assert.IsTrue(snapshot["semanticCoverage"]!.AsArray().Count > 0);
            Assert.IsTrue(snapshot["gates"]!.AsArray().Count > 0);
            Assert.IsTrue(snapshot["reviews"]!.AsArray().Count > 0);
            Assert.IsTrue(snapshot["evidence"]!.AsArray().Count > 0);
            Assert.IsTrue(snapshot["receipts"]!.AsArray().Count > 0);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Snapshot_freshness_has_one_fail_closed_result_for_every_governed_state()
    {
        const string closure = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
        const string evidence = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
        JsonObject snapshot = new() { ["closureDigest"] = closure, ["evidenceDigest"] = evidence };
        ArtifactObservation exact = new("artifact", closure, closure, "exact", "generated-owned");

        Assert.AreEqual("current", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact }, true, true, false));
        Assert.AreEqual("stale", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, evidence, evidence, new[] { exact }, true, true, false));
        Assert.AreEqual("drifted", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact with { State = "modified" } }, true, true, false));
        Assert.AreEqual("drifted", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact with { State = "missing" } }, true, true, false));
        Assert.AreEqual("drifted", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact with { State = "colliding" } }, true, true, false));
        Assert.AreEqual("unsupported", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact }, false, true, false));
        Assert.AreEqual("unavailable", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact }, true, false, false));
        Assert.AreEqual("incomplete", WorkspaceSnapshotBuilder.RecomputeFreshness(snapshot, closure, evidence, new[] { exact }, true, true, true));
    }
}
