using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterPreparationOrchestrationTests
{
    [TestMethod]
    public void Adapter_prepare_uses_only_public_effect_free_commands_and_repeat_is_zero_write()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            PublicCliTestInvoker invoker = new();
            PrepareCommand command = new(invoker);
            JsonObject request = SpecKitAdapterFixture.AdapterRequest("prepare");
            byte[] handoffBefore = File.ReadAllBytes(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff.yaml"));
            byte[] reviewBefore = File.ReadAllBytes(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff-review.json"));
            JsonObject first = command.Execute(workspace, request);
            Assert.AreEqual("succeeded", first["outcome"]!.GetValue<string>());
            Assert.AreEqual("adapter-files-only", first["effectState"]!.GetValue<string>());
            CollectionAssert.AreEqual(new[] { "prepare", "explain" }, invoker.Commands.ToArray());
            string generated = Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "generated");
            Assert.IsTrue(File.Exists(Path.Combine(generated, "results", "prepare.json")));
            Assert.IsTrue(File.Exists(Path.Combine(generated, "results", "explain.json")));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "src", "Reference.Status")));
            CollectionAssert.AreEqual(handoffBefore, File.ReadAllBytes(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff.yaml")));
            CollectionAssert.AreEqual(reviewBefore, File.ReadAllBytes(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff-review.json")));
            JsonObject manifest = CanonicalDocument.Parse(File.ReadAllBytes(Path.Combine(generated, "adapter-manifest.json"))).AsObject();
            Assert.AreEqual(AdapterCompatibility.Load().Digest, manifest["compatibility"]!["digest"]!.GetValue<string>());
            Assert.IsTrue(manifest["outputs"]!.AsArray().All(item => item!["logicalPath"]!.GetValue<string>().StartsWith($"specs/{SpecKitAdapterFixture.FeatureKey}/program-kit/generated/", System.StringComparison.Ordinal)));
            string beforeRepeat = TestRepository.DigestTree(workspace);

            invoker.Commands.Clear();
            JsonObject repeated = command.Execute(workspace, request);
            Assert.AreEqual(false, repeated["payload"]!["changed"]!.GetValue<bool>());
            Assert.AreEqual(beforeRepeat, TestRepository.DigestTree(workspace));
            CollectionAssert.AreEqual(new[] { "prepare", "explain" }, invoker.Commands.ToArray());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private sealed class PublicCliTestInvoker : IPublicProgramKitInvoker
    {
        public List<string> Commands { get; } = new();

        public JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath)
        {
            Commands.Add(command);
            string request = Path.Combine(workspaceRoot, requestLogicalPath.Replace('/', Path.DirectorySeparatorChar));
            var execution = TestRepository.RunCli(command, "--workspace", workspaceRoot, "--request", request, "--format", "json");
            Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            return CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(execution.StandardOutput)).AsObject();
        }
    }
}
