using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeAvailabilityAcceptanceTests
{
    [TestMethod]
    public void Availability_is_classified_separately_from_exact_installation()
    {
        AssertClassification(null, ClaudeSkillDiscoveryState.NotEvaluated, "not-evaluated", "program-kit.session.claude-code/PKCLD0006");
        AssertClassification("2.1.220", ClaudeSkillDiscoveryState.ReloadRequired, "reload-required", "program-kit.session.claude-code/PKCLD0003");
        AssertClassification("2.1.220", ClaudeSkillDiscoveryState.Available, "available", null);
        AssertClassification("2.1.219", ClaudeSkillDiscoveryState.Unavailable, "unavailable", "program-kit.session.claude-code/PKCLD0001");
    }

    private static void AssertClassification(string? version, ClaudeSkillDiscoveryState discovery, string expected, string? diagnostic)
    {
        ClaudeObservationClassification result = ClaudeObservationClassifier.Classify(new(
            version, ClaudeAuthenticationState.NotEvaluated, ClaudeWorkspaceTrustState.NotEvaluated,
            discovery, InvocationPreserved: true, ProviderClaimsSuccess: false,
            ProgramKitOutcome: OperationOutcome.Succeeded, IsolatedBoundaryClean: true, LiveEvidenceComplete: version is not null));
        Assert.AreEqual(expected, result.Availability);
        if (diagnostic is null) Assert.AreEqual(0, result.DiagnosticIds.Count);
        else CollectionAssert.Contains(result.DiagnosticIds.ToArray(), diagnostic);
    }
}
