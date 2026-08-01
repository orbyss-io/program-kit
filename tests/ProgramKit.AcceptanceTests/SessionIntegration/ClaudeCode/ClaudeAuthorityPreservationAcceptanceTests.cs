using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeAuthorityPreservationAcceptanceTests
{
    [TestMethod]
    public void Process_permission_and_complete_adapter_mechanics_cannot_upgrade_rejected_authority()
    {
        ClaudeSupportDecision decision = ClaudeSupportAdmissionEvaluator.Evaluate(
            CanonicalDependencyStatus.Rejected, deterministicGatesPassed: true, providerCompatible: true);
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, decision.SupportClaim);
        Assert.IsFalse(decision.ReleaseEligible);
    }
}
