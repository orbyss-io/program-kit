using System;
using System.Diagnostics;
using System.IO;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterHumanReviewSeedContractTests
{
    [TestMethod]
    public void Human_review_seed_has_valid_scripts_and_one_unambiguous_unpublished_flow()
    {
        string initializePath = Path.Combine(TestRepository.Root, "eng", "Initialize-SpecKitAdapterHumanReview.ps1");
        string servePath = Path.Combine(TestRepository.Root, "eng", "Start-SpecKitAdapterHumanReviewCatalog.ps1");
        AssertPowerShellParses(initializePath);
        AssertPowerShellParses(servePath);

        string initialize = File.ReadAllText(initializePath);
        string serve = File.ReadAllText(servePath);
        string quickstart = File.ReadAllText(Path.Combine(TestRepository.Root, "specs", "003-speckit-adapter", "quickstart.md"));

        StringAssert.Contains(initialize, "status --porcelain=v1");
        StringAssert.Contains(initialize, "Pack-ProgramKitTool.ps1");
        StringAssert.Contains(initialize, "$env:NUGET_PACKAGES = Join-Path $packageCache 'packages'");
        StringAssert.Contains(initialize, "Pack-SpecKitAdapter.ps1");
        StringAssert.Contains(initialize, "consumer-01");
        StringAssert.Contains(initialize, "consumer-02");
        StringAssert.Contains(initialize, "consumer-03");
        StringAssert.Contains(initialize, "status = 'ready'");
        Assert.IsFalse(initialize.Contains("specify init", StringComparison.Ordinal));
        Assert.IsFalse(initialize.Contains("tool run program-kit", StringComparison.Ordinal));

        StringAssert.Contains(serve, "environment.cli.digest");
        StringAssert.Contains(serve, "environment.adapter.digest");
        StringAssert.Contains(serve, "http.server");
        StringAssert.Contains(serve, "Keep this terminal open during all three review journeys");

        StringAssert.Contains(quickstart, "The CLI and adapter are not published");
        StringAssert.Contains(quickstart, "Initialize-SpecKitAdapterHumanReview.ps1");
        StringAssert.Contains(quickstart, "Start-SpecKitAdapterHumanReviewCatalog.ps1");
        StringAssert.Contains(quickstart, "Do not run a human journey in the Program Kit repository");
        StringAssert.Contains(quickstart, "$speckit-orbyss-program-kit-adapter-doctor");
        StringAssert.Contains(quickstart, "chat skill, not a PowerShell command");
        StringAssert.Contains(quickstart, "does not need to transcribe JSON or manually run every command");
    }

    private static void AssertPowerShellParses(string path)
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
        start.ArgumentList.Add("-Command");
        start.ArgumentList.Add(
            "$tokens=$null; $errors=$null; " +
            "[Management.Automation.Language.Parser]::ParseFile($env:PROGRAM_KIT_SCRIPT_TO_PARSE,[ref]$tokens,[ref]$errors) | Out-Null; " +
            "if ($errors.Count) { $errors | ForEach-Object { $_.Message }; exit 1 }");
        start.Environment["PROGRAM_KIT_SCRIPT_TO_PARSE"] = path;

        using Process process = Process.Start(start) ?? throw new AssertFailedException("Could not start PowerShell syntax validation.");
        string output = process.StandardOutput.ReadToEnd();
        string error = process.StandardError.ReadToEnd();
        Assert.IsTrue(process.WaitForExit(20_000), "PowerShell syntax validation timed out.");
        Assert.AreEqual(0, process.ExitCode, output + error);
    }
}
