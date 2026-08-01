using System;
using System.Diagnostics;
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
        StringAssert.Contains(export, "SharedConformance");
        StringAssert.Contains(export, "componentBindings");
        StringAssert.Contains(export, "runtime/build inputs must be committed");
        StringAssert.Contains(export, "SourceRevisionId");
        StringAssert.Contains(export, "conformanceCorpusDigest");
        StringAssert.Contains(initialize, "Review-kit digest mismatch");
        StringAssert.Contains(initialize, "aggregate review-kit identity");
        StringAssert.Contains(initialize, "exact .NET SDK 10.0.302");
        StringAssert.Contains(initialize, ".claude/skills/program-kit");
        StringAssert.Contains(initialize, "runtime source revision");
        StringAssert.Contains(initialize, ".program-kit-source.json");
        StringAssert.Contains(deterministic, "supportClaim = 'not-evaluated'");
        StringAssert.Contains(deterministic, "passed = 10");
        StringAssert.Contains(deterministic, "cliExecutableDigest");
        StringAssert.Contains(live, "[ValidateRange(10, 10)]");
        StringAssert.Contains(live, "$pkProviderResult = $null");
        StringAssert.Contains(live, "finally { $pkProviderResult = $null }");
        StringAssert.Contains(live, "& claude -p");
        Assert.IsFalse(live.Contains("--bare", StringComparison.Ordinal));
        Assert.IsLessThan(live.IndexOf("& claude --version", StringComparison.Ordinal), live.IndexOf("Live Claude trials are blocked", StringComparison.Ordinal));
        StringAssert.Contains(complete, "Accepted review is forbidden");
        StringAssert.Contains(complete, "Count -ne 10");
        Assert.IsFalse(string.Join('\n', export, initialize, deterministic, live, complete).Contains("transcriptPath", StringComparison.OrdinalIgnoreCase));
    }

    [TestMethod]
    public void Exported_review_kit_executes_clean_tamper_contamination_and_acceptance_gates()
    {
        string kit = TestRepository.CreateEmptyWorkspace();
        string cleanConsumer = TestRepository.CreateEmptyWorkspace();
        string contaminatedConsumer = TestRepository.CreateEmptyWorkspace();
        string tamperConsumer = TestRepository.CreateEmptyWorkspace();
        try
        {
            ProcessResult export = RunPowerShell(
                Path.Combine(TestRepository.Root, "eng", "Export-ClaudeCodeReviewKit.ps1"),
                "-Configuration", "Release", "-OutputPath", kit);
            Assert.AreEqual(0, export.ExitCode, export.Output);

            string initialize = Path.Combine(kit, "scripts", "Initialize-ConsumerWorkspace.ps1");
            ProcessResult clean = RunPowerShell(initialize, "-ReviewKit", kit, "-ConsumerRoot", cleanConsumer);
            Assert.AreEqual(0, clean.ExitCode, clean.Output);
            StringAssert.Contains(clean.Output, "\"cleanBoundaryPassed\":true");

            Directory.CreateDirectory(Path.Combine(contaminatedConsumer, ".claude", "skills", "program-kit"));
            File.WriteAllText(Path.Combine(contaminatedConsumer, ".claude", "skills", "program-kit", "SKILL.md"), "consumer state");
            ProcessResult contamination = RunPowerShell(initialize, "-ReviewKit", kit, "-ConsumerRoot", contaminatedConsumer);
            Assert.AreNotEqual(0, contamination.ExitCode);
            StringAssert.Contains(contamination.Output, "Isolated boundary contamination");

            ProcessResult accepted = RunPowerShell(
                Path.Combine(kit, "scripts", "Complete-HumanReview.ps1"),
                "-ReviewKit", kit, "-ConsumerRoot", cleanConsumer, "-Decision", "accepted", "-ReviewerIdentity", "test-reviewer");
            Assert.AreNotEqual(0, accepted.ExitCode);
            StringAssert.Contains(accepted.Output, "Accepted review is forbidden");

            File.AppendAllText(Path.Combine(kit, "README.md"), "tampered");
            ProcessResult tamper = RunPowerShell(initialize, "-ReviewKit", kit, "-ConsumerRoot", tamperConsumer);
            Assert.AreNotEqual(0, tamper.ExitCode);
            StringAssert.Contains(tamper.Output, "Review-kit digest mismatch");
        }
        finally
        {
            TestRepository.DeleteWorkspace(kit);
            TestRepository.DeleteWorkspace(cleanConsumer);
            TestRepository.DeleteWorkspace(contaminatedConsumer);
            TestRepository.DeleteWorkspace(tamperConsumer);
        }
    }

    private static ProcessResult RunPowerShell(string script, params string[] arguments)
    {
        ProcessStartInfo start = new("pwsh")
        {
            WorkingDirectory = TestRepository.Root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(script);
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Unable to start PowerShell.");
        string output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
        process.WaitForExit();
        return new ProcessResult(process.ExitCode, output);
    }

    private sealed record ProcessResult(int ExitCode, string Output);
}
