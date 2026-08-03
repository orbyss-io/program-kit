using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Authority;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Providers.DotNet;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class RepositoryAuthorityRecordingContractTests
{
    [TestMethod]
    public void Public_authority_record_atomically_creates_exact_grant_and_revocation_records()
    {
        using AuthorityFixture fixture = AuthorityFixture.Create();
        var execution = fixture.Record();
        Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
        JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
        Assert.AreEqual("succeeded", result["outcome"]!.GetValue<string>());
        Assert.AreEqual("committed", result["effectState"]!.GetValue<string>());
        JsonObject grantReference = result["payload"]!["grant"]!.AsObject();
        JsonObject revocationReference = result["payload"]!["revocation"]!.AsObject();
        Assert.AreEqual(fixture.GrantPath, grantReference["logicalPath"]!.GetValue<string>());
        Assert.AreEqual(fixture.RevocationPath, revocationReference["logicalPath"]!.GetValue<string>());
        JsonObject grant = fixture.Read(fixture.GrantPath);
        ContractAssertions.AssertValid("https://schemas.program-kit.dev/v1/authority-grant.schema.json", grant);
        Assert.AreEqual(fixture.DecisionDigest, grant["provenance"]!["digest"]!.GetValue<string>());
        Assert.AreEqual(2, grant["subjects"]!.AsArray().Count);
        Assert.AreEqual("candidate-only", grant["effects"]![0]!.GetValue<string>());
        Assert.IsTrue(File.Exists(Path.Combine(fixture.Workspace, fixture.RevocationPath.Replace('/', Path.DirectorySeparatorChar))));
        fixture.Demand(grantReference);

        var constructExecution = fixture.Construct(grantReference);
        Assert.AreEqual(3, constructExecution.ExitCode, constructExecution.StandardOutput + constructExecution.StandardError);
        JsonObject constructResult = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, constructExecution.StandardOutput);
        string[] diagnosticIds = constructResult["diagnostics"]!["items"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray();
        CollectionAssert.Contains(diagnosticIds, "program-kit.kernel/PKEXT0002", "The production-recorded grant must pass authority preflight and reach the later declared dependency-mirror boundary.");
        CollectionAssert.DoesNotContain(diagnosticIds, "program-kit.kernel/PKPOL0001");
        Assert.IsFalse(Directory.Exists(Path.Combine(fixture.Workspace, ".program-kit", "candidates")));
    }

    [TestMethod]
    [DataRow("denied")]
    [DataRow("widened-effect")]
    [DataRow("ambiguous-operation")]
    [DataRow("mismatched-subject")]
    [DataRow("invalid-validity")]
    [DataRow("stale-live-state")]
    [DataRow("partial-collision")]
    public void Authority_recording_refuses_inexact_or_partial_decisions_without_authority_files(string scenario)
    {
        using AuthorityFixture fixture = AuthorityFixture.Create();
        fixture.Arrange(scenario);
        var execution = fixture.Record();
        Assert.AreNotEqual(0, execution.ExitCode, scenario);
        JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
        Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
        Assert.IsFalse(File.Exists(Path.Combine(fixture.Workspace, fixture.GrantPath.Replace('/', Path.DirectorySeparatorChar))), scenario);
        if (scenario != "partial-collision")
            Assert.IsFalse(File.Exists(Path.Combine(fixture.Workspace, fixture.RevocationPath.Replace('/', Path.DirectorySeparatorChar))), scenario);
    }

    private sealed class AuthorityFixture : IDisposable
    {
        private AuthorityFixture(string workspace, string requestPath, string decisionPath, string decisionDigest)
        {
            Workspace = workspace;
            RequestPath = requestPath;
            DecisionPath = decisionPath;
            DecisionDigest = decisionDigest;
        }

        public string Workspace { get; }
        public string RequestPath { get; private set; }
        public string DecisionPath { get; }
        public string DecisionDigest { get; private set; }
        public string GrantPath { get; } = ".program-kit/authority/reference-status.grant.json";
        public string RevocationPath { get; } = ".program-kit/authority/reference-status.revocations.json";

        public static AuthorityFixture Create()
        {
            string workspace = SpecKitAdapterFixture.CreateWorkspace();
            AdapterCliInvoker invoker = new();
            JsonObject adapterRequest = SpecKitAdapterFixture.AdapterRequest("prepare");
            JsonObject prepared = new PrepareCommand(invoker).Execute(workspace, adapterRequest);
            Assert.AreEqual("succeeded", prepared["outcome"]!.GetValue<string>());

            string preparationPath = $"specs/{SpecKitAdapterFixture.FeatureKey}/program-kit/generated/results/prepare.json";
            JsonObject preparationReference = Artifact(workspace, preparationPath, "preparation-result", "reference-status-preparation", "application/vnd.program-kit.operation-result+json", "generated-owned");
            JsonObject preparationResult = Read(workspace, preparationPath);
            JsonObject proposal = preparationResult["payload"]!["proposal"]!.AsObject();
            string reviewPath = $"specs/{SpecKitAdapterFixture.FeatureKey}/program-kit/handoff-review.json";
            JsonObject reviewReference = Artifact(workspace, reviewPath, "handoff-review", "reference-status-handoff", "application/json", "consumer-owned");
            JsonObject decision = new()
            {
                ["schema"] = "program-kit.authority-decision-record/v1",
                ["canonicalProfile"] = "program-kit.canonical-json/v1",
                ["proposal"] = preparationReference.DeepClone(),
                ["reviewer"] = "joey-orbyss",
                ["decision"] = "approve",
                ["subjects"] = proposal["subjects"]!.DeepClone(),
                ["operations"] = new JsonArray("construct"),
                ["effects"] = new JsonArray("candidate-only"),
                ["conditions"] = new JsonArray(),
                ["validity"] = new JsonObject { ["notBefore"] = "2026-01-01T00:00:00Z", ["notAfter"] = "2027-01-01T00:00:00Z" },
                ["provenance"] = reviewReference,
                ["recordedAt"] = "2026-08-02T10:10:00Z",
            };
            string decisionPath = ".program-kit/authority/reference-status.decision.json";
            string decisionDigest = Write(workspace, decisionPath, decision);
            JsonObject decisionReference = Artifact(workspace, decisionPath, "authority-decision", "reference-status-decision", "application/json", "consumer-owned");
            Assert.AreEqual(decisionDigest, decisionReference["digest"]!.GetValue<string>());

            JsonObject request = new()
            {
                ["schema"] = "program-kit.authority-record-request/v1",
                ["canonicalProfile"] = "program-kit.canonical-json/v1",
                ["proposal"] = preparationReference,
                ["decision"] = decisionReference,
                ["grantPath"] = ".program-kit/authority/reference-status.grant.json",
                ["revocationPath"] = ".program-kit/authority/reference-status.revocations.json",
            };
            string requestPath = Path.Combine(workspace, "requests", "authority-record.json");
            File.WriteAllBytes(requestPath, CanonicalJson.Encode(request));
            return new AuthorityFixture(workspace, requestPath, decisionPath, decisionDigest);
        }

        public void Arrange(string scenario)
        {
            JsonObject decision = Read(Workspace, DecisionPath);
            switch (scenario)
            {
                case "denied":
                    decision["decision"] = "deny";
                    break;
                case "widened-effect":
                    decision["effects"] = new JsonArray("committed");
                    break;
                case "ambiguous-operation":
                    decision["operations"] = new JsonArray("construct", "construct");
                    break;
                case "mismatched-subject":
                    decision["subjects"]!.AsArray().RemoveAt(1);
                    break;
                case "invalid-validity":
                    decision["validity"]!["notAfter"] = "2025-01-01T00:00:00Z";
                    break;
                case "stale-live-state":
                    MakeProspectiveOutputStale();
                    return;
                case "partial-collision":
                    {
                        string collision = Path.Combine(Workspace, RevocationPath.Replace('/', Path.DirectorySeparatorChar));
                        Directory.CreateDirectory(Path.GetDirectoryName(collision)!);
                        File.WriteAllText(collision, "consumer-owned");
                        return;
                    }
                default:
                    throw new ArgumentOutOfRangeException(nameof(scenario), scenario, "Unknown authority scenario.");
            }

            DecisionDigest = Write(Workspace, DecisionPath, decision);
            JsonObject request = ReadAbsolute(RequestPath);
            Rebind(request["decision"]!.AsObject(), DecisionDigest);
            File.WriteAllBytes(RequestPath, CanonicalJson.Encode(request));
        }

        public (int ExitCode, string StandardOutput, string StandardError) Record() => TestRepository.RunCli(
            "authority", "record", "--workspace", Workspace, "--request", RequestPath, "--format", "json");

        public (int ExitCode, string StandardOutput, string StandardError) Construct(JsonObject grantReference)
        {
            JsonObject construct = ConstructRequest(grantReference);
            string path = Path.Combine(Workspace, "requests", "recorded-authority-construct.json");
            File.WriteAllBytes(path, CanonicalJson.Encode(construct));
            return TestRepository.RunCli("construct", "--workspace", Workspace, "--request", path, "--format", "json");
        }

        public void Demand(JsonObject grantReference)
        {
            ProviderRegistry registry = new(new[] { new DotNetProvider() });
            IntakePipeline intake = new(registry);
            ResolutionEngine resolution = new(registry);
            FactoryInput input = intake.AdmitAndMap(Workspace, ConstructRequest(grantReference));
            _ = new RepositoryAuthorityProvider().Demand(Workspace, input, resolution.Resolve(input).Lock);
        }

        public JsonObject Read(string logicalPath) => Read(Workspace, logicalPath);

        public void Dispose() => TestRepository.DeleteWorkspace(Workspace);

        private void MakeProspectiveOutputStale()
        {
            JsonObject request = ReadAbsolute(RequestPath);
            string preparationPath = request["proposal"]!["logicalPath"]!.GetValue<string>();
            JsonObject proposal = Read(Workspace, preparationPath)["payload"]!["proposal"]!.AsObject();
            string logicalPath = FindLogicalPaths(proposal["explanation"]!).First(path => !File.Exists(Path.Combine(Workspace, path.Replace('/', Path.DirectorySeparatorChar))));
            string path = Path.Combine(Workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, "stale");
        }

        private JsonObject ConstructRequest(JsonObject grantReference)
        {
            JsonObject proposal = Read(Workspace, $"specs/{SpecKitAdapterFixture.FeatureKey}/program-kit/generated/results/prepare.json")["payload"]!["proposal"]!.AsObject();
            JsonObject construct = (JsonObject)proposal["ungrantedProjection"]!.DeepClone();
            construct["authorityGrant"] = grantReference.DeepClone();
            return construct;
        }

        private static IEnumerable<string> FindLogicalPaths(JsonNode node)
        {
            if (node is JsonObject obj)
            {
                if (obj["logicalPath"]?.GetValue<string>() is { Length: > 0 } path) yield return path;
                foreach (JsonNode? child in obj.Select(static item => item.Value).Where(static item => item is not null))
                    foreach (string nested in FindLogicalPaths(child!)) yield return nested;
            }
            else if (node is JsonArray array)
            {
                foreach (JsonNode? child in array.Where(static item => item is not null))
                    foreach (string nested in FindLogicalPaths(child!)) yield return nested;
            }
        }

        private static JsonObject Artifact(string workspace, string logicalPath, string kind, string name, string mediaType, string ownership)
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            string digest = Digests.Sha256(File.ReadAllBytes(path));
            return new JsonObject
            {
                ["identity"] = new JsonObject { ["authority"] = "consumer.reference", ["kind"] = kind, ["name"] = name, ["revision"] = "1.0.0", ["digest"] = digest },
                ["mediaType"] = mediaType,
                ["logicalPath"] = logicalPath,
                ["digest"] = digest,
                ["ownership"] = ownership,
            };
        }

        private static void Rebind(JsonObject artifact, string digest)
        {
            artifact["digest"] = digest;
            artifact["identity"]!["digest"] = digest;
        }

        private static string Write(string workspace, string logicalPath, JsonObject document)
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            byte[] bytes = CanonicalJson.Encode(document);
            File.WriteAllBytes(path, bytes);
            return Digests.Sha256(bytes);
        }

        private static JsonObject Read(string workspace, string logicalPath) =>
            CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar)))).AsObject();

        private static JsonObject ReadAbsolute(string path) => CanonicalJson.Parse(File.ReadAllBytes(path)).AsObject();
    }

    private sealed class AdapterCliInvoker : IPublicProgramKitInvoker
    {
        public JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath)
        {
            string request = Path.Combine(workspaceRoot, requestLogicalPath.Replace('/', Path.DirectorySeparatorChar));
            var execution = TestRepository.RunCli(command, "--workspace", workspaceRoot, "--request", request, "--format", "json");
            Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            return CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(execution.StandardOutput)).AsObject();
        }
    }
}
