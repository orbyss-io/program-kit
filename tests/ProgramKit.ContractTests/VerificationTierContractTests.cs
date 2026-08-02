using System.IO;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class VerificationTierContractTests
{
    [TestMethod]
    public void Local_tiers_are_bounded_and_only_protected_ci_runs_authoritative_proof()
    {
        string script = File.ReadAllText(Path.Combine(TestRepository.Root, "eng", "Invoke-Verification.ps1"));
        StringAssert.Contains(script, "ValidateSet('Edit', 'Story', 'PrePr', 'Ci', 'Human', 'Fast', 'Contract')");
        StringAssert.Contains(script, "'Fast' { 'Edit' }");
        StringAssert.Contains(script, "'Contract' { 'Story' }");
        StringAssert.Contains(script, "$env:GITHUB_ACTIONS -ne 'true'");
        StringAssert.Contains(script, "CI verification is protected-runner-only");
        StringAssert.Contains(script, "SpecKitAdapterBootstrapAcceptanceTests");
        StringAssert.Contains(script, "Human verification is a post-CI review checkpoint");
        Assert.AreEqual(1, Count(script, "Generate-DistributionEvidence.ps1"));
        Assert.AreEqual(1, Count(script, "dotnet test ProgramKit.slnx"));

        int prePrStart = script.IndexOf("$dependencyChanges", System.StringComparison.Ordinal);
        string prePr = script[prePrStart..];
        Assert.IsFalse(prePr.Contains("Generate-DistributionEvidence.ps1", System.StringComparison.Ordinal));
        Assert.IsFalse(prePr.Contains("windows-latest", System.StringComparison.Ordinal));
        Assert.IsFalse(prePr.Contains("ubuntu-latest", System.StringComparison.Ordinal));
    }

    [TestMethod]
    public void Workflow_runs_core_once_and_only_platform_sensitive_proof_on_two_operating_systems()
    {
        string workflow = File.ReadAllText(Path.Combine(TestRepository.Root, ".github", "workflows", "vertical-slice.yml"));
        StringAssert.Contains(workflow, "  core:");
        StringAssert.Contains(workflow, "runs-on: ubuntu-latest");
        StringAssert.Contains(workflow, "./eng/Invoke-Verification.ps1 -Mode Ci");
        StringAssert.Contains(workflow, "  platform:");
        StringAssert.Contains(workflow, "os: [windows-latest, ubuntu-latest]");
        StringAssert.Contains(workflow, "--filter");
        StringAssert.Contains(workflow, "SpecKitAdapterProductRuntimeAcceptanceTests");
        Assert.AreEqual(1, Count(workflow, "Run authoritative Ubuntu core proof once"));
        Assert.AreEqual(1, Count(workflow, "Upload bounded core evidence"));

        string platform = workflow[workflow.IndexOf("  platform:", System.StringComparison.Ordinal)..];
        Assert.IsFalse(platform.Contains("Generate-DistributionEvidence.ps1", System.StringComparison.Ordinal));
        Assert.IsFalse(platform.Contains("dotnet test ProgramKit.slnx", System.StringComparison.Ordinal));
        Assert.IsFalse(platform.Contains("dotnet format ProgramKit.slnx", System.StringComparison.Ordinal));
    }

    [TestMethod]
    public void Evidence_invalidation_has_no_time_branch_or_repository_head_inputs()
    {
        string engine = File.ReadAllText(Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "Handoff", "TraceInvalidationEngine.cs"));
        Assert.IsFalse(engine.Contains("DateTime", System.StringComparison.Ordinal));
        Assert.IsFalse(engine.Contains("branch", System.StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(engine.Contains("GITHUB_SHA", System.StringComparison.Ordinal));
        Assert.IsFalse(engine.Contains("HEAD", System.StringComparison.Ordinal));
        StringAssert.Contains(engine, "retained-evidence:");
        StringAssert.Contains(engine, "compatibility:");
        StringAssert.Contains(engine, "implementation:");
    }

    private static int Count(string value, string needle)
    {
        int count = 0;
        int index = 0;
        while ((index = value.IndexOf(needle, index, System.StringComparison.Ordinal)) >= 0)
        {
            count++;
            index += needle.Length;
        }

        return count;
    }
}
