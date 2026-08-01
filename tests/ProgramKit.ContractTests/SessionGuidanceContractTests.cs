using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Definitions;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionGuidanceContractTests
{
    [TestMethod]
    public void Canonical_guidance_preserves_human_authority_and_semantic_honesty()
    {
        string guidance = string.Join('\n', CanonicalSessionGuidance.WorkflowSteps);
        StringAssert.Contains(guidance, "known, incomplete-known, or unknown");
        StringAssert.Contains(guidance, "provider selection as explicit");
        StringAssert.Contains(guidance, "request-bound authority");
        StringAssert.Contains(guidance, "Leave unknown custom implementation intent explicit");
        Assert.AreEqual(9, CanonicalSessionGuidance.WorkflowSteps.Count);
        Assert.IsFalse(guidance.Contains("authentication", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(guidance.Contains("business domain", StringComparison.OrdinalIgnoreCase));
    }
}
