using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeProviderParityAcceptanceTests
{
    private const string CorpusIdentity = "sha256:12d964d52f2b1aa374c158643d0c497e9eb0e511ba828edcac69020eedc7320b";

    [TestMethod]
    public void Shared_corpus_preserves_direct_neutral_Codex_and_Claude_meaning()
    {
        string corpusRoot = Path.Combine(TestRepository.Root, "tests", "Fixtures", "SessionIntegration", "Providers", "Conformance");
        Assert.AreEqual(CorpusIdentity, DigestCorpus(corpusRoot));

        JsonNode input = JsonNode.Parse(File.ReadAllText(Path.Combine(corpusRoot, "canonical-input.json")))!;
        JsonNode result = JsonNode.Parse(File.ReadAllText(Path.Combine(corpusRoot, "result.json")))!;
        JsonNode authority = JsonNode.Parse(File.ReadAllText(Path.Combine(corpusRoot, "authority.json")))!;
        JsonNode diagnostic = JsonNode.Parse(File.ReadAllText(Path.Combine(corpusRoot, "diagnostic.json")))!;
        JsonNode artifact = JsonNode.Parse(File.ReadAllText(Path.Combine(corpusRoot, "artifact.json")))!;

        Assert.AreEqual("session-explain", input["operation"]!.GetValue<string>());
        Assert.AreEqual("workspace", input["scope"]!.GetValue<string>());
        Assert.AreEqual("none", input["effect"]!.GetValue<string>());
        Assert.AreEqual("program-kit.operation-result/v1", result["schema"]!.GetValue<string>());
        Assert.AreEqual("succeeded", result["outcome"]!.GetValue<string>());
        Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
        Assert.IsTrue(authority["requestBound"]!.GetValue<bool>());
        Assert.IsFalse(authority["ambientAuthority"]!.GetValue<bool>());
        Assert.IsTrue(diagnostic["structured"]!.GetValue<bool>());
        Assert.IsTrue(diagnostic["boundedDisclosure"]!.GetValue<bool>());
        Assert.AreEqual("generated-owned", artifact["ownership"]!.GetValue<string>());
        Assert.AreEqual("exact-admitted-digest-only", artifact["removalPolicy"]!.GetValue<string>());

        SessionSemanticObservation[] observations =
        {
            Observation("direct-cli"),
            Observation("neutral-harness"),
            Observation("codex"),
            Observation("claude-code"),
        };
        SessionProviderConformanceReport report = ClaudeConformanceProfiles.Compare(observations);
        Assert.IsTrue(report.Conforms, string.Join(';', report.Failures));
    }

    [TestMethod]
    public void Provider_prerequisite_diagnostic_cannot_change_canonical_result_meaning()
    {
        ClaudeObservationClassification unavailable = ClaudeObservationClassifier.Classify(new(
            "2.0.0",
            ClaudeAuthenticationState.NotEvaluated,
            ClaudeWorkspaceTrustState.NotEvaluated,
            ClaudeSkillDiscoveryState.NotEvaluated,
            true,
            false,
            OperationOutcome.Succeeded,
            true,
            false));

        CollectionAssert.Contains(unavailable.DiagnosticIds.ToArray(), ClaudeDiagnosticCatalog.Id(1));
        SessionProviderConformanceReport report = ClaudeConformanceProfiles.Compare(new[] { Observation("direct-cli"), Observation("claude-code") });
        Assert.IsTrue(report.Conforms);
    }

    private static SessionSemanticObservation Observation(string channel) => new(
        channel, PublicCommand.SessionExplain, OperationOutcome.Succeeded, EffectState.None,
        PrimaryDisposition.Complete, "program-kit.operation-result/v1", true, true, true, true);

    private static string DigestCorpus(string root)
    {
        string identityInput = string.Join('\n', Directory.EnumerateFiles(root, "*.json", SearchOption.TopDirectoryOnly)
            .OrderBy(static path => Path.GetFileName(path), StringComparer.Ordinal)
            .Select(static path => Path.GetFileName(path) + ":sha256:" + Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant()));
        return "sha256:" + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(identityInput))).ToLowerInvariant();
    }
}
