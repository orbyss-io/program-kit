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
        StringAssert.Contains(guidance, "continuation.missingInputs");
        StringAssert.Contains(guidance, "provider selection as explicit");
        StringAssert.Contains(guidance, "conversation and human confirmation as direction, never as an authority grant");
        StringAssert.Contains(guidance, "do not author, widen, refresh, replace, or reuse a grant");
        StringAssert.Contains(guidance, "read its existing authorityGrant.logicalPath, name that exact request-bound grant before asking");
        StringAssert.Contains(guidance, "never require the human to discover or guess the grant");
        StringAssert.Contains(guidance, "Invoke construct only for the same reviewed canonical request");
        StringAssert.Contains(guidance, "Invoke evaluate only after construct reports that successful committed result");
        StringAssert.Contains(guidance, "obey primaryDisposition");
        StringAssert.Contains(guidance, "requestDocument, requestArtifact, or requestArguments");
        StringAssert.Contains(guidance, "Leave unknown custom implementation intent explicit");
        Assert.AreEqual(12, CanonicalSessionGuidance.WorkflowSteps.Count);
        Assert.IsTrue(guidance.IndexOf("invoke explain", StringComparison.OrdinalIgnoreCase) < guidance.IndexOf("Invoke construct", StringComparison.Ordinal));
        Assert.IsTrue(guidance.IndexOf("Invoke construct", StringComparison.Ordinal) < guidance.IndexOf("Invoke evaluate", StringComparison.Ordinal));
        Assert.IsFalse(guidance.Contains("authentication", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(guidance.Contains("business domain", StringComparison.OrdinalIgnoreCase));
    }
}
