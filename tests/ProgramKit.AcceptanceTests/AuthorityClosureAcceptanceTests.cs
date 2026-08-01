using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class AuthorityClosureAcceptanceTests
{
    [TestMethod]
    [DataRow("mutated-grant")]
    [DataRow("wrong-request-binding")]
    [DataRow("wrong-effect")]
    [DataRow("expired")]
    [DataRow("wrong-closure")]
    [DataRow("wrong-live-state")]
    [DataRow("missing-review")]
    [DataRow("rejected-review")]
    [DataRow("revoked")]
    public void Construction_fails_closed_for_every_inexact_authority_dimension(string scenario)
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            ArrangeScenario(workspace, scenario);
            var execution = TestRepository.RunCli(
                "construct",
                "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"),
                "--format", "json");
            Assert.AreEqual(3, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            Assert.AreEqual("blocked", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
            Assert.AreEqual("request-approval", result["primaryDisposition"]!.GetValue<string>());
            string[] ids = result["diagnostics"]!["items"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray();
            CollectionAssert.Contains(ids, "program-kit.kernel/PKPOL0001");
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Missing_grant_returns_one_non_authorizing_continuation_and_no_effect()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            JsonObject request = Read(workspace, "requests/construct.json");
            request.Remove("authorityGrant");
            Write(workspace, "requests/construct.json", request);
            var execution = TestRepository.RunCli(
                "construct",
                "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"),
                "--format", "json");
            Assert.AreEqual(2, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            Assert.AreEqual("needs-input", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
            Assert.IsTrue(result["continuation"]!["missingInputs"]!.AsArray().Any(static item => item!["identity"]!.GetValue<string>() == "authoritygrant"));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void ArrangeScenario(string workspace, string scenario)
    {
        JsonObject grant = Read(workspace, "authority/construct-grant.json");
        switch (scenario)
        {
            case "mutated-grant":
                File.AppendAllText(Path.Combine(workspace, "authority", "construct-grant.json"), " ");
                return;
            case "wrong-request-binding":
                grant["requestBinding"] = Digest("wrong-request");
                break;
            case "wrong-effect":
                grant["effects"] = new JsonArray("candidate-only");
                break;
            case "expired":
                grant["validity"]!["notAfter"] = "2026-07-31T23:59:59Z";
                break;
            case "wrong-closure":
                Condition(grant, "operation-closure")["value"] = Digest("wrong-closure");
                break;
            case "wrong-live-state":
                Condition(grant, "expected-live-state")["value"] = Digest("wrong-live-state");
                break;
            case "missing-review":
                File.Delete(Path.Combine(workspace, "authority", "review.json"));
                return;
            case "rejected-review":
                {
                    JsonObject review = Read(workspace, "authority/review.json");
                    review["decision"] = "rejected";
                    string reviewDigest = Write(workspace, "authority/review.json", review);
                    RebindArtifact((JsonObject)grant["provenance"]!, reviewDigest);
                    Condition(grant, "review-digest")["value"] = reviewDigest;
                    break;
                }
            case "revoked":
                {
                    string handle = Condition(grant, "revocation-handle")["value"]!.GetValue<string>();
                    JsonObject revocations = Read(workspace, "authority/revocations.json");
                    revocations["revokedGrantDigests"] = new JsonArray(handle);
                    string revocationDigest = Write(workspace, "authority/revocations.json", revocations);
                    RebindArtifact((JsonObject)grant["revocationReference"]!, revocationDigest);
                    break;
                }
            default:
                throw new ArgumentOutOfRangeException(nameof(scenario), scenario, "Unknown authority scenario.");
        }

        RebindGrant(workspace, grant);
    }

    private static JsonObject Condition(JsonObject grant, string kind) => grant["conditions"]!.AsArray()
        .Select(static item => item!.AsObject())
        .Single(item => string.Equals(item["kind"]!.GetValue<string>(), kind, StringComparison.Ordinal))["value"]!.AsObject();

    private static void RebindGrant(string workspace, JsonObject grant)
    {
        JsonObject identity = grant["identity"]!.AsObject();
        identity["digest"] = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
        identity["digest"] = IntakePipeline.DocumentIdentityDigest(grant);
        string grantDigest = Write(workspace, "authority/construct-grant.json", grant);
        JsonObject request = Read(workspace, "requests/construct.json");
        JsonObject authority = request["authorityGrant"]!.AsObject();
        authority["identity"] = identity.DeepClone();
        authority["digest"] = grantDigest;
        Write(workspace, "requests/construct.json", request);
    }

    private static void RebindArtifact(JsonObject artifact, string digest)
    {
        artifact["digest"] = digest;
        artifact["identity"]!["digest"] = digest;
    }

    private static JsonObject Read(string workspace, string logicalPath) =>
        CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar)))).AsObject();

    private static string Write(string workspace, string logicalPath, JsonObject document)
    {
        byte[] bytes = CanonicalJson.Encode(document);
        File.WriteAllBytes(Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar)), bytes);
        return Digests.Sha256(bytes);
    }

    private static string Digest(string value) => Digests.Sha256(Encoding.UTF8.GetBytes(value));
}
