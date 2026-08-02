using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
[TestCategory("PlatformLifecycle")]
public sealed class SpecKitAdapterQuickstartAcceptanceTests
{
    [TestMethod]
    [DataRow("reference-status")]
    [DataRow("inventory-health")]
    public void Clean_packaged_consumer_reaches_evaluated_running_isolated_product(string scenarioName)
    {
        SpecKitAdapterScenario scenario = scenarioName == "reference-status"
            ? SpecKitAdapterFixture.ReferenceStatus
            : SpecKitAdapterFixture.InventoryHealth;
        using SpecKitAdapterPackagedWorkspace consumer = SpecKitAdapterPackagedWorkspace.CreateClean(scenario, includeDependencyMirror: true);

        Assert.IsFalse(File.Exists(Path.Combine(consumer.Root, "program-kit.yaml")));
        Assert.IsFalse(File.Exists(Path.Combine(consumer.Root, "program-kit.lock.json")));
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "specs")));
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "requests")));
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "products")));

        consumer.InitializeFactory();
        consumer.StageConsumerIntent();
        Assert.IsTrue(File.Exists(Path.Combine(consumer.Root, "tests", "Fixtures", "SpecKitAdapter", scenario.FixtureName, "spec.md")));
        Assert.IsFalse(Directory.Exists(Path.Combine(consumer.Root, "specs", scenario.FeatureKey, "program-kit")));
        consumer.StageReviewedHandoff();
        consumer.ApproveCommittedHandoff();

        ProcessResult validated = consumer.RunAdapter("validate", consumer.WriteAdapterRequest("validate", requestedEffect: "none"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(validated);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(validated, "succeeded", "none");

        ProcessResult prepared = consumer.RunAdapter("prepare", consumer.WriteAdapterRequest("prepare", requestedEffect: "none"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(prepared);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(prepared, "succeeded", "adapter-files-only");

        ProcessResult explained = consumer.RunAdapter("explain", consumer.WriteAdapterRequest("explain", requestedEffect: "none"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(explained);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(explained, "succeeded", "none");

        JsonObject grant = consumer.RecordAuthority("committed");
        ProcessResult constructed = consumer.RunAdapter("construct", consumer.WriteAdapterRequest("construct", grant, "committed"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(constructed);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(constructed, "succeeded", "program-kit-committed");
        Assert.IsTrue(File.Exists(Path.Combine(consumer.Root, "products", scenario.ApplicationName, scenario.ApplicationName + ".csproj")));

        ProcessResult evaluated = consumer.RunAdapter("evaluate", consumer.WriteAdapterRequest("evaluate", requestedEffect: "none"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(evaluated);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(evaluated, "succeeded", "adapter-files-only");

        SpecKitAdapterGeneratedProduct.VerifyRelocatableRuntime(consumer);
    }
}
