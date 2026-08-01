using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeSupportAdmissionContractTests
{
    [TestMethod]
    [DataRow(CanonicalDependencyStatus.Rejected)]
    [DataRow(CanonicalDependencyStatus.Missing)]
    [DataRow(CanonicalDependencyStatus.Stale)]
    [DataRow(CanonicalDependencyStatus.Mismatched)]
    public void Unaccepted_canonical_dependency_cannot_become_supported(CanonicalDependencyStatus dependency)
    {
        ClaudeSupportDecision decision = ClaudeSupportAdmissionEvaluator.Evaluate(dependency, deterministicGatesPassed: true, providerCompatible: true);
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, decision.SupportClaim);
        Assert.IsFalse(decision.ReleaseEligible);
        Assert.AreEqual("canonical-dependency-not-accepted", decision.Limitation);
    }

    [TestMethod]
    public void Accepted_dependency_still_requires_deterministic_gates()
    {
        ClaudeSupportDecision decision = ClaudeSupportAdmissionEvaluator.Evaluate(CanonicalDependencyStatus.Accepted, deterministicGatesPassed: false, providerCompatible: true);
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, decision.SupportClaim);
        Assert.IsFalse(decision.ReleaseEligible);
    }
}
