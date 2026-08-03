using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
[TestCategory("PlatformLifecycle")]
public sealed class SpecKitAdapterNegativeMatrixAcceptanceTests
{
    [TestMethod]
    public void Bootstrap_and_resolution_negative_groups_refuse_effects_with_exact_public_diagnostics()
    {
        string initWorkspace = TestRepository.CreateEmptyWorkspace();
        string restoreWorkspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            File.WriteAllText(Path.Combine(initWorkspace, "program-kit.yaml"), "consumer-owned: true");
            string initRequest = WorkspaceBootstrapFixture.WriteRequest(initWorkspace, "init.json", WorkspaceBootstrapFixture.InitRequest());
            var init = TestRepository.RunCli("init", "--workspace", initWorkspace, "--request", initRequest, "--format", "json");
            Assert.AreEqual(3, init.ExitCode, init.StandardOutput + init.StandardError);
            AssertKernelFailure(init.StandardOutput, "workspace", "none", "repair", DiagnosticIds.GeneratedDrift);
            Assert.AreEqual("consumer-owned: true", File.ReadAllText(Path.Combine(initWorkspace, "program-kit.yaml")));
            Assert.IsFalse(File.Exists(Path.Combine(initWorkspace, ".program-kit", "bootstrap-evidence.json")), "NEG-001 published trusted bootstrap evidence.");

            File.WriteAllBytes(Path.Combine(restoreWorkspace, "program-kit.yaml"), CanonicalJson.Encode(new JsonObject
            {
                ["schema"] = "program-kit.workspace/v1",
                ["distribution"] = WorkspaceBootstrapFixture.DistributionBinding(),
                ["factory"] = new JsonObject { ["selections"] = new JsonArray() },
            }));
            JsonObject invalidRestore = WorkspaceBootstrapFixture.RestoreRequest("base");
            invalidRestore["distributionBinding"]!["packageVersion"] = ">=1.0.0";
            invalidRestore["allowedSources"]!.AsArray().Add("https://example.invalid/package");
            string restoreRequest = WorkspaceBootstrapFixture.WriteRequest(restoreWorkspace, "restore.json", invalidRestore);
            var restore = TestRepository.RunCli("restore", "--workspace", restoreWorkspace, "--request", restoreRequest, "--format", "json");
            Assert.AreEqual(3, restore.ExitCode, restore.StandardOutput + restore.StandardError);
            AssertKernelFailure(restore.StandardOutput, "request", "none", "revise", DiagnosticIds.InvalidInput);
            Assert.IsFalse(File.Exists(Path.Combine(restoreWorkspace, "program-kit.lock.json")), "NEG-002 published a factory lock.");
        }
        finally
        {
            TestRepository.DeleteWorkspace(initWorkspace);
            TestRepository.DeleteWorkspace(restoreWorkspace);
        }
    }

    [TestMethod]
    public void Adapter_negative_groups_have_real_boundary_triggers_and_no_unauthorized_product_effect()
    {
        using SpecKitAdapterPackagedWorkspace consumer = SpecKitAdapterPackagedWorkspace.Create(includeDependencyMirror: false);
        string configPath = Path.Combine(consumer.Root, ".specify", "extensions", "orbyss-program-kit-adapter", "orbyss-program-kit-adapter-config.yml");
        string handoffPath = Path.Combine(consumer.Root, "specs", consumer.Scenario.FeatureKey, "program-kit", "handoff.yaml");
        string reviewPath = Path.Combine(consumer.Root, "specs", consumer.Scenario.FeatureKey, "program-kit", "handoff-review.json");
        string implementationPath = Path.Combine(consumer.Root, "tests", "Fixtures", "SpecKitAdapter", "Reference.Status", "implementation", "StatusFeature.cs");
        string lockPath = Path.Combine(consumer.Root, "program-kit.lock.json");
        byte[] config = File.ReadAllBytes(configPath);
        byte[] handoff = File.ReadAllBytes(handoffPath);
        byte[] review = File.ReadAllBytes(reviewPath);
        byte[] implementation = File.ReadAllBytes(implementationPath);
        byte[] workspaceLock = File.ReadAllBytes(lockPath);

        File.WriteAllText(configPath, "invalid: true");
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 3, "blocked", "request", "none", "provide-input", "orbyss.program-kit.spec-kit-adapter/PKSKA0002");
        File.WriteAllBytes(configPath, config);

        JsonObject unresolvedConfig = RestrictedYaml.Parse(System.Text.Encoding.UTF8.GetString(config));
        unresolvedConfig["activation"]!["features"]![consumer.Scenario.FeatureKey]!["applicability"] = "unresolved";
        File.WriteAllBytes(configPath, CanonicalDocument.Encode(unresolvedConfig));
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 2, "needs-input", "applicability", "none", "provide-input", "orbyss.program-kit.spec-kit-adapter/PKSKA0003");
        File.WriteAllBytes(configPath, config);

        JsonObject missingSelection = CanonicalDocument.Parse(workspaceLock).AsObject();
        missingSelection["selections"] = new JsonArray();
        File.WriteAllBytes(lockPath, CanonicalDocument.Encode(missingSelection));
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 2, "needs-input", "compatibility", "none", "provide-input", "orbyss.program-kit.spec-kit-adapter/PKSKA0004");
        File.WriteAllBytes(lockPath, workspaceLock);

        JsonObject invalidHandoff = RestrictedYaml.Parse(System.Text.Encoding.UTF8.GetString(handoff));
        invalidHandoff.Remove("intentOwner");
        File.WriteAllBytes(handoffPath, CanonicalDocument.Encode(invalidHandoff));
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 3, "blocked", "handoff", "none", "revise", "orbyss.program-kit.spec-kit-adapter/PKSKA0005");
        File.WriteAllBytes(handoffPath, handoff);

        JsonObject invalidReview = CanonicalDocument.Parse(review).AsObject();
        invalidReview["decision"] = "rejected";
        File.WriteAllBytes(reviewPath, CanonicalDocument.Encode(invalidReview));
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 2, "needs-input", "handoff", "none", "request-approval", "orbyss.program-kit.spec-kit-adapter/PKSKA0006");
        File.WriteAllBytes(reviewPath, review);

        File.AppendAllText(implementationPath, Environment.NewLine + "// semantic drift");
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 3, "blocked", "handoff", "none", "revise", "orbyss.program-kit.spec-kit-adapter/PKSKA0007");
        File.WriteAllBytes(implementationPath, implementation);

        JsonObject incompatibleHandoff = RestrictedYaml.Parse(System.Text.Encoding.UTF8.GetString(handoff));
        incompatibleHandoff["definitionFamily"]!["digest"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
        JsonObject familyTrace = incompatibleHandoff["trace"]!.AsArray().OfType<JsonObject>()
            .Single(item => item["targetPointer"]!.GetValue<string>() == "/definitionFamily");
        familyTrace["observedValue"] = incompatibleHandoff["definitionFamily"]!.DeepClone();
        File.WriteAllBytes(handoffPath, CanonicalDocument.Encode(incompatibleHandoff));
        consumer.RebindReview();
        AssertAdapterFailure(consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate")), 3, "blocked", "compatibility", "none", "stop", "orbyss.program-kit.spec-kit-adapter/PKSKA0001");
        File.WriteAllBytes(handoffPath, handoff);
        File.WriteAllBytes(reviewPath, review);

        AssertAdapterFailure(consumer.RunAdapter("construct", consumer.WriteAdapterRequest("construct", requestedEffect: "none")), 2, "needs-input", "invocation", "none", "request-approval", "orbyss.program-kit.spec-kit-adapter/PKSKA0011");

        string outside = TestRepository.CreateEmptyWorkspace();
        try
        {
            string outsideRequest = Path.Combine(outside, "adapter.json");
            File.WriteAllBytes(outsideRequest, CanonicalDocument.Encode(SpecKitAdapterFixture.AdapterRequest("validate")));
            AssertAdapterFailure(consumer.RunAdapter("validate", outsideRequest), 3, "blocked", "request", "none", "stop", "orbyss.program-kit.spec-kit-adapter/PKSKA0008");
        }
        finally
        {
            TestRepository.DeleteWorkspace(outside);
        }

        AssertAdapterFailure(consumer.RunAdapter("unsupported", consumer.WriteAdapterRequest("validate")), 3, "blocked", "request", "none", "stop", "orbyss.program-kit.spec-kit-adapter/PKSKA0012");

        string toolManifest = Path.Combine(consumer.Root, ".config", "dotnet-tools.json");
        byte[] toolManifestBytes = File.ReadAllBytes(toolManifest);
        File.Delete(toolManifest);
        AssertAdapterFailure(consumer.RunAdapter("prepare", consumer.WriteAdapterRequest("prepare")), 1, "faulted", "invocation", "adapter-files-only", "retry", "orbyss.program-kit.spec-kit-adapter/PKSKA0010");
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "products")), "NEG-008 constructed a product.");
        File.WriteAllBytes(toolManifest, toolManifestBytes);

        ProcessResult prepared = consumer.RunAdapter("prepare", consumer.WriteAdapterRequest("prepare"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(prepared);
        string generatedRoot = Path.Combine(consumer.Root, "specs", consumer.Scenario.FeatureKey, "program-kit", "generated");
        string definitionPath = Path.Combine(generatedRoot, "definitions", "dotnet-component-api.json");
        byte[] definitionBytes = File.ReadAllBytes(definitionPath);
        File.AppendAllText(definitionPath, " ");
        AssertAdapterFailure(consumer.RunAdapter("prepare", consumer.WriteAdapterRequest("prepare")), 3, "blocked", "publication", "none", "repair", "orbyss.program-kit.spec-kit-adapter/PKSKA0009");
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "products")), "NEG-007 constructed a product.");
        File.WriteAllBytes(definitionPath, definitionBytes);

        JsonObject cleanupRequest = SpecKitAdapterFixture.AdapterRequest("cleanup");
        string cleanupPath = consumer.WriteJson("requests/adapter-cleanup.json", cleanupRequest);
        File.AppendAllText(definitionPath, " ");
        AssertAdapterFailure(consumer.RunAdapter("cleanup", cleanupPath), 3, "blocked", "publication", "none", "repair", "orbyss.program-kit.spec-kit-adapter/PKSKA0009");
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "products")), "NEG-009 changed product state.");
    }

    private static void AssertKernelFailure(string output, string phase, string effect, string disposition, string id)
    {
        JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, output);
        Assert.AreEqual("blocked", result["outcome"]!.GetValue<string>());
        Assert.AreEqual(phase, result["furthestPhase"]!.GetValue<string>());
        Assert.AreEqual(effect, result["effectState"]!.GetValue<string>());
        Assert.AreEqual(disposition, result["primaryDisposition"]!.GetValue<string>());
        AssertSafeDiagnostic(result["diagnostics"]!["items"]!.AsArray().Single()!.AsObject(), id);
    }

    private static void AssertAdapterFailure(ProcessResult execution, int exitCode, string outcome, string stage, string effect, string disposition, string id)
    {
        Assert.AreEqual(exitCode, execution.ExitCode, execution.Output + execution.Error);
        JsonObject result = SpecKitAdapterPackagedWorkspace.AssertAdapterResult(execution, outcome, effect);
        Assert.AreEqual(stage, result["furthestStage"]!.GetValue<string>());
        Assert.AreEqual(disposition, result["primaryDisposition"]!.GetValue<string>());
        Assert.AreEqual(0, result["artifacts"]!.AsArray().Count);
        AssertSafeDiagnostic(result["diagnostics"]!["items"]!.AsArray().Single()!.AsObject(), id);
    }

    private static void AssertSafeDiagnostic(JsonObject diagnostic, string id)
    {
        Assert.AreEqual(id, diagnostic["id"]!.GetValue<string>());
        foreach (string field in new[] { "expected", "observed" })
        {
            JsonObject value = diagnostic[field]!.AsObject();
            Assert.AreEqual("public", value["classification"]!.GetValue<string>());
            Assert.IsFalse(string.IsNullOrWhiteSpace(value["value"]!.GetValue<string>()));
        }

        Assert.IsTrue(diagnostic["evidence"]!.AsArray().Count > 0);
        Assert.IsTrue(diagnostic["remediations"]!.AsArray().Count > 0);
    }
}
