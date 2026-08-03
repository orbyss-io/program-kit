using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class SpecKitAdapterConstructionAcceptanceTests
{
    [TestMethod]
    public void Packaged_consumer_records_production_authority_then_constructs_and_evaluates_with_negative_siblings_closed()
    {
        using SpecKitAdapterPackagedWorkspace consumer = SpecKitAdapterPackagedWorkspace.Create(includeDependencyMirror: true);
        consumer.ApproveCommittedHandoff();
        string prepareRequest = consumer.WriteAdapterRequest("prepare", requestedEffect: "none");
        ProcessResult prepared = consumer.RunAdapter("prepare", prepareRequest);
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(prepared);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(prepared, "succeeded", "adapter-files-only");
        JsonObject grant = consumer.RecordAuthority("committed");
        string products = Path.Combine(consumer.Root, "products");

        string absentRequest = consumer.WriteAdapterRequest("construct", requestedEffect: "committed");
        ProcessResult absent = consumer.RunAdapter("construct", absentRequest);
        Assert.AreEqual(2, absent.ExitCode, absent.Output + absent.Error);
        SpecKitAdapterPackagedWorkspace.AssertAdapterResult(absent, "needs-input", "none");
        Assert.IsFalse(Directory.Exists(products));

        JsonObject review = consumer.Read($"specs/{SpecKitAdapterFixture.FeatureKey}/program-kit/handoff-review.json");
        string reviewRequest = consumer.WriteAdapterRequest("construct", review, "committed");
        ProcessResult reviewAsAuthority = consumer.RunAdapter("construct", reviewRequest);
        Assert.AreEqual(3, reviewAsAuthority.ExitCode, reviewAsAuthority.Output + reviewAsAuthority.Error);
        JsonObject reviewResult = SpecKitAdapterPackagedWorkspace.AssertAdapterResult(reviewAsAuthority, "blocked", "adapter-files-only");
        Assert.AreEqual("program-kit.kernel/PKREQ0002", reviewResult["programKitResult"]!["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.IsFalse(Directory.Exists(products));

        string grantPath = Path.Combine(consumer.Root, grant["logicalPath"]!.GetValue<string>().Replace('/', Path.DirectorySeparatorChar));
        byte[] exactGrant = File.ReadAllBytes(grantPath);
        File.AppendAllText(grantPath, " ");
        string staleRequest = consumer.WriteAdapterRequest("construct", grant, "committed");
        ProcessResult stale = consumer.RunAdapter("construct", staleRequest);
        Assert.AreEqual(3, stale.ExitCode, stale.Output + stale.Error);
        JsonObject staleResult = SpecKitAdapterPackagedWorkspace.AssertAdapterResult(stale, "blocked", "adapter-files-only");
        Assert.AreEqual("program-kit.kernel/PKPOL0001", staleResult["programKitResult"]!["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.IsFalse(Directory.Exists(products));
        File.WriteAllBytes(grantPath, exactGrant);

        string constructRequest = consumer.WriteAdapterRequest("construct", grant, "committed");
        ProcessResult constructed = consumer.RunAdapter("construct", constructRequest);
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(constructed);
        JsonObject constructResult = SpecKitAdapterPackagedWorkspace.AssertAdapterResult(constructed, "succeeded", "program-kit-committed");
        Assert.AreEqual("committed", constructResult["programKitResult"]!["effectState"]!.GetValue<string>());
        Assert.IsTrue(File.Exists(Path.Combine(products, "Reference.Status.Api", "Reference.Status.Api.csproj")));
        Assert.IsTrue(File.Exists(Path.Combine(consumer.Root, ".program-kit", "construction-receipt.json")));

        string beforeEvaluation = TestRepository.DigestTree(consumer.Root);
        string productBeforeEvaluation = TestRepository.DigestTree(products);
        string evaluateRequest = consumer.WriteAdapterRequest("evaluate", requestedEffect: "none");
        ProcessResult evaluated = consumer.RunAdapter("evaluate", evaluateRequest);
        SpecKitAdapterPackagedWorkspace.AssertSucceeded(evaluated);
        JsonObject evaluateResult = SpecKitAdapterPackagedWorkspace.AssertAdapterResult(evaluated, "succeeded", "adapter-files-only");
        Assert.AreEqual("none", evaluateResult["programKitResult"]!["effectState"]!.GetValue<string>());
        Assert.AreNotEqual(beforeEvaluation, TestRepository.DigestTree(consumer.Root), "Only adapter-owned evaluation request/result publication is expected to change the tree.");
        Assert.AreEqual(productBeforeEvaluation, TestRepository.DigestTree(products), "Evaluation must not rewrite the generated product.");
    }
}
