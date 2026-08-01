using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeConformanceNegativeAcceptanceTests
{
    [TestMethod]
    public void Semantic_loss_is_an_exact_authority_failure()
    {
        SessionProviderConformanceReport report = Compare(Observation("provider-claude-code") with { AuthorityPreserved = false });
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "authority");
    }

    [TestMethod]
    public void Altered_operation_or_argument_boundary_is_an_exact_failure()
    {
        SessionProviderConformanceReport report = Compare(Observation("provider-claude-code") with { Command = PublicCommand.Evaluate, WorkingScopePreserved = false });
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "operation-identity");
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "working-scope");
    }

    [TestMethod]
    public void Contaminated_output_is_an_exact_disclosure_failure()
    {
        SessionProviderConformanceReport report = Compare(Observation("provider-claude-code") with { DisclosurePreserved = false });
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "disclosure");
    }

    [TestMethod]
    public void Contradictory_provider_success_is_classified_without_overriding_Program_Kit()
    {
        ClaudeObservationClassification classification = Classify(
            ClaudeProviderIdentities.ProviderVersion, true, OperationOutcome.Blocked, true, true);
        CollectionAssert.Contains(classification.DiagnosticIds.ToArray(), ClaudeDiagnosticCatalog.Id(7));
        Assert.AreEqual("blocked", classification.SafeFields["programKitOutcome"]);
    }

    [TestMethod]
    public void Unavailable_provider_version_is_incompatible()
    {
        ClaudeObservationClassification classification = Classify("2.0.0", false, OperationOutcome.Blocked, true, false);
        Assert.AreEqual("unavailable", classification.Availability);
        CollectionAssert.Contains(classification.DiagnosticIds.ToArray(), ClaudeDiagnosticCatalog.Id(1));
    }

    [TestMethod]
    public void Exact_adapter_mechanics_do_not_override_not_evaluated_support()
    {
        ClaudeSessionProviderAdapter adapter = new();
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, adapter.Manifest.SupportClaim);
        SessionProviderConformanceReport report = new SessionProviderConformanceEvaluator().Evaluate(adapter, ClaudeTestContext.Create(adapter.Manifest));
        Assert.IsFalse(report.Conforms);
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "support");

        ClaudeObservationClassification classification = Classify(null, false, OperationOutcome.Blocked, true, false);
        Assert.AreEqual("not-evaluated", classification.Availability);
        CollectionAssert.Contains(classification.DiagnosticIds.ToArray(), ClaudeDiagnosticCatalog.Id(6));
    }

    private static SessionProviderConformanceReport Compare(SessionSemanticObservation claude)
    {
        SessionProviderConformanceReport report = ClaudeConformanceProfiles.Compare(new[] { Observation("direct-cli"), claude });
        Assert.IsFalse(report.Conforms);
        return report;
    }

    private static ClaudeObservationClassification Classify(
        string? version,
        bool providerClaimsSuccess,
        OperationOutcome programKitOutcome,
        bool invocationPreserved,
        bool liveEvidenceComplete) =>
        ClaudeObservationClassifier.Classify(new(
            version,
            ClaudeAuthenticationState.NotEvaluated,
            ClaudeWorkspaceTrustState.NotEvaluated,
            ClaudeSkillDiscoveryState.NotEvaluated,
            invocationPreserved,
            providerClaimsSuccess,
            programKitOutcome,
            true,
            liveEvidenceComplete));

    private static SessionSemanticObservation Observation(string channel) => new(
        channel, PublicCommand.SessionExplain, OperationOutcome.Succeeded, EffectState.None,
        PrimaryDisposition.Complete, "program-kit.operation-result/v1", true, true, true, true);
}
