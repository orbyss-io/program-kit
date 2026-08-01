using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Validation;
using Orbyss.ProgramKit.SessionIntegration.Providers;

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
    private readonly string removalReceiptPath;

    public SessionInstallationStore(string workspaceRoot, string provider)
    {
        this.workspaceRoot = Path.GetFullPath(workspaceRoot);
        string normalizedProvider = provider.ToLowerInvariant();
        if (normalizedProvider.Any(static value => !(char.IsAsciiLetterOrDigit(value) || value == '-'))) throw new ArgumentException("Provider state name is not safe.", nameof(provider));
        stateRoot = Path.Combine(this.workspaceRoot, ".program-kit", "session-integrations", normalizedProvider);
        recordPath = Path.Combine(stateRoot, "installation.json");
        removalReceiptPath = Path.Combine(stateRoot, "removal.json");
    }

    public string RecordLogicalPath => LogicalPaths.Normalize(Path.GetRelativePath(workspaceRoot, recordPath).Replace('\\', '/'));

    public string RemovalReceiptLogicalPath => LogicalPaths.Normalize(Path.GetRelativePath(workspaceRoot, removalReceiptPath).Replace('\\', '/'));
    public SessionInstallationInspection Inspect(SessionIntegrationCandidate? expected = null)
    {
        if (!File.Exists(recordPath))
            return new(File.Exists(removalReceiptPath) ? SessionIntegrationState.Removed : SessionIntegrationState.Absent, SessionAvailability.NotEvaluated, null, Array.Empty<SessionProjectionObservation>());

        SessionInstallationRecord record;
        try
        {
            JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(recordPath)).AsObject();
            ValidateRecordDocument(document);
            record = Parse(document);
            DemandRecordIntegrity(record);
        }
        catch
        {
            return new(SessionIntegrationState.Partial, SessionAvailability.NotEvaluated, null, Array.Empty<SessionProjectionObservation>());
        }

        try
        {
            new SessionCliReleaseVerifier(SessionCliReleaseContract.Current(record.CliRelease.PackageVersion)).DemandExact(workspaceRoot, record.CliRelease);
        }
        catch
        {
            return new(SessionIntegrationState.Stale, record.SessionAvailability, record, Array.Empty<SessionProjectionObservation>());
        }

        string observedRootBinding = Digests.Sha256(Encoding.UTF8.GetBytes(workspaceRoot));
        if (!string.Equals(record.WorkspaceIdentity.RootBindingDigest, observedRootBinding, StringComparison.Ordinal))
            return new(SessionIntegrationState.Stale, record.SessionAvailability, record, Array.Empty<SessionProjectionObservation>());

        if (expected is not null)
        {
            if (record.Provider.ConformanceProfile != expected.Provider.Manifest.ConformanceProfile)
                return new(SessionIntegrationState.Incompatible, record.SessionAvailability, record, Array.Empty<SessionProjectionObservation>());
            if (record.WorkspaceIdentity != expected.Request.Workspace ||
                !string.Equals(record.Scope, expected.Request.Scope, StringComparison.Ordinal) ||
                record.Definition != expected.Request.ProviderSelection.Definition ||
                record.Provider.Provider != expected.Request.ProviderSelection.Provider ||
                record.Provider.Adapter != expected.Request.ProviderSelection.Adapter ||
                record.CliRelease != expected.Request.CliRelease)
                return new(SessionIntegrationState.Stale, record.SessionAvailability, record, Array.Empty<SessionProjectionObservation>());
            if (!ProjectionBindingMatches(record.ProjectionSet, expected))
                return new(SessionIntegrationState.Incompatible, record.SessionAvailability, record, Array.Empty<SessionProjectionObservation>());
        }

        List<SessionProjectionObservation> observations = new();
        bool missing = false;
        bool drift = false;
        foreach (SessionProjectionArtifact artifact in record.ProjectionSet.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal))
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

    private void ValidateRecordDocument(JsonObject document)
    {
        string[] expectedProperties = { "schema", "canonicalProfile", "installationIdentity", "requestIdentity", "requestCoreIdentity", "workspaceIdentity", "scope", "definition", "provider", "cliRelease", "projectionSet", "publication", "state", "sessionAvailability", "admissionReceipt", "recordDigest" };
        if (!document.Select(static item => item.Key).OrderBy(static item => item, StringComparer.Ordinal).SequenceEqual(expectedProperties.OrderBy(static item => item, StringComparer.Ordinal), StringComparer.Ordinal))
            throw new InvalidDataException("The installation-record properties do not match the governed contract.");
        string[] failures = new StructuralSchemaValidator(new SchemaRegistry()).ValidateRequiredShape(ContractSchemaResources.SessionInstallationRecordId, document).ToArray();
        if (failures.Length > 0) throw new InvalidDataException(string.Join("; ", failures));
        if (!string.Equals(document["schema"]?.GetValue<string>(), "program-kit.session-installation-record/v1", StringComparison.Ordinal) ||
            !string.Equals(document["canonicalProfile"]?.GetValue<string>(), CanonicalJson.Profile, StringComparison.Ordinal))
            throw new InvalidDataException("The installation-record schema or canonical profile is unsupported.");

        string storedDigest = document["recordDigest"]?.GetValue<string>() ?? throw new InvalidDataException("recordDigest is required.");
        JsonObject normalized = (JsonObject)document.DeepClone();
        normalized.Remove("recordDigest");
        if (!string.Equals(storedDigest, CanonicalJson.Digest(normalized), StringComparison.Ordinal))
            throw new InvalidDataException("The installation-record digest does not match its canonical content.");
    }

    private void DemandRecordIntegrity(SessionInstallationRecord record)
    {
        if (record.State != SessionIntegrationState.Admitted ||
            record.ProjectionSet.Count == 0 ||
            record.ProjectionSet.Select(static item => item.LogicalPath).Distinct(StringComparer.Ordinal).Count() != record.ProjectionSet.Count ||
            record.Definition != record.Provider.Definition ||
            record.ProjectionSet.Any(item => item.ProducerIdentity != record.Provider.Adapter || item.DefinitionBinding != record.Definition))
            throw new InvalidDataException("The installation record contains an incompatible binding.");

        string setDigest = ProjectionSetDigest(record.ProjectionSet);
        if (!string.Equals(record.Publication.LiveStateDigest, setDigest, StringComparison.Ordinal) ||
            !string.Equals(record.Publication.State, "committed", StringComparison.Ordinal))
            throw new InvalidDataException("The publication live-state evidence is not exact.");

        string journalPath = LogicalPaths.ResolveInside(workspaceRoot, record.Publication.JournalLogicalPath);
        if (!File.Exists(journalPath) ||
            !string.Equals(Digests.Sha256(File.ReadAllBytes(journalPath)), record.Publication.JournalDigest, StringComparison.Ordinal))
            throw new InvalidDataException("The publication journal evidence is unavailable or drifted.");

        string receipt = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[] { record.InstallationIdentity.Digest, record.RequestIdentity, record.Publication.LiveStateDigest })));
        if (!string.Equals(receipt, record.AdmissionReceipt, StringComparison.Ordinal))
            throw new InvalidDataException("The admission receipt does not bind the installation, request, and publication.");

        string installation = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[]
        {
            record.RequestCoreIdentity,
            record.Definition.Digest,
            record.Provider.Provider.Digest,
            record.Provider.Adapter.Digest,
            record.Provider.ConformanceProfile.Digest,
            record.CliRelease.PackageDigest,
            record.CliRelease.ExecutableDigest,
            record.CliRelease.RuntimeProfile.Digest,
            setDigest,
        })));
        if (!string.Equals(installation, record.InstallationIdentity.Digest, StringComparison.Ordinal))
            throw new InvalidDataException("The installation identity does not match the admitted exact bindings.");
    }

    private static bool ProjectionBindingMatches(IReadOnlyList<SessionProjectionArtifact> recorded, SessionIntegrationCandidate expected)
    {
        SessionProjectionArtifact[] orderedRecord = recorded.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ToArray();
        ProjectedSessionArtifact[] orderedExpected = expected.Artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ToArray();
        if (orderedRecord.Length != orderedExpected.Length) return false;
        for (int index = 0; index < orderedRecord.Length; index++)
        {
            SessionProjectionArtifact record = orderedRecord[index];
            ProjectedSessionArtifact artifact = orderedExpected[index];
            if (!string.Equals(record.LogicalPath, artifact.LogicalPath, StringComparison.Ordinal) ||
                !string.Equals(record.MediaType, artifact.MediaType, StringComparison.Ordinal) ||
                !string.Equals(record.ContentDigest, Digests.Sha256(artifact.Content), StringComparison.Ordinal) ||
                record.ProducerIdentity != expected.Provider.Manifest.AdapterIdentity ||
                record.DefinitionBinding != expected.Provider.Manifest.DefinitionBinding ||
                record.Ownership != ArtifactOwnership.GeneratedOwned ||
                record.ClaimClass != ClaimClass.CanonicalByte ||
                !string.Equals(record.RemovalPolicy, "exact-admitted-digest-only", StringComparison.Ordinal))
                return false;
        }

        return true;
    }

    private static string ProjectionSetDigest(IEnumerable<SessionProjectionArtifact> artifacts) =>
        Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).Select(static artifact => $"{artifact.LogicalPath}:{artifact.ContentDigest}"))));

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
        ["canonicalProfile"] = CanonicalJson.Profile,
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
