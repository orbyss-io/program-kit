using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeConformanceNegativeAcceptanceTests
{
    [TestMethod]
    public void Altered_result_meaning_is_an_exact_conformance_failure()
    {
        SessionSemanticObservation[] observations =
        {
            Observation("direct-cli", OperationOutcome.Succeeded),
            Observation("claude-code", OperationOutcome.Blocked),
        };
        SessionProviderConformanceReport report = ClaudeConformanceProfiles.Compare(observations);
        Assert.IsFalse(report.Conforms);
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "outcome");
    }

    [TestMethod]
    public void Exact_adapter_mechanics_do_not_override_not_evaluated_support()
    {
        ClaudeSessionProviderAdapter adapter = new();
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, adapter.Manifest.SupportClaim);
        SessionProviderConformanceReport report = new SessionProviderConformanceEvaluator().Evaluate(adapter, ClaudeTestContext.Create(adapter.Manifest));
        Assert.IsFalse(report.Conforms);
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "support");
    }

    private static SessionSemanticObservation Observation(string channel, OperationOutcome outcome) => new(
        channel, PublicCommand.Construct, outcome, EffectState.Committed,
        PrimaryDisposition.Complete, "program-kit.operation-result/v1", true, true, true, true);
}
