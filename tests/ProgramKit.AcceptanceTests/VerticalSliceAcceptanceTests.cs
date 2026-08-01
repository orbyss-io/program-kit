using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class VerticalSliceAcceptanceTests
{
    [TestMethod]
    public void Explain_is_repeatable_canonical_and_read_only()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            string before = TestRepository.DigestTree(workspace);
            string request = Path.Combine(workspace, "requests", "explain.yaml");
            var first = TestRepository.RunCli("explain", "--workspace", workspace, "--request", request, "--format", "json");
            var second = TestRepository.RunCli("explain", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(0, first.ExitCode);
            Assert.AreEqual(string.Empty, first.StandardError);
            Assert.AreEqual(first.StandardOutput, second.StandardOutput);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            JsonNode result = JsonNode.Parse(first.StandardOutput)!;
            Assert.AreEqual("succeeded", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
        }
        finally { TestRepository.DeleteWorkspace(workspace); }
    }

    [TestMethod]
    public void Construct_then_evaluate_proves_admission_and_read_only_evaluation()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            string constructRequest = Path.Combine(workspace, "requests", "construct.yaml");
            var construct = TestRepository.RunCli("construct", "--workspace", workspace, "--request", constructRequest, "--format", "json");
            Assert.AreEqual(0, construct.ExitCode, construct.StandardOutput + construct.StandardError);
            Assert.IsTrue(File.Exists(Path.Combine(workspace, ".program-kit", "construction-receipt.json")));
            Assert.IsTrue(File.Exists(Path.Combine(workspace, "feeds", "component", "Reference.Status.1.0.0.nupkg")));
            string before = TestRepository.DigestTree(workspace);
            string evaluateRequest = Path.Combine(workspace, "requests", "evaluate.yaml");
            var evaluate = TestRepository.RunCli("evaluate", "--workspace", workspace, "--request", evaluateRequest, "--format", "json");
            Assert.AreEqual(0, evaluate.ExitCode, evaluate.StandardOutput + evaluate.StandardError);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
        }
        finally { TestRepository.DeleteWorkspace(workspace); }
    }
}
