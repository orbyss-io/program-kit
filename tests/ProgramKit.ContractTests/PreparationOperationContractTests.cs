using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Cli.Composition;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class PreparationOperationContractTests
{
    [TestMethod]
    public void Public_prepare_returns_exact_ungranted_proposal_with_zero_filesystem_effect()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
            Publish(workspace, translation);
            string requestPath = Path.Combine(workspace, translation.FeatureRoot.Replace('/', Path.DirectorySeparatorChar), "requests", "prepare.json");
            JsonObject request = CanonicalJson.Parse(File.ReadAllBytes(requestPath)).AsObject();
            string before = TestRepository.DigestTree(workspace);

            _ = ProgramKitComposition.CreateKernel().Prepare(workspace, requestPath);

            var execution = TestRepository.RunCli("prepare", "--workspace", workspace, "--request", requestPath, "--format", "json");

            Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
            JsonObject proposal = result["payload"]!["proposal"]!.AsObject();
            ContractAssertions.AssertValid(ContractSchemaResources.PreparationProposalId, proposal);
            Assert.AreEqual(CanonicalJson.Digest(request), proposal["requestBinding"]!.GetValue<string>());
            StringAssert.StartsWith(proposal["closureDigest"]!.GetValue<string>(), "sha256:");
            StringAssert.StartsWith(proposal["liveStateDigest"]!.GetValue<string>(), "sha256:");
            Assert.AreEqual(proposal["closureDigest"]!.GetValue<string>(), proposal["ungrantedProjection"]!["expectedState"]!["closureDigest"]!.GetValue<string>());
            Assert.AreEqual(proposal["liveStateDigest"]!.GetValue<string>(), proposal["ungrantedProjection"]!["expectedState"]!["liveStateDigest"]!.GetValue<string>());
            Assert.AreEqual("construct", proposal["operation"]!.GetValue<string>());
            Assert.AreEqual("candidate-only", proposal["maximumEffect"]!.GetValue<string>());
            Assert.AreEqual(2, proposal["subjects"]!.AsArray().Count);
            Assert.IsTrue(proposal["authorityRequirements"]!.AsArray().Count >= 6);
            Assert.IsTrue(proposal["explanation"]!.AsObject().Count > 0);
            Assert.IsFalse(proposal["ungrantedProjection"]!.AsObject().ContainsKey("authorityGrant"));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "src", "Reference.Status")));

            JsonObject digestMaterial = (JsonObject)proposal.DeepClone();
            string declaredDigest = digestMaterial["digest"]!.GetValue<string>();
            digestMaterial.Remove("digest");
            Assert.AreEqual(declaredDigest, CanonicalJson.Digest(digestMaterial));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Public_prepare_is_repeatable_and_refuses_a_stale_workspace_lock()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
            Publish(workspace, translation);
            string requestPath = Path.Combine(workspace, translation.FeatureRoot.Replace('/', Path.DirectorySeparatorChar), "requests", "prepare.json");
            var first = TestRepository.RunCli("prepare", "--workspace", workspace, "--request", requestPath, "--format", "json");
            var second = TestRepository.RunCli("prepare", "--workspace", workspace, "--request", requestPath, "--format", "json");
            Assert.AreEqual(0, first.ExitCode, first.StandardOutput + first.StandardError);
            Assert.AreEqual(first.StandardOutput, second.StandardOutput);

            File.AppendAllText(Path.Combine(workspace, "program-kit.lock.json"), " ");
            var stale = TestRepository.RunCli("prepare", "--workspace", workspace, "--request", requestPath, "--format", "json");
            Assert.AreNotEqual(0, stale.ExitCode);
            JsonObject refusal = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, stale.StandardOutput);
            Assert.AreEqual("none", refusal["effectState"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void Publish(string workspace, TranslationResult translation)
    {
        foreach ((string logicalPath, byte[] bytes) in translation.Bytes.OrderBy(static item => item.Key, StringComparer.Ordinal))
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllBytes(path, bytes);
        }
    }
}
