using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class SpecKitAdapterProductRuntimeAcceptanceTests
{
    [TestMethod]
    public void Adapter_generated_product_relocates_builds_tests_runs_and_has_no_authoring_runtime_dependency()
    {
        using SpecKitAdapterPackagedWorkspace consumer = SpecKitAdapterPackagedWorkspace.Create(includeDependencyMirror: true);
        consumer.ApproveCommittedHandoff();
        ProcessResult prepared = consumer.RunAdapter("prepare", consumer.WriteAdapterRequest("prepare", requestedEffect: "none"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(prepared);
        JsonObject grant = consumer.RecordAuthority("committed");
        ProcessResult constructed = consumer.RunAdapter("construct", consumer.WriteAdapterRequest("construct", grant, "committed"));
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(constructed);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(constructed, "succeeded", "program-kit-committed");

        SpecKitAdapterGeneratedProduct.VerifyRelocatableRuntime(consumer);
    }
}
