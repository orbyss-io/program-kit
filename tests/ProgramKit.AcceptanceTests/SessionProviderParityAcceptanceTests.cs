using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionProviderParityAcceptanceTests
{
    [TestMethod]
    public void Direct_neutral_and_reference_channels_preserve_normalized_result_meaning()
    {
        SessionSemanticObservation[] observations =
        {
            Observation("direct-cli"),
            Observation("neutral-harness"),
            Observation("reference-provider"),
        };
        SessionProviderConformanceReport report = new SessionProviderConformanceEvaluator().CompareSemanticObservations(observations);
        Assert.IsTrue(report.Conforms, string.Join(';', report.Failures.Select(static item => item.Code)));
        StringAssert.StartsWith(report.ObservationDigest, "sha256:");
    }

    [TestMethod]
    public void Semantic_weakening_is_reported_as_exact_incompatibility()
    {
        SessionSemanticObservation direct = Observation("direct-cli");
        SessionSemanticObservation weakened = Observation("reference-provider") with { EffectState = EffectState.Committed, AuthorityPreserved = false };
        SessionProviderConformanceReport report = new SessionProviderConformanceEvaluator().CompareSemanticObservations(new[] { direct, weakened });
        Assert.IsFalse(report.Conforms);
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "effect");
        CollectionAssert.Contains(report.Failures.Select(static item => item.Code).ToArray(), "authority");
    }

    private static SessionSemanticObservation Observation(string channel) => new(
        channel,
        PublicCommand.SessionExplain,
        OperationOutcome.Succeeded,
        EffectState.None,
        PrimaryDisposition.Complete,
        "program-kit.operation-result/v2",
        true,
        true,
        true,
        true);
}
