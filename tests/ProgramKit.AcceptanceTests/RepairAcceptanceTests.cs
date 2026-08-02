using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class RepairAcceptanceTests
{
    [TestMethod]
    public void Generated_drift_requires_fresh_authority_and_repairs_without_changing_consumer_source()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            var initial = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"), "--format", "json");
            Assert.AreEqual(0, initial.ExitCode, initial.StandardOutput + initial.StandardError);

            string source = Path.Combine(workspace, "implementation", "StatusFeature.cs");
            string sourceDigest = Digests.Sha256(File.ReadAllBytes(source));
            string drifted = Path.Combine(workspace, "products", "Reference.Status.Api", "appsettings.json");
            File.AppendAllText(drifted, " ");

            var evaluated = TestRepository.RunCli(
                "evaluate", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "evaluate.json"), "--format", "json");
            Assert.AreEqual(3, evaluated.ExitCode, evaluated.StandardOutput + evaluated.StandardError);
            JsonObject evaluation = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, evaluated.StandardOutput);
            JsonObject repair = evaluation["diagnostics"]!["items"]!.AsArray()
                .SelectMany(static item => item!["remediations"]!.AsArray())
                .Select(static item => item!["request"]!["document"]!.AsObject())
                .First();
            ContractAssertions.AssertValid(ContractAssertions.FactoryRequest, repair);

            string pendingPath = Path.Combine(workspace, "requests", "repair-pending.json");
            File.WriteAllBytes(pendingPath, CanonicalJson.Encode(repair));
            var pending = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", pendingPath, "--format", "json");
            Assert.AreEqual(3, pending.ExitCode, pending.StandardOutput + pending.StandardError);
            JsonObject pendingResult = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, pending.StandardOutput);
            Assert.AreEqual("request-approval", pendingResult["primaryDisposition"]!.GetValue<string>());

            MaterializeFreshRepairAuthority(workspace, repair);
            string repairPath = Path.Combine(workspace, "requests", "repair.json");
            File.WriteAllBytes(repairPath, CanonicalJson.Encode(repair));
            var repaired = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", repairPath, "--format", "json");
            Assert.AreEqual(0, repaired.ExitCode, repaired.StandardOutput + repaired.StandardError);
            JsonObject repairResult = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, repaired.StandardOutput);
            Assert.AreEqual("committed", repairResult["effectState"]!.GetValue<string>());
            Assert.AreEqual(sourceDigest, Digests.Sha256(File.ReadAllBytes(source)), "Consumer-owned implementation changed during repair.");
            Assert.IsTrue(Directory.EnumerateFiles(Path.Combine(workspace, ".program-kit", "history"), "construction-receipt-*.json").Any());

            var exact = TestRepository.RunCli(
                "evaluate", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "evaluate.json"), "--format", "json");
            Assert.AreEqual(0, exact.ExitCode, exact.StandardOutput + exact.StandardError);
            ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, exact.StandardOutput);
            ContractAssertions.ReadAndValidate(ContractAssertions.ConstructionReceipt, Path.Combine(workspace, ".program-kit", "construction-receipt.json"));
            ContractAssertions.ReadAndValidate(ContractAssertions.WorkspaceSnapshot, Path.Combine(workspace, ".program-kit", "workspace.snapshot.json"));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    internal static void MaterializeFreshRepairAuthority(string workspace, JsonObject repair)
    {
        JsonObject bindingDocument = IntakePipeline.NormalizeRequest(repair);
        bindingDocument.Remove("authorityGrant");
        string requestBinding = CanonicalJson.Digest(bindingDocument);
        string closure = repair["expectedState"]!["closureDigest"]!.GetValue<string>();
        string liveState = repair["expectedState"]!["liveStateDigest"]!.GetValue<string>();
        string revocationHandle = Digest($"repair:{requestBinding}:revocation-handle/v1");

        JsonObject review = new()
        {
            ["schema"] = "program-kit.human-review/v1",
            ["decision"] = "approved",
            ["reviewerIdentity"] = "fixture-reviewer:repair-v1",
            ["requestBinding"] = requestBinding,
            ["operation"] = "construct",
            ["effect"] = "committed",
            ["evaluationInstant"] = repair["evaluationContext"]!["instant"]!.GetValue<string>(),
        };
        JsonObject reviewArtifact = WriteArtifact(workspace, "authority/repair-review.json", review, "human-review", "reference-status-repair");

        JsonObject revocations = new()
        {
            ["schema"] = "program-kit.authority-revocations/v1",
            ["revokedGrantDigests"] = new JsonArray(),
        };
        JsonObject revocationArtifact = WriteArtifact(workspace, "authority/repair-revocations.json", revocations, "revocation-state", "reference-status-repair");

        JsonObject sourceGrant = CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(workspace, "authority", "construct-grant.json"))).AsObject();
        JsonObject grant = new()
        {
            ["schema"] = "program-kit.authority-grant/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["identity"] = Identity("authority-grant", "reference-status-repair", "sha256:0000000000000000000000000000000000000000000000000000000000000000"),
            ["issuerAssertion"] = sourceGrant["issuerAssertion"]!.DeepClone(),
            ["subjects"] = new JsonArray(
                new JsonObject { ["kind"] = "workspace", ["identity"] = repair["workspaceIdentity"]!.DeepClone() },
                new JsonObject { ["kind"] = "root-bundle", ["identity"] = repair["rootBundle"]!["identity"]!.DeepClone() }),
            ["operations"] = new JsonArray("construct"),
            ["effects"] = new JsonArray("committed"),
            ["requestBinding"] = requestBinding,
            ["conditions"] = new JsonArray(
                Condition("operation-closure", closure),
                Condition("review-digest", reviewArtifact["digest"]!.GetValue<string>()),
                Condition("expected-live-state", liveState),
                Condition("revocation-handle", revocationHandle)),
            ["validity"] = sourceGrant["validity"]!.DeepClone(),
            ["revocationReference"] = revocationArtifact,
            ["provenance"] = reviewArtifact,
        };
        grant["identity"]!["digest"] = IntakePipeline.DocumentIdentityDigest(grant);
        byte[] grantBytes = CanonicalJson.Encode(grant);
        string grantDigest = Digests.Sha256(grantBytes);
        File.WriteAllBytes(Path.Combine(workspace, "authority", "repair-grant.json"), grantBytes);
        repair["authorityGrant"] = new JsonObject
        {
            ["identity"] = grant["identity"]!.DeepClone(),
            ["mediaType"] = "application/vnd.program-kit.authority-grant+json",
            ["logicalPath"] = "authority/repair-grant.json",
            ["digest"] = grantDigest,
            ["ownership"] = "consumer-owned",
        };
    }

    private static JsonObject WriteArtifact(string workspace, string logicalPath, JsonObject document, string kind, string name)
    {
        byte[] bytes = CanonicalJson.Encode(document);
        string digest = Digests.Sha256(bytes);
        File.WriteAllBytes(Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar)), bytes);
        return new JsonObject
        {
            ["identity"] = Identity(kind, name, digest),
            ["mediaType"] = "application/json",
            ["logicalPath"] = logicalPath,
            ["digest"] = digest,
            ["ownership"] = "consumer-owned",
        };
    }

    private static JsonObject Identity(string kind, string name, string digest) => new()
    {
        ["authority"] = "consumer.reference",
        ["kind"] = kind,
        ["name"] = name,
        ["revision"] = "1.0.0",
        ["digest"] = digest,
    };

    private static JsonObject Condition(string kind, string digest) => new()
    {
        ["kind"] = kind,
        ["value"] = new JsonObject { ["classification"] = "public", ["valueKind"] = "digest", ["value"] = digest },
    };

    private static string Digest(string value) => Digests.Sha256(Encoding.UTF8.GetBytes(value));
}
