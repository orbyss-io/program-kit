using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionInstallationTrustAcceptanceTests
{
    [TestMethod]
    public void Exact_record_is_idempotent_and_remains_reload_required_until_fresh_session_evidence()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        JsonNode first = Install(workspace, requests.Install);
        JsonNode second = Install(workspace, requests.Install);
        Assert.AreEqual(first["session"]!["installationIdentity"]!.GetValue<string>(), second["session"]!["installationIdentity"]!.GetValue<string>());
        Assert.AreEqual("committed", second["effectState"]!.GetValue<string>());

        (int exitCode, string output, _) = TestRepository.RunCli("session", "verify", "--workspace", workspace.Root, "--request", requests.Verify, "--format", "json");
        JsonNode verification = JsonNode.Parse(output) ?? throw new InvalidDataException(output);
        Assert.AreEqual(0, exitCode, output);
        Assert.AreEqual("exact", verification["session"]!["state"]!.GetValue<string>());
        Assert.AreEqual("reload-required", verification["session"]!["sessionAvailability"]!.GetValue<string>());
        Assert.AreEqual("retry", verification["primaryDisposition"]!.GetValue<string>());
    }

    [TestMethod]
    public void Corrupt_record_digest_or_publication_journal_is_partial()
    {
        using SessionIntegrationTestWorkspace corruptRecord = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths corruptRequests = SessionIntegrationFixture.WriteLifecycleRequests(corruptRecord.Root);
        _ = Install(corruptRecord, corruptRequests.Install);
        string recordPath = corruptRecord.PathOf(".program-kit/session-integrations/codex/installation.json");
        JsonObject record = CanonicalJson.Parse(File.ReadAllBytes(recordPath)).AsObject();
        record["admissionReceipt"] = "sha256:" + new string('4', 64);
        File.WriteAllBytes(recordPath, CanonicalJson.Encode(record));
        AssertVerification(corruptRecord, corruptRequests.Verify, "partial", "program-kit.session/PKSES0005");

        using SessionIntegrationTestWorkspace missingJournal = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths journalRequests = SessionIntegrationFixture.WriteLifecycleRequests(missingJournal.Root);
        _ = Install(missingJournal, journalRequests.Install);
        File.Delete(missingJournal.PathOf(".program-kit/session-integrations/codex/publication.journal.json"));
        AssertVerification(missingJournal, journalRequests.Verify, "partial", "program-kit.session/PKSES0005");
    }

    [TestMethod]
    public void Current_cli_drift_is_stale_and_conformance_binding_change_is_incompatible()
    {
        using SessionIntegrationTestWorkspace stale = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths staleRequests = SessionIntegrationFixture.WriteLifecycleRequests(stale.Root);
        _ = Install(stale, staleRequests.Install);
        string executable = stale.PathOf(OperatingSystem.IsWindows() ? ".program-kit/tools/program-kit.exe" : ".program-kit/tools/program-kit");
        File.WriteAllBytes(executable, File.ReadAllBytes(executable).Concat(new byte[] { 0x20 }).ToArray());
        string refreshedVerify = SessionIntegrationFixture.WriteLifecycleRequests(stale.Root).Verify;
        AssertVerification(stale, refreshedVerify, "stale", "program-kit.session/PKSES0004");

        using SessionIntegrationTestWorkspace incompatible = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths incompatibleRequests = SessionIntegrationFixture.WriteLifecycleRequests(incompatible.Root);
        _ = Install(incompatible, incompatibleRequests.Install);
        string recordPath = incompatible.PathOf(".program-kit/session-integrations/codex/installation.json");
        JsonObject record = CanonicalJson.Parse(File.ReadAllBytes(recordPath)).AsObject();
        record["provider"]!["conformanceProfile"]!["digest"] = "sha256:" + new string('5', 64);
        RecomputeRecordTrust(record);
        File.WriteAllBytes(recordPath, CanonicalJson.Encode(record));
        AssertVerification(incompatible, incompatibleRequests.Verify, "incompatible", "program-kit.session/PKSES0003");
    }

    private static JsonNode Install(SessionIntegrationTestWorkspace workspace, string request)
    {
        (int exitCode, string output, _) = TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", request, "--format", "json");
        Assert.AreEqual(0, exitCode, output);
        return JsonNode.Parse(output) ?? throw new InvalidDataException(output);
    }

    private static void AssertVerification(SessionIntegrationTestWorkspace workspace, string request, string expectedState, string diagnostic)
    {
        (int exitCode, string output, _) = TestRepository.RunCli("session", "verify", "--workspace", workspace.Root, "--request", request, "--format", "json");
        JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException(output);
        Assert.AreEqual(3, exitCode, output);
        Assert.AreEqual(expectedState, result["session"]!["state"]!.GetValue<string>(), output);
        Assert.AreEqual(diagnostic, result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>(), output);
        Assert.AreEqual("none", result["effectState"]!.GetValue<string>(), output);
    }

    private static void RecomputeRecordTrust(JsonObject record)
    {
        JsonObject[] projections = record["projectionSet"]!.AsArray().Select(static item => item!.AsObject()).OrderBy(static item => item["logicalPath"]!.GetValue<string>(), StringComparer.Ordinal).ToArray();
        string setDigest = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', projections.Select(static item => $"{item["logicalPath"]!.GetValue<string>()}:{item["contentDigest"]!.GetValue<string>()}"))));
        string installation = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[]
        {
            record["requestCoreIdentity"]!.GetValue<string>(),
            record["definition"]!["digest"]!.GetValue<string>(),
            record["provider"]!["provider"]!["digest"]!.GetValue<string>(),
            record["provider"]!["adapter"]!["digest"]!.GetValue<string>(),
            record["provider"]!["conformanceProfile"]!["digest"]!.GetValue<string>(),
            record["cliRelease"]!["packageDigest"]!.GetValue<string>(),
            record["cliRelease"]!["executableDigest"]!.GetValue<string>(),
            record["cliRelease"]!["runtimeProfile"]!["digest"]!.GetValue<string>(),
            setDigest,
        })));
        record["installationIdentity"]!["digest"] = installation;
        record["publication"]!["liveStateDigest"] = setDigest;
        record["admissionReceipt"] = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[] { installation, record["requestIdentity"]!.GetValue<string>(), setDigest })));
        record.Remove("recordDigest");
        record["recordDigest"] = CanonicalJson.Digest(record);
    }
}
