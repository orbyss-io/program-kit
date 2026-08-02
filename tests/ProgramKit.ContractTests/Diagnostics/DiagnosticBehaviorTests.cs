using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Providers.DotNet;
using Orbyss.ProgramKit.Providers.DotNet.Composition.HttpEndpoints;
using Orbyss.ProgramKit.Providers.DotNet.Diagnostics;
using Orbyss.ProgramKit.Providers.DotNet.Evaluation;

namespace Orbyss.ProgramKit.Tests.Diagnostics;

[TestClass]
public sealed class DiagnosticBehaviorTests
{
    [TestMethod]
    public void Valid_explain_reaches_the_public_kernel_result_without_fallback()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            OperationExecutionTracker.Start(PublicCommand.Explain);
            OperationResult result = new ProgramKitKernel(new[] { new DotNetProvider() }).Explain(
                workspace,
                Path.Combine(workspace, "requests", "explain.json"));

            Assert.AreEqual(OperationOutcome.Succeeded, result.Outcome);
            Assert.AreEqual(PrimaryDisposition.Complete, result.PrimaryDisposition);
            Assert.IsTrue(OperationResultProjector.ToCanonicalBytes(result).Length > 0);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Every_catalog_entry_projects_authoritative_typed_guidance()
    {
        Assert.AreEqual(26, DiagnosticCatalog.Entries.Count);
        foreach (DiagnosticDefinition definition in DiagnosticCatalog.Entries.Values)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                definition.Id,
                OperationPhase.Validation,
                DisclosureFilter.PublicText("catalog-trigger"),
                DisclosureFilter.PublicText("The production invariant was exercised."),
                DisclosureFilter.PublicText("The operation remains bounded by the reported disposition."));

            Assert.AreEqual(definition.Disposition, diagnostic.Disposition, definition.Id);
            Assert.IsFalse(string.IsNullOrWhiteSpace(diagnostic.Expected.Value), definition.Id);
            Assert.IsFalse(string.IsNullOrWhiteSpace(diagnostic.Observed.Value), definition.Id);
            Assert.IsTrue(diagnostic.Evidence.Count > 0, definition.Id);
            Assert.IsTrue(diagnostic.Remediations.Count > 0, definition.Id);
            Assert.IsTrue(diagnostic.Remediations.All(static remediation =>
                remediation.Targets.Count > 0
                && remediation.Preconditions.Count > 0
                && remediation.Postconditions.Count > 0
                && (remediation.RequestDocument is not null
                    || remediation.RequestArtifact is not null
                    || remediation.RequestArguments is { Count: > 0 })), definition.Id);

            OperationResult result = OperationResultFactory.Failure(
                PublicCommand.Construct,
                OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                definition.Disposition,
                new[] { diagnostic });
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, OperationResultProjector.ToJson(result));
        }
    }

    [TestMethod]
    public void Dotnet_composition_invariants_trigger_their_exact_public_diagnostics()
    {
        AssertProviderDiagnostic(
            ExpectedDiagnostic("MissingAssembler"),
            PrimaryDisposition.ProvideInput,
            () => EndpointAssembler.Resolve(new[]
            {
                new EndpointContribution("missing", "GET", "/status", "StatusFeature", null, null),
            }));

        AssertProviderDiagnostic(
            ExpectedDiagnostic("DuplicateRoute"),
            PrimaryDisposition.Revise,
            () => EndpointAssembler.Resolve(new[]
            {
                new EndpointContribution("one", "GET", "/status", "StatusFeature", null),
                new EndpointContribution("two", "get", "status/", "OtherFeature", null),
            }));

        AssertProviderDiagnostic(
            ExpectedDiagnostic("AmbiguousOrder"),
            PrimaryDisposition.ProvideInput,
            () => EndpointAssembler.Resolve(new[]
            {
                new EndpointContribution("one", "GET", "/first", "FirstFeature", 1),
                new EndpointContribution("two", "GET", "/second", "SecondFeature", null),
            }));
    }

    [TestMethod]
    public void Policy_provider_and_runtime_boundaries_trigger_exact_public_diagnostics()
    {
        ProgramKitDiagnosticException waiver = Assert.ThrowsExactly<ProgramKitDiagnosticException>(() =>
            WaiverPolicy.EnsureFirstSliceContainsNoWaivers(new JsonArray(new JsonObject { ["rule"] = "not-waivable" })));
        Assert.AreEqual(DiagnosticIds.InvalidWaiver, waiver.DiagnosticId);
        Assert.AreEqual(PrimaryDisposition.Stop, waiver.Disposition);

        ProgramKitDiagnosticException provider = Assert.ThrowsExactly<ProgramKitDiagnosticException>(() =>
            ProviderInvocation.Invoke(
                static () => Task.FromException<int>(new InvalidOperationException("provider secret must not escape")),
                OperationPhase.Construction));
        Assert.AreEqual(DiagnosticIds.ExternalFailure, provider.DiagnosticId);
        Assert.AreEqual(PrimaryDisposition.Retry, provider.Disposition);
        Assert.IsFalse(provider.Message.Contains("secret", StringComparison.OrdinalIgnoreCase));

        AssertProviderDiagnostic(
            DiagnosticIds.ForbiddenRuntimeDependency,
            PrimaryDisposition.Stop,
            () => RuntimeDependencyValidator.EnsureAllowed(
                new[] { "ProgramKit.Kernel/1.0.0" },
                new[] { "Consumer.Application" }));
    }

    [TestMethod]
    public void Equal_construction_identity_with_different_canonical_bytes_fails_closed_without_mutation()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            string state = Path.Combine(workspace, ".program-kit");
            Directory.CreateDirectory(state);
            string constructionIdentity = $"sha256:{new string('1', 64)}";
            string admittedDigest = $"sha256:{new string('2', 64)}";
            string proposedDigest = $"sha256:{new string('3', 64)}";
            File.WriteAllBytes(
                Path.Combine(state, "construction-receipt.json"),
                CanonicalJson.Encode(new JsonObject { ["constructionIdentity"] = constructionIdentity }));
            File.WriteAllBytes(
                Path.Combine(state, "artifact-manifest.json"),
                CanonicalJson.Encode(new JsonObject
                {
                    ["artifacts"] = new JsonArray(new JsonObject
                    {
                        ["logicalPath"] = "products/value.txt",
                        ["digest"] = admittedDigest,
                        ["claimClass"] = "canonical-byte",
                    }),
                }));
            CandidateArtifactSet candidate = new(
                constructionIdentity,
                Path.Combine(state, "candidate"),
                new[]
                {
                    new ArtifactManifestEntry(
                        "products/value.txt",
                        ArtifactOwnership.GeneratedOwned,
                        "text/plain",
                        proposedDigest,
                        "test-provider",
                        ClaimClass.CanonicalByte),
                },
                $"sha256:{new string('4', 64)}",
                CandidateState.Sealed);
            string before = TestRepository.DigestTree(workspace);

            ProgramKitDiagnosticException mismatch = Assert.ThrowsExactly<ProgramKitDiagnosticException>(() =>
                DeterminismGuard.EnsureCompatibleWithAdmittedCanonicalBytes(workspace, candidate));

            Assert.AreEqual(DiagnosticIds.DeterminismMismatch, mismatch.DiagnosticId);
            Assert.AreEqual(PrimaryDisposition.Stop, mismatch.Disposition);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Missing_inputs_are_grouped_into_one_stateless_continuation_with_typed_guidance()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            string request = Path.Combine(workspace, "requests", "diagnostic-missing.json");
            File.WriteAllText(request, "{\"schema\":\"program-kit.factory-request/v1\",\"canonicalProfile\":\"program-kit.canonical-json/v1\",\"operation\":\"explain\"}");
            var execution = TestRepository.RunCli(
                "explain", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(2, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            Assert.IsTrue(result["continuation"]!["missingInputs"]!.AsArray().Count >= 5);
            JsonObject diagnostic = result["diagnostics"]!["items"]![0]!.AsObject();
            Assert.AreEqual("provide-input", diagnostic["disposition"]!.GetValue<string>());
            Assert.IsTrue(diagnostic["remediations"]!.AsArray().Count > 0);
            Assert.IsNotNull(diagnostic["expected"]);
            Assert.IsNotNull(diagnostic["observed"]);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public async Task Remaining_public_ids_are_asserted_at_their_real_production_boundaries()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            var missing = TestRepository.RunCli("construct", "--format", "json");
            AssertResultDiagnostic(missing.StandardOutput, DiagnosticIds.MissingInput);

            var conflict = TestRepository.RunCli(
                "explain", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"),
                "--format", "json");
            AssertResultDiagnostic(conflict.StandardOutput, DiagnosticIds.ConflictingInput);

            DotNetProvider provider = new();
            ProviderIntakeResult intake = await provider.MapAsync(new ProviderIntakeContext(
                workspace,
                new JsonObject { ["semanticRecords"] = new JsonArray() },
                $"sha256:{new string('1', 64)}",
                CancellationToken.None));
            CollectionAssert.Contains(intake.Diagnostics.ToArray(), DiagnosticIds.IncompleteMeaning);

            ProviderEvaluationResult evaluation = await provider.EvaluateAsync(new ProviderEvaluationContext(
                workspace,
                new JsonObject(),
                $"sha256:{new string('2', 64)}",
                null,
                CancellationToken.None));
            CollectionAssert.Contains(evaluation.Diagnostics.ToArray(), DiagnosticIds.GateFailed);

            AssertProviderDiagnostic(
                DiagnosticIds.CShellsConformance,
                PrimaryDisposition.Stop,
                () => ProviderArtifactValidator.ReadRuntimeLibraries(Path.Combine(workspace, "missing.deps.json")));
            AssertProviderDiagnostic(
                DiagnosticIds.PackageMismatch,
                PrimaryDisposition.Stop,
                () => ProviderArtifactValidator.RequirePackage(Path.Combine(workspace, "missing.nupkg")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void AssertResultDiagnostic(string json, string id)
    {
        JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, json);
        string[] ids = result["diagnostics"]!["items"]!.AsArray()
            .Select(static item => item!["id"]!.GetValue<string>())
            .ToArray();
        CollectionAssert.Contains(ids, id);
    }
    private static void AssertProviderDiagnostic(string id, PrimaryDisposition disposition, Action action)
    {
        ProviderDiagnosticException exception = Assert.ThrowsExactly<ProviderDiagnosticException>(action);
        Assert.AreEqual(id, exception.DiagnosticId);
        Assert.AreEqual(disposition, exception.Disposition);
    }
    private static string ExpectedDiagnostic(string fixtureName) =>
        JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture($"Invalid/{fixtureName}/fixture.json")))!
            ["expectedDiagnostic"]!
            .GetValue<string>();

}
