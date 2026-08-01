using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Artifacts;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed record SessionInstallationInspection(
    SessionIntegrationState State,
    SessionAvailability SessionAvailability,
    SessionInstallationRecord? Record,
    IReadOnlyList<SessionProjectionObservation> Observations);

public sealed class SessionInstallationStore
{
    private readonly string workspaceRoot;
    private readonly string stateRoot;
    private readonly string recordPath;

    public SessionInstallationStore(string workspaceRoot, string provider)
    {
        this.workspaceRoot = Path.GetFullPath(workspaceRoot);
        string normalizedProvider = provider.ToLowerInvariant();
        if (normalizedProvider.Any(static value => !(char.IsAsciiLetterOrDigit(value) || value == '-'))) throw new ArgumentException("Provider state name is not safe.", nameof(provider));
        stateRoot = Path.Combine(this.workspaceRoot, ".program-kit", "session-integrations", normalizedProvider);
        recordPath = Path.Combine(stateRoot, "installation.json");
    }

    public string RecordLogicalPath => LogicalPaths.Normalize(Path.GetRelativePath(workspaceRoot, recordPath).Replace('\\', '/'));

    public SessionInstallationInspection Inspect()
    {
        if (!File.Exists(recordPath)) return new(SessionIntegrationState.Absent, SessionAvailability.NotEvaluated, null, Array.Empty<SessionProjectionObservation>());
        SessionInstallationRecord record;
        try { record = Parse(CanonicalJson.Parse(File.ReadAllBytes(recordPath)).AsObject()); }
        catch { return new(SessionIntegrationState.Partial, SessionAvailability.NotEvaluated, null, Array.Empty<SessionProjectionObservation>()); }

        List<SessionProjectionObservation> observations = new();
        bool missing = false;
        bool drift = false;
        foreach (SessionProjectionArtifact artifact in record.ProjectionSet)
        {
            string path = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
            string? observed = File.Exists(path) ? Digests.Sha256(File.ReadAllBytes(path)) : null;
            string state = observed is null ? "missing" : string.Equals(observed, artifact.ContentDigest, StringComparison.Ordinal) ? "exact" : "drifted";
            missing |= observed is null;
            drift |= observed is not null && !string.Equals(observed, artifact.ContentDigest, StringComparison.Ordinal);
            observations.Add(new SessionProjectionObservation(artifact.LogicalPath, artifact.ContentDigest, observed, state));
        }

        SessionIntegrationState integrationState = drift ? SessionIntegrationState.Drifted : missing ? SessionIntegrationState.Partial : SessionIntegrationState.Exact;
        return new(integrationState, record.SessionAvailability, record, observations);
    }

    public string CurrentStateDigest(IEnumerable<string> projectionPaths)
    {
        List<string> observations = new();
        foreach (string logicalPath in projectionPaths.OrderBy(static value => value, StringComparer.Ordinal))
        {
            string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
            observations.Add($"{logicalPath}:{(File.Exists(path) ? Digests.Sha256(File.ReadAllBytes(path)) : "absent")}");
        }

        observations.Add($"installation:{(File.Exists(recordPath) ? Digests.Sha256(File.ReadAllBytes(recordPath)) : "absent")}");
        return Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', observations)));
    }

    public void Admit(SessionInstallationRecord record)
    {
        Directory.CreateDirectory(stateRoot);
        JsonObject document = Project(record);
        document.Remove("recordDigest");
        string digest = CanonicalJson.Digest(document);
        document["recordDigest"] = digest;
        AtomicWrite(recordPath, CanonicalJson.Encode(document));
        if (!string.Equals(Digests.Sha256(File.ReadAllBytes(recordPath)), Digests.Sha256(CanonicalJson.Encode(document)), StringComparison.Ordinal))
            throw new IOException("The admitted installation record bytes could not be verified.");
    }

    public bool IsGrantConsumed(string grantIdentity) => File.Exists(GrantPath(grantIdentity));

    public void MarkGrantConsumed(string grantIdentity, string requestIdentity)
    {
        JsonObject marker = new() { ["schema"] = "program-kit.consumed-authority-grant/v1", ["grantIdentity"] = grantIdentity, ["requestIdentity"] = requestIdentity };
        AtomicWrite(GrantPath(grantIdentity), CanonicalJson.Encode(marker));
    }

    private string GrantPath(string grantIdentity)
    {
        string digest = Digests.Sha256(Encoding.UTF8.GetBytes(grantIdentity))["sha256:".Length..];
        return Path.Combine(stateRoot, "consumed-grants", $"{digest}.json");
    }

    private static void AtomicWrite(string path, byte[] bytes)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        string temporary = $"{path}.{Guid.NewGuid():N}.tmp";
        using (FileStream stream = new(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        {
            stream.Write(bytes);
            stream.Flush(flushToDisk: true);
        }

        File.Move(temporary, path, overwrite: true);
    }

    private static JsonObject Project(SessionInstallationRecord record) => new()
    {
        ["schema"] = record.Schema,
        ["installationIdentity"] = Identity(record.InstallationIdentity),
        ["requestIdentity"] = record.RequestIdentity,
        ["requestCoreIdentity"] = record.RequestCoreIdentity,
        ["workspaceIdentity"] = new JsonObject { ["identity"] = Identity(record.WorkspaceIdentity.Identity), ["rootBinding"] = record.WorkspaceIdentity.RootBindingDigest },
        ["scope"] = record.Scope,
        ["definition"] = Identity(record.Definition),
        ["provider"] = new JsonObject { ["provider"] = Identity(record.Provider.Provider), ["adapter"] = Identity(record.Provider.Adapter), ["definition"] = Identity(record.Provider.Definition), ["conformanceProfile"] = Identity(record.Provider.ConformanceProfile) },
        ["cliRelease"] = Cli(record.CliRelease),
        ["projectionSet"] = new JsonArray(record.ProjectionSet.Select(Projection).ToArray()),
        ["publication"] = new JsonObject { ["journalLogicalPath"] = record.Publication.JournalLogicalPath, ["journalDigest"] = record.Publication.JournalDigest, ["liveStateDigest"] = record.Publication.LiveStateDigest, ["state"] = record.Publication.State },
        ["state"] = Kebab(record.State),
        ["sessionAvailability"] = Kebab(record.SessionAvailability),
        ["admissionReceipt"] = record.AdmissionReceipt,
        ["recordDigest"] = record.RecordDigest,
    };

    private static SessionInstallationRecord Parse(JsonObject document)
    {
        JsonObject workspace = document["workspaceIdentity"]!.AsObject();
        JsonObject provider = document["provider"]!.AsObject();
        JsonObject publication = document["publication"]!.AsObject();
        return new SessionInstallationRecord(
            document["schema"]!.GetValue<string>(), ParseIdentity(document["installationIdentity"]!.AsObject()), document["requestIdentity"]!.GetValue<string>(), document["requestCoreIdentity"]!.GetValue<string>(),
            new SessionWorkspaceBinding(ParseIdentity(workspace["identity"]!.AsObject()), workspace["rootBinding"]!.GetValue<string>()), document["scope"]!.GetValue<string>(), ParseIdentity(document["definition"]!.AsObject()),
            new SessionProviderSelection(ParseIdentity(provider["provider"]!.AsObject()), ParseIdentity(provider["adapter"]!.AsObject()), ParseIdentity(provider["definition"]!.AsObject()), ParseIdentity(provider["conformanceProfile"]!.AsObject())),
            ParseCli(document["cliRelease"]!.AsObject()), document["projectionSet"]!.AsArray().Select(value => ParseProjection(value!.AsObject())).ToArray(),
            new SessionPublicationEvidence(publication["journalLogicalPath"]!.GetValue<string>(), publication["journalDigest"]!.GetValue<string>(), publication["liveStateDigest"]!.GetValue<string>(), publication["state"]!.GetValue<string>()),
            ParseState(document["state"]!.GetValue<string>()), ParseAvailability(document["sessionAvailability"]!.GetValue<string>()), document["admissionReceipt"]!.GetValue<string>(), document["recordDigest"]!.GetValue<string>());
    }

    private static JsonObject Identity(GovernedIdentity value) => new() { ["authority"] = value.Authority, ["kind"] = value.Kind, ["name"] = value.Name, ["revision"] = value.Revision, ["digest"] = value.Digest };
    private static GovernedIdentity ParseIdentity(JsonObject value) => new(value["authority"]!.GetValue<string>(), value["kind"]!.GetValue<string>(), value["name"]!.GetValue<string>(), value["revision"]!.GetValue<string>(), value["digest"]!.GetValue<string>());
    private static JsonObject Projection(SessionProjectionArtifact value) => new() { ["logicalPath"] = value.LogicalPath, ["mediaType"] = value.MediaType, ["ownership"] = "generated-owned", ["producerIdentity"] = Identity(value.ProducerIdentity), ["definitionBinding"] = Identity(value.DefinitionBinding), ["contentDigest"] = value.ContentDigest, ["claimClass"] = "canonical-byte", ["removalPolicy"] = value.RemovalPolicy };
    private static SessionProjectionArtifact ParseProjection(JsonObject value) => new(value["logicalPath"]!.GetValue<string>(), value["mediaType"]!.GetValue<string>(), ArtifactOwnership.GeneratedOwned, ParseIdentity(value["producerIdentity"]!.AsObject()), ParseIdentity(value["definitionBinding"]!.AsObject()), value["contentDigest"]!.GetValue<string>(), ClaimClass.CanonicalByte, value["removalPolicy"]!.GetValue<string>());
    private static JsonObject Cli(CliReleaseIdentity value) => new() { ["schema"] = value.Schema, ["canonicalProfile"] = value.CanonicalProfile, ["packageId"] = value.PackageId, ["packageVersion"] = value.PackageVersion, ["packageSource"] = Identity(value.PackageSource), ["packageDigest"] = value.PackageDigest, ["commandName"] = value.CommandName, ["workspaceRelativeExecutable"] = value.WorkspaceRelativeExecutable, ["executableDigest"] = value.ExecutableDigest, ["reportedVersion"] = value.ReportedVersion, ["runtimeProfile"] = Identity(value.RuntimeProfile), ["claimClass"] = "verified-equivalent" };
    private static CliReleaseIdentity ParseCli(JsonObject value) => new(value["schema"]!.GetValue<string>(), value["canonicalProfile"]!.GetValue<string>(), value["packageId"]!.GetValue<string>(), value["packageVersion"]!.GetValue<string>(), ParseIdentity(value["packageSource"]!.AsObject()), value["packageDigest"]!.GetValue<string>(), value["commandName"]!.GetValue<string>(), value["workspaceRelativeExecutable"]!.GetValue<string>(), value["executableDigest"]!.GetValue<string>(), value["reportedVersion"]!.GetValue<string>(), ParseIdentity(value["runtimeProfile"]!.AsObject()), ClaimClass.VerifiedEquivalent);
    private static SessionIntegrationState ParseState(string value) => value switch { "admitted" => SessionIntegrationState.Admitted, "exact" => SessionIntegrationState.Exact, "drifted" => SessionIntegrationState.Drifted, "stale" => SessionIntegrationState.Stale, "incompatible" => SessionIntegrationState.Incompatible, "partial" => SessionIntegrationState.Partial, "removed" => SessionIntegrationState.Removed, _ => throw new InvalidDataException("Unknown installation state.") };
    private static SessionAvailability ParseAvailability(string value) => value switch { "not-evaluated" => SessionAvailability.NotEvaluated, "reload-required" => SessionAvailability.ReloadRequired, "available" => SessionAvailability.Available, "unavailable" => SessionAvailability.Unavailable, _ => throw new InvalidDataException("Unknown session availability.") };
    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
