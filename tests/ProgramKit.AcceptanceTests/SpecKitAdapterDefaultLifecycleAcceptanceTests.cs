using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class SpecKitAdapterDefaultLifecycleAcceptanceTests
{
    [TestMethod]
    public void Default_drift_and_disable_reenable_preserve_reviewed_meaning_and_all_existing_bytes()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            ConvertReviewedHandoffToInheritedSelection(workspace);
            JsonObject config = ReadConfig(workspace);
            config["activation"]!["features"]![SpecKitAdapterFixture.FeatureKey]!.AsObject().Remove("selection");
            WriteConfig(workspace, config);

            JsonObject initial = ValidateCommand.Execute(workspace, SpecKitAdapterFixture.AdapterRequest("validate"));
            Assert.AreEqual(false, initial["payload"]!["selectionDiverged"]!.GetValue<bool>());
            ChangeWorkspaceDefault(workspace);

            string marker = Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "generated", "preserved-result.json");
            Directory.CreateDirectory(Path.GetDirectoryName(marker)!);
            File.WriteAllText(marker, "preserve across default and activation lifecycle");
            string before = TestRepository.DigestTree(workspace);
            JsonObject drifted = ValidateCommand.Execute(workspace, SpecKitAdapterFixture.AdapterRequest("validate"));
            Assert.AreEqual("succeeded", drifted["outcome"]!.GetValue<string>());
            Assert.AreEqual(true, drifted["payload"]!["selectionDiverged"]!.GetValue<bool>());
            Assert.AreEqual("dotnet-default", drifted["payload"]!["selectionAlias"]!.GetValue<string>());
            Assert.AreEqual("dotnet-alternate", drifted["payload"]!["currentSelectionAlias"]!.GetValue<string>());
            Assert.AreEqual(true, drifted["payload"]!["requiresRehandoff"]!.GetValue<bool>());
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));

            JsonObject disableRequest = SpecKitAdapterFixture.AdapterRequest("disable");
            JsonObject disabledProposal = DisableCommand.Execute(workspace, disableRequest);
            Assert.AreEqual(false, disabledProposal["payload"]!["applied"]!.GetValue<bool>());
            Assert.AreEqual(true, disabledProposal["payload"]!["preservesHistoricalArtifacts"]!.GetValue<bool>());
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));

            config["activation"]!["features"]![SpecKitAdapterFixture.FeatureKey]!["applicability"] = "disabled";
            WriteConfig(workspace, config);
            before = TestRepository.DigestTree(workspace);
            RecordingInvoker invoker = new();
            JsonObject inactive = new PrepareCommand(invoker).Execute(workspace, SpecKitAdapterFixture.AdapterRequest("prepare"));
            Assert.AreEqual("not-applicable", inactive["outcome"]!.GetValue<string>());
            Assert.AreEqual(0, invoker.InvocationCount);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            Assert.IsTrue(File.Exists(marker));

            JsonObject activation = ActivateCommand.Execute(workspace, SpecKitAdapterFixture.AdapterRequest("activate"));
            Assert.AreEqual(false, activation["payload"]!["applied"]!.GetValue<bool>());
            Assert.AreEqual("dotnet-alternate", activation["payload"]!["effectiveSelection"]!["alias"]!.GetValue<string>());
            Assert.AreEqual(true, activation["payload"]!["requiresHandoffReview"]!.GetValue<bool>());
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));

            config["activation"]!["features"]![SpecKitAdapterFixture.FeatureKey]!["applicability"] = "applicable";
            WriteConfig(workspace, config);
            before = TestRepository.DigestTree(workspace);
            JsonObject reenabled = ValidateCommand.Execute(workspace, SpecKitAdapterFixture.AdapterRequest("validate"));
            Assert.AreEqual(true, reenabled["payload"]!["requiresRehandoff"]!.GetValue<bool>());
            Assert.AreEqual(0, invoker.InvocationCount);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            Assert.IsTrue(File.Exists(marker));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void ConvertReviewedHandoffToInheritedSelection(string workspace)
    {
        string featureRoot = Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit");
        string handoffPath = Path.Combine(featureRoot, "handoff.yaml");
        JsonObject handoff = RestrictedYaml.Parse(File.ReadAllText(handoffPath));
        handoff["effectiveSelection"]!["source"] = "workspace-lock-default";
        JsonObject trace = handoff["trace"]!.AsArray().OfType<JsonObject>()
            .Single(item => item["targetPointer"]!.GetValue<string>() == "/effectiveSelection");
        trace["observedValue"] = handoff["effectiveSelection"]!.DeepClone();
        File.WriteAllBytes(handoffPath, CanonicalJson.Encode(handoff));
        BoundHandoff bound = new HandoffBinder().Bind(handoff, requireComplete: true);

        string reviewPath = Path.Combine(featureRoot, "handoff-review.json");
        JsonObject review = CanonicalDocument.Parse(File.ReadAllBytes(reviewPath)).AsObject();
        review["handoff"]!["digest"] = bound.Digest;
        review.Remove("digest");
        review["digest"] = CanonicalDocument.Digest(review);
        File.WriteAllBytes(reviewPath, CanonicalDocument.Encode(review));
    }

    private static void ChangeWorkspaceDefault(string workspace)
    {
        string path = Path.Combine(workspace, "program-kit.lock.json");
        JsonObject workspaceLock = CanonicalDocument.Parse(File.ReadAllBytes(path)).AsObject();
        JsonObject alternate = (JsonObject)workspaceLock["selections"]!.AsArray()[0]!.DeepClone();
        alternate["alias"] = "dotnet-alternate";
        workspaceLock["selections"]!.AsArray().Add(alternate);
        workspaceLock["defaultSelection"] = "dotnet-alternate";
        File.WriteAllBytes(path, CanonicalDocument.Encode(workspaceLock));
    }

    private static JsonObject ReadConfig(string workspace)
    {
        string path = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
        return RestrictedYaml.Parse(File.ReadAllText(path));
    }

    private static void WriteConfig(string workspace, JsonObject config)
    {
        string path = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
        File.WriteAllBytes(path, CanonicalJson.Encode(config));
    }

    private sealed class RecordingInvoker : IPublicProgramKitInvoker
    {
        public int InvocationCount { get; private set; }

        public JsonObject Invoke(string workspaceRoot, string operation, string requestLogicalPath)
        {
            InvocationCount++;
            throw new AssertFailedException("Disable/re-enable silently resumed Program Kit work.");
        }
    }
}
