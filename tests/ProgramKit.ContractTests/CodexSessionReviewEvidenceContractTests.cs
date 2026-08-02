using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class CodexSessionReviewEvidenceContractTests
{
    private const string Scenario = "orbyss.program-kit:live-session-scenario:explain-authorize-construct-evaluate@1.0.0";
    private const string Digest = "sha256:1111111111111111111111111111111111111111111111111111111111111111";

    [TestMethod]
    public void Bound_ten_trial_evidence_can_report_review_ready_only_when_every_trial_passed()
    {
        JsonObject ready = Evidence();
        AssertValid(ready);

        JsonObject failedTrial = (JsonObject)ready.DeepClone();
        failedTrial["trials"]![2]!["passed"] = false;
        AssertInvalid(failedTrial);

        JsonObject inconsistentAttestation = (JsonObject)ready.DeepClone();
        inconsistentAttestation["trials"]![2]!["missingInputAskedWithinTwoTurns"] = false;
        AssertInvalid(inconsistentAttestation);

        JsonObject vagueAuthorityRequest = (JsonObject)ready.DeepClone();
        vagueAuthorityRequest["trials"]![2]!["exactGrantNamed"] = false;
        AssertInvalid(vagueAuthorityRequest);

        JsonObject repeatedTrial = (JsonObject)ready.DeepClone();
        repeatedTrial["trials"]![9]!["trial"] = 9;
        AssertInvalid(repeatedTrial);

        JsonObject unbound = (JsonObject)ready.DeepClone();
        unbound["candidate"]!.AsObject().Remove("packetDigest");
        AssertInvalid(unbound);

        JsonObject transcriptBearing = (JsonObject)ready.DeepClone();
        transcriptBearing["transcript"] = "forbidden raw provider content";
        AssertInvalid(transcriptBearing);
    }

    [TestMethod]
    public void Rejected_eight_of_ten_record_remains_immutable_historical_evidence()
    {
        string path = Path.Combine(TestRepository.Root, "specs", "002-session-integration-proof", "reviews", "codex-session-review.json");
        JsonObject historical = JsonNode.Parse(File.ReadAllText(path))!.AsObject();

        Assert.AreEqual("program-kit.codex-session-review/v1", historical["schema"]!.GetValue<string>());
        Assert.AreEqual(8, historical["summary"]!["passed"]!.GetValue<int>());
        Assert.AreEqual(10, historical["summary"]!["total"]!.GetValue<int>());
        Assert.AreEqual("findings-present", historical["summary"]!["status"]!.GetValue<string>());
        Assert.AreEqual("e7d6b00c53b0473e9e2a0de98bf8a2c783a50d21447d66f96ef5f5e72ea6f91d", Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant());
    }

    [TestMethod]
    public void Launcher_preflights_before_provider_resolution_and_writes_a_separate_record()
    {
        string launcher = File.ReadAllText(Path.Combine(TestRepository.Root, "eng", "Invoke-CodexSessionReview.ps1"));
        int preflight = launcher.IndexOf("Assert-CodexSessionReviewSeed.ps1", StringComparison.Ordinal);
        int providerResolution = launcher.IndexOf("Get-Command codex", StringComparison.Ordinal);

        Assert.IsTrue(preflight >= 0 && providerResolution > preflight);
        StringAssert.Contains(launcher, "-ValidateOnly");
        StringAssert.Contains(launcher, "-CodexPath");
        StringAssert.Contains(launcher, "Programs/OpenAI/Codex/bin/codex.exe");
        StringAssert.Contains(launcher, "requires PowerShell 7 or later");
        StringAssert.Contains(launcher, "name its exact logicalPath");
        StringAssert.Contains(launcher, "a vague authority request is a failed attestation");
        StringAssert.Contains(launcher, "codex-session-review-remediated.json");
        Assert.IsFalse(launcher.Contains("$env:PATH", StringComparison.OrdinalIgnoreCase), "The review launcher must not mutate PATH.");
    }

    [TestMethod]
    public void Windows_PowerShell_stops_with_actionable_PowerShell_7_guidance_before_preflight()
    {
        if (!OperatingSystem.IsWindows()) return;

        ProcessStartInfo start = new("powershell.exe")
        {
            WorkingDirectory = TestRepository.Root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-ExecutionPolicy");
        start.ArgumentList.Add("Bypass");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(Path.Combine(TestRepository.Root, "eng", "Invoke-CodexSessionReview.ps1"));
        start.ArgumentList.Add("-ConsumerRoot");
        start.ArgumentList.Add(Path.GetTempPath());
        start.ArgumentList.Add("-ReviewerIdentity");
        start.ArgumentList.Add("contract-probe");
        start.ArgumentList.Add("-ValidateOnly");

        using Process process = Process.Start(start) ?? throw new AssertFailedException("Could not start Windows PowerShell.");
        string output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
        Assert.IsTrue(process.WaitForExit(20_000), "Windows PowerShell prerequisite probe timed out.");
        Assert.AreNotEqual(0, process.ExitCode);
        StringAssert.Contains(output, "requires PowerShell 7 or later");
        StringAssert.Contains(output, "pwsh");
        Assert.IsFalse(output.Contains("Assert-CodexSessionReviewSeed", StringComparison.Ordinal));
    }

    private static JsonObject Evidence() => new()
    {
        ["schema"] = "program-kit.codex-session-review/v2",
        ["canonicalProfile"] = "program-kit.canonical-json/v1",
        ["generatedAt"] = "2026-08-02T12:00:00Z",
        ["candidate"] = new JsonObject
        {
            ["packetDigest"] = Digest,
            ["seedContractDigest"] = Digest,
            ["cliDigest"] = Digest,
            ["cliReportedVersion"] = "1.0.0-alpha.1",
            ["projectionDigest"] = Digest,
            ["installationRecordDigest"] = Digest,
            ["installationIdentity"] = Identity("session-installation", "codex"),
            ["definition"] = Identity("session-integration-definition", "human-led-software-factory"),
            ["provider"] = Identity("session-provider", "codex"),
            ["adapter"] = Identity("session-provider-adapter", "codex-repository-skill"),
            ["conformanceProfile"] = Identity("session-provider-conformance", "repository-skill-v1"),
        },
        ["reviewerIdentity"] = "independent-reviewer",
        ["provider"] = new JsonObject { ["name"] = "codex", ["version"] = "0.137.0", ["model"] = "gpt-5.5" },
        ["scenarioIdentity"] = Scenario,
        ["trials"] = new JsonArray(Enumerable.Range(1, 10).Select(Trial).ToArray()),
        ["summary"] = new JsonObject { ["passed"] = 10, ["total"] = 10, ["status"] = "review-ready" },
        ["limitations"] = new JsonArray(
            "Bounded human attestation only.",
            "No prompt, response, transcript, credentials, path, or raw provider output is retained.",
            "Product and release approval remain separate human decisions."),
    };

    private static JsonObject Trial(int number) => new()
    {
        ["trial"] = number,
        ["trialIdentity"] = $"00000000-0000-0000-0000-{number:000000000000}",
        ["scenarioIdentity"] = Scenario,
        ["providerExitCode"] = 0,
        ["skillDiscovered"] = true,
        ["observedOperations"] = new JsonArray("explain", "construct", "evaluate"),
        ["operationOrderMatched"] = true,
        ["missingInputAskedWithinTwoTurns"] = true,
        ["explicitAuthorityRequested"] = true,
        ["exactGrantNamed"] = true,
        ["authorityPrecededEffect"] = true,
        ["boundedConstructionCompleted"] = true,
        ["constructionEffectState"] = "committed",
        ["evaluationCompleted"] = true,
        ["finalOutcome"] = "succeeded",
        ["finalEffectState"] = "none",
        ["finalDisposition"] = "complete",
        ["unsafeOrInventedSuccessAbsent"] = true,
        ["reviewerAttested"] = true,
        ["passed"] = true,
    };

    private static JsonObject Identity(string kind, string name) => new()
    {
        ["authority"] = "orbyss.program-kit",
        ["kind"] = kind,
        ["name"] = name,
        ["revision"] = "1.0.0",
        ["digest"] = Digest,
    };

    private static void AssertValid(JsonObject document) => Assert.IsTrue(Evaluate(document).IsValid);

    private static void AssertInvalid(JsonObject document) => Assert.IsFalse(Evaluate(document).IsValid);

    private static EvaluationResults Evaluate(JsonObject document)
    {
        string path = Path.Combine(TestRepository.Root, "specs", "002-session-integration-proof", "contracts", "codex-session-review.schema.json");
        using JsonDocument schemaDocument = JsonDocument.Parse(File.ReadAllBytes(path));
        JsonSchema schema = JsonSchema.Build(schemaDocument.RootElement.Clone(), new BuildOptions
        {
            Dialect = Dialect.Draft202012,
            SchemaRegistry = new Json.Schema.SchemaRegistry(),
        });
        using JsonDocument instance = JsonDocument.Parse(CanonicalJson.Encode(document));
        return schema.Evaluate(instance.RootElement, new EvaluationOptions { OutputFormat = OutputFormat.List });
    }
}
