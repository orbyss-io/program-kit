using System;
using System.IO;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeReviewKitAcceptanceTests
{
    [TestMethod]
    public void Review_scripts_seal_inputs_fail_closed_and_discard_provider_output()
    {
        string reviewRoot = Path.Combine(TestRepository.Root, "eng", "ClaudeCodeReview");
        string export = File.ReadAllText(Path.Combine(TestRepository.Root, "eng", "Export-ClaudeCodeReviewKit.ps1"));
        string initialize = File.ReadAllText(Path.Combine(reviewRoot, "Initialize-ConsumerWorkspace.ps1"));
        string deterministic = File.ReadAllText(Path.Combine(reviewRoot, "Invoke-DeterministicConsumerProof.ps1"));
        string live = File.ReadAllText(Path.Combine(reviewRoot, "Invoke-ClaudeCodeTrials.ps1"));
        string complete = File.ReadAllText(Path.Combine(reviewRoot, "Complete-HumanReview.ps1"));

        StringAssert.Contains(export, "Get-FileHash");
        StringAssert.Contains(export, "canonicalDependencyStatus = 'rejected'");
        StringAssert.Contains(initialize, "Review-kit digest mismatch");
        StringAssert.Contains(initialize, ".program-kit-source.json");
        StringAssert.Contains(deterministic, "supportClaim = 'not-evaluated'");
        StringAssert.Contains(deterministic, "passed = 10");
        StringAssert.Contains(live, "[ValidateRange(10, 10)]");
        StringAssert.Contains(live, "$pkProviderResult = $null");
        StringAssert.Contains(live, "& claude -p");
        Assert.IsFalse(live.Contains("--bare", StringComparison.Ordinal));
        Assert.IsLessThan(live.IndexOf("& claude --version", StringComparison.Ordinal), live.IndexOf("Live Claude trials are blocked", StringComparison.Ordinal));
        StringAssert.Contains(complete, "Accepted review is forbidden");
        StringAssert.Contains(complete, "Count -ne 10");
        Assert.IsFalse(string.Join('\n', export, initialize, deterministic, live, complete).Contains("transcriptPath", StringComparison.OrdinalIgnoreCase));
    }
}
