using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionProviderConformanceContractTests
{
    [TestMethod]
    public void Profile_covers_operations_scope_ownership_results_authority_disclosure_and_discovery()
    {
        SessionProviderConformanceProfile profile = SessionProviderConformanceProfiles.RepositoryWorkspaceV1;
        CollectionAssert.AreEqual(new[] { "explain", "construct", "evaluate", "session-explain", "session-install", "session-verify", "session-remove" }, profile.RequiredOperations.ToArray());
        CollectionAssert.AreEqual(new[] { "workspace" }, profile.RequiredScopes.ToArray());
        Assert.AreEqual("program-kit.operation-result/v1", profile.ResultSchema);
        Assert.IsTrue(profile.RequireGeneratedOwnership);
        Assert.IsTrue(profile.RequireCleanStructuredResult);
        Assert.IsTrue(profile.RequireAuthorityPreservation);
        Assert.IsTrue(profile.RequireDisclosurePreservation);
        Assert.IsTrue(profile.RequireFreshSessionClassification);
    }

    [TestMethod]
    public void Neutral_harness_conforms_and_reports_normalized_evidence()
    {
        SessionProviderConformanceReport report = new SessionProviderConformanceEvaluator().Evaluate(new NeutralSessionProviderHarness(), SessionIntegrationFixture.ProjectionContext());
        Assert.IsTrue(report.Conforms, string.Join(';', report.Failures.Select(static item => item.Code)));
        StringAssert.StartsWith(report.NormalizedInputDigest, "sha256:");
        StringAssert.StartsWith(report.ObservationDigest, "sha256:");
        Assert.AreEqual(0, report.Failures.Count);
    }
}
