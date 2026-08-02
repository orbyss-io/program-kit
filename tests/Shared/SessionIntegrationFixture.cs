using System;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;
using Orbyss.ProgramKit.SessionIntegration.Publication;

namespace Orbyss.ProgramKit.Tests;

internal sealed record SessionRequestPaths(string Explain, string Install, string Verify);

internal static class SessionIntegrationFixture
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
    private static readonly DateTimeOffset Instant = new(2026, 8, 1, 12, 0, 0, TimeSpan.Zero);
    private static readonly SessionProviderManifest Manifest = new CodexSessionProviderAdapter().Manifest;

    public static SessionIntegrationServices Services() =>
        new(new SessionProviderRegistry(new[] { new CodexSessionProviderAdapter() }), "1.0.0-alpha.2");

    public static string ExplainRequest(string workspaceRoot) => WriteLifecycleRequests(workspaceRoot).Explain;

    public static SessionRequestPaths WriteLifecycleRequests(string workspaceRoot)
    {
        string requests = Path.Combine(workspaceRoot, "requests");
        Directory.CreateDirectory(requests);
        EnsureCliEvidence(workspaceRoot);
        string expected = new SessionInstallationStore(workspaceRoot, "codex").CurrentStateDigest(new[] { ".agents/skills/program-kit/SKILL.md" });

        JsonObject explain = Request("explain", "none", workspaceRoot);
        JsonObject install = Request("install", "committed", workspaceRoot);
        install["expectedInstallationState"] = expected;
        JsonObject grant = Grant(CanonicalJson.Digest(install), install["workspace"]!["identity"]!.AsObject(), "session-install", "install-codex");
        string grantPath = Path.Combine(workspaceRoot, ".program-kit", "authority", "session-install.json");
        Directory.CreateDirectory(Path.GetDirectoryName(grantPath)!);
        byte[] grantBytes = CanonicalJson.Encode(grant);
        File.WriteAllBytes(grantPath, grantBytes);
        install["authorityGrant"] = Artifact("authority-grant", ".program-kit/authority/session-install.json", Digests.Sha256(grantBytes), "consumer-owned");
        JsonObject verify = Request("verify", "none", workspaceRoot);

        string explainPath = Path.Combine(requests, "session-explain.json");
        string installPath = Path.Combine(requests, "session-install.json");
        string verifyPath = Path.Combine(requests, "session-verify.json");
        File.WriteAllBytes(explainPath, CanonicalJson.Encode(explain));
        File.WriteAllBytes(installPath, CanonicalJson.Encode(install));
        File.WriteAllBytes(verifyPath, CanonicalJson.Encode(verify));
        return new SessionRequestPaths(explainPath, installPath, verifyPath);
    }

    public static string WriteRemoveRequest(string workspaceRoot)
    {
        string requests = Path.Combine(workspaceRoot, "requests");
        Directory.CreateDirectory(requests);
        EnsureCliEvidence(workspaceRoot);
        JsonObject remove = Request("remove", "committed", workspaceRoot);
        remove["expectedInstallationState"] = new SessionInstallationStore(workspaceRoot, "codex").CurrentStateDigest(new[] { ".agents/skills/program-kit/SKILL.md" });
        JsonObject grant = Grant(CanonicalJson.Digest(remove), remove["workspace"]!["identity"]!.AsObject(), "session-remove", "remove-codex");
        string grantPath = Path.Combine(workspaceRoot, ".program-kit", "authority", "session-remove.json");
        Directory.CreateDirectory(Path.GetDirectoryName(grantPath)!);
        byte[] grantBytes = CanonicalJson.Encode(grant);
        File.WriteAllBytes(grantPath, grantBytes);
        remove["authorityGrant"] = Artifact("authority-grant", ".program-kit/authority/session-remove.json", Digests.Sha256(grantBytes), "consumer-owned");
        string removePath = Path.Combine(requests, "session-remove.json");
        File.WriteAllBytes(removePath, CanonicalJson.Encode(remove));
        return removePath;
    }

    public static SessionProjectionContext ProjectionContext()
    {
        GovernedIdentity workspace = Identity("consumer.example", "workspace", "fixture", "1.0.0");
        CliReleaseIdentity cli = ProjectionCli();
        SessionIntegrationRequest request = new(
            "program-kit.session-integration-request/v1", CanonicalJson.Profile, SessionLifecycleOperation.Explain,
            new EvaluationContext(Instant, Identity("consumer.example", "evaluation-source", "fixture", "1.0.0"), "approved-declared-instant"),
            new SessionWorkspaceBinding(workspace, EmptyDigest), "workspace",
            new SessionProviderSelection(Provider(), Adapter(), CanonicalSessionGuidance.Definition.Identity, Conformance()), cli,
            RequestedEffect.None, EmptyDigest, EmptyDigest, null, null);
        return new SessionProjectionContext(CanonicalSessionGuidance.Definition, request, false);
    }

    public static SessionInstallationRecord InstallationRecord(string workspaceRoot, byte[] skill)
    {
        EnsureCliEvidence(workspaceRoot);
        string digest = Digests.Sha256(skill);
        string requestIdentity = Digests.Sha256(Encoding.UTF8.GetBytes("fixture installation request"));
        string requestCoreIdentity = Digests.Sha256(Encoding.UTF8.GetBytes("fixture installation request core"));
        CliReleaseIdentity cli = Cli(workspaceRoot);
        string setDigest = Digests.Sha256(Encoding.UTF8.GetBytes($".agents/skills/program-kit/SKILL.md:{digest}"));
        string installation = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[]
        {
            requestCoreIdentity,
            CanonicalSessionGuidance.Definition.Identity.Digest,
            Provider().Digest,
            Adapter().Digest,
            Conformance().Digest,
            cli.PackageDigest,
            cli.ExecutableDigest,
            cli.RuntimeProfile.Digest,
            setDigest,
        })));
        string journalLogicalPath = ".program-kit/session-integrations/codex/publication.journal.json";
        string journalPath = Path.Combine(workspaceRoot, journalLogicalPath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(journalPath)!);
        byte[] journal = CanonicalJson.Encode(new JsonObject { ["schema"] = "program-kit.namespaced-publication-journal/v1", ["state"] = "committed", ["transactionIdentity"] = installation });
        File.WriteAllBytes(journalPath, journal);
        string receipt = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[] { installation, requestIdentity, setDigest })));
        return new SessionInstallationRecord(
            "program-kit.session-installation-record/v1", Identity("orbyss.program-kit", "session-installation", "codex", "1.0.0", installation), requestIdentity, requestCoreIdentity,
            new SessionWorkspaceBinding(Identity("consumer.example", "workspace", "fixture", "1.0.0"), Digests.Sha256(Encoding.UTF8.GetBytes(Path.GetFullPath(workspaceRoot)))), "workspace",
            CanonicalSessionGuidance.Definition.Identity, new SessionProviderSelection(Provider(), Adapter(), CanonicalSessionGuidance.Definition.Identity, Conformance()), cli,
            new[] { new SessionProjectionArtifact(".agents/skills/program-kit/SKILL.md", "text/markdown", ArtifactOwnership.GeneratedOwned, Adapter(), CanonicalSessionGuidance.Definition.Identity, digest, ClaimClass.CanonicalByte, "exact-admitted-digest-only") },
            new SessionPublicationEvidence(journalLogicalPath, Digests.Sha256(journal), setDigest, "committed"), SessionIntegrationState.Admitted, SessionAvailability.ReloadRequired, receipt, EmptyDigest);
    }

    private static JsonObject Request(string operation, string effect, string workspaceRoot)
    {
        JsonObject workspaceIdentity = IdentityJson(Identity("consumer.example", "workspace", "fixture", "1.0.0"));
        return new JsonObject
        {
            ["schema"] = "program-kit.session-integration-request/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["operation"] = operation,
            ["evaluationContext"] = new JsonObject { ["instant"] = "2026-08-01T12:00:00Z", ["source"] = IdentityJson(Identity("consumer.example", "evaluation-source", "fixture", "1.0.0")), ["assurance"] = "approved-declared-instant" },
            ["workspace"] = new JsonObject { ["identity"] = workspaceIdentity, ["rootBinding"] = Digests.Sha256(Encoding.UTF8.GetBytes(Path.GetFullPath(workspaceRoot))) },
            ["scope"] = "workspace",
            ["providerSelection"] = new JsonObject { ["provider"] = Selection("provider", Provider()), ["adapter"] = Selection("adapter", Adapter()), ["definition"] = Selection("definition", CanonicalSessionGuidance.Definition.Identity), ["conformanceProfile"] = IdentityJson(Conformance()) },
            ["cliRelease"] = CliJson(Cli(workspaceRoot)),
            ["requestedEffect"] = effect,
        };
    }

    private static void EnsureCliEvidence(string workspaceRoot)
    {
        string executable = Path.Combine(workspaceRoot, ExecutableLogicalPath().Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(executable)!);
        if (!File.Exists(executable)) File.Copy(TestRepository.CliExecutable, executable);

        string packageName = "orbyss.programkit.cli";
        string package = Path.Combine(
            Path.GetDirectoryName(executable)!,
            ".store",
            packageName,
            "1.0.0-alpha.2",
            packageName,
            "1.0.0-alpha.2",
            $"{packageName}.1.0.0-alpha.2.nupkg");
        Directory.CreateDirectory(Path.GetDirectoryName(package)!);
        if (!File.Exists(package)) File.Copy(TestRepository.CliExecutable, package);
    }

    private static JsonObject Grant(string requestBinding, JsonObject workspaceIdentity, string operation, string name) => new()
    {
        ["schema"] = "program-kit.authority-grant/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["identity"] = IdentityJson(Identity("consumer.example", "authority-grant", name, "1.0.0")),
        ["issuerAssertion"] = new JsonObject { ["provider"] = IdentityJson(Identity("consumer.example", "authority-provider", "repository-record", "1.0.0")), ["issuer"] = "fixture-human-review-record", ["assurance"] = "repository-record-presence" },
        ["subjects"] = new JsonArray(new JsonObject { ["kind"] = "workspace", ["identity"] = workspaceIdentity.DeepClone() }),
        ["operations"] = new JsonArray(operation),
        ["effects"] = new JsonArray("committed"),
        ["requestBinding"] = requestBinding,
        ["conditions"] = new JsonArray(
            new JsonObject { ["kind"] = "provider", ["value"] = Safe(Provider().StableKey) },
            new JsonObject { ["kind"] = "scope", ["value"] = Safe("workspace") }),
        ["validity"] = new JsonObject { ["notBefore"] = "2026-08-01T11:59:00Z", ["notAfter"] = "2026-08-01T12:01:00Z" },
        ["revocationReference"] = Artifact("revocation", ".program-kit/authority/revocations.json", EmptyDigest, "consumer-owned"),
        ["provenance"] = Artifact("authority-provenance", ".program-kit/authority/review.json", EmptyDigest, "consumer-owned"),
    };

    private static JsonObject Safe(string value) => new() { ["classification"] = "public", ["valueKind"] = "string", ["value"] = value };
    private static JsonObject Selection(string role, GovernedIdentity selected) => new() { ["role"] = role, ["selected"] = IdentityJson(selected), ["selectionAuthority"] = IdentityJson(Identity("orbyss.program-kit", "selection-authority", role, "1.0.0")), ["trace"] = new JsonObject { ["source"] = Artifact("selection", $"requests/{role}.json", EmptyDigest, "consumer-owned"), ["pointer"] = $"/providerSelection/{role}", ["claimKind"] = "explicit-selection" } };
    private static JsonObject Artifact(string kind, string path, string digest, string ownership) => new() { ["identity"] = IdentityJson(Identity("consumer.example", kind, Path.GetFileNameWithoutExtension(path).ToLowerInvariant(), "1.0.0", digest)), ["mediaType"] = "application/json", ["logicalPath"] = path, ["digest"] = digest, ["ownership"] = ownership };

    private static CliReleaseIdentity Cli(string workspaceRoot)
    {
        string executable = Path.Combine(workspaceRoot, ExecutableLogicalPath().Replace('/', Path.DirectorySeparatorChar));
        string packageName = "orbyss.programkit.cli";
        string package = Path.Combine(Path.GetDirectoryName(executable)!, ".store", packageName, "1.0.0-alpha.2", packageName, "1.0.0-alpha.2", $"{packageName}.1.0.0-alpha.2.nupkg");
        return new CliReleaseIdentity(
            "program-kit.cli-release-identity/v1",
            CanonicalJson.Profile,
            "Orbyss.ProgramKit.Cli",
            "1.0.0-alpha.2",
            PackageSource(),
            Digests.Sha256(File.ReadAllBytes(package)),
            "program-kit",
            ExecutableLogicalPath(),
            Digests.Sha256(File.ReadAllBytes(executable)),
            "1.0.0-alpha.2",
            SessionCliReleaseContract.Current("1.0.0-alpha.2").RuntimeProfile,
            ClaimClass.VerifiedEquivalent);
    }

    private static CliReleaseIdentity ProjectionCli() => new(
        "program-kit.cli-release-identity/v1",
        CanonicalJson.Profile,
        "Orbyss.ProgramKit.Cli",
        "1.0.0-alpha.2",
        PackageSource(),
        Digests.Sha256(Encoding.UTF8.GetBytes("fixture package")),
        "program-kit",
        ExecutableLogicalPath(),
        Digests.Sha256(Encoding.UTF8.GetBytes("fixture executable")),
        "1.0.0-alpha.2",
        SessionCliReleaseContract.Current("1.0.0-alpha.2").RuntimeProfile,
        ClaimClass.VerifiedEquivalent);

    private static GovernedIdentity PackageSource() => Identity("consumer.example", "package-source", "local-feed", "1.0.0", Digests.Sha256(Encoding.UTF8.GetBytes("consumer.example package source local-feed v1")));
    private static string ExecutableLogicalPath() => OperatingSystem.IsWindows() ? ".program-kit/tools/program-kit.exe" : ".program-kit/tools/program-kit";
    private static JsonObject CliJson(CliReleaseIdentity value) => new() { ["schema"] = value.Schema, ["canonicalProfile"] = value.CanonicalProfile, ["packageId"] = value.PackageId, ["packageVersion"] = value.PackageVersion, ["packageSource"] = IdentityJson(value.PackageSource), ["packageDigest"] = value.PackageDigest, ["commandName"] = value.CommandName, ["workspaceRelativeExecutable"] = value.WorkspaceRelativeExecutable, ["executableDigest"] = value.ExecutableDigest, ["reportedVersion"] = value.ReportedVersion, ["runtimeProfile"] = IdentityJson(value.RuntimeProfile), ["claimClass"] = "verified-equivalent" };
    private static GovernedIdentity Provider() => Manifest.ProviderIdentity;
    private static GovernedIdentity Adapter() => Manifest.AdapterIdentity;
    private static GovernedIdentity Conformance() => Manifest.ConformanceProfile;
    private static GovernedIdentity Identity(string authority, string kind, string name, string revision, string digest = EmptyDigest) => new(authority, kind, name, revision, digest);
    private static JsonObject IdentityJson(GovernedIdentity value) => new() { ["authority"] = value.Authority, ["kind"] = value.Kind, ["name"] = value.Name, ["revision"] = value.Revision, ["digest"] = value.Digest };
}
