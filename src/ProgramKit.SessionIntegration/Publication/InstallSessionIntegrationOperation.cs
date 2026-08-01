using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed class InstallSessionIntegrationOperation
{
    private readonly SessionIntegrationServices services;

    public InstallSessionIntegrationOperation(SessionIntegrationServices services)
    {
        this.services = services;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        services.SourceGuard.DemandConsumerWorkspace(workspaceRoot);
        SessionIntegrationCandidate candidate = new SessionIntegrationCandidateBuilder(services).Build(workspaceRoot, requestPath, SessionLifecycleOperation.Install);
        SessionInstallationStore store = new(workspaceRoot, candidate.Provider.Manifest.ProviderIdentity.Name);
        SessionInstallationInspection existing = store.Inspect();
        if (existing.State == SessionIntegrationState.Exact && string.Equals(existing.Record?.RequestCoreIdentity, candidate.RequestCoreIdentity, StringComparison.Ordinal))
            return OperationResultFactory.Success(PublicCommand.SessionInstall, OperationPhase.Completion, EffectState.Committed, candidate.RequestIdentity, session: SessionPayload.Candidate(candidate, "exact", Kebab(existing.SessionAvailability)), disclosure: SessionPayload.Disclosure);

        RequestBoundAuthorityGrant grant = LoadGrant(workspaceRoot, candidate, store);
        services.Authority.Demand(new AuthorityDemand(
            candidate.Request.Workspace.Identity.StableKey, "session-install", RequestedEffect.Committed, candidate.RequestCoreIdentity,
            candidate.Provider.Manifest.ProviderIdentity.StableKey, candidate.Request.Scope, candidate.Request.EvaluationContext.Instant), grant);

        NamespacedArtifact[] publications = candidate.Artifacts.Select(static artifact => new NamespacedArtifact(artifact.LogicalPath, artifact.Content)).ToArray();
        NamespacedPublicationResult publication = services.Publisher.Publish(workspaceRoot, $"session-integrations/{candidate.Provider.Manifest.ProviderIdentity.Name}", candidate.InstallationIdentity, publications);
        SessionProjectionArtifact[] projectionSet = candidate.Artifacts.Select(artifact => new SessionProjectionArtifact(
            artifact.LogicalPath, artifact.MediaType, ArtifactOwnership.GeneratedOwned, candidate.Provider.Manifest.AdapterIdentity, candidate.Provider.Manifest.DefinitionBinding,
            Digests.Sha256(artifact.Content), ClaimClass.CanonicalByte, "exact-admitted-digest-only")).ToArray();
        string receipt = Digests.Sha256(Encoding.UTF8.GetBytes($"{candidate.InstallationIdentity}\n{candidate.RequestIdentity}\n{publication.LiveStateDigest}"));
        SessionInstallationRecord record = new(
            "program-kit.session-installation-record/v1",
            new GovernedIdentity("orbyss.program-kit", "session-installation", candidate.Provider.Manifest.ProviderIdentity.Name, candidate.Provider.Manifest.Revision, candidate.InstallationIdentity),
            candidate.RequestIdentity, candidate.RequestCoreIdentity, candidate.Request.Workspace, candidate.Request.Scope, candidate.Provider.Manifest.DefinitionBinding,
            candidate.Request.ProviderSelection, candidate.Request.CliRelease, projectionSet,
            new SessionPublicationEvidence(publication.JournalLogicalPath, publication.JournalDigest, publication.LiveStateDigest, "committed"),
            SessionIntegrationState.Admitted, SessionAvailability.ReloadRequired, receipt, $"sha256:{new string('0', 64)}");
        store.Admit(record);
        store.MarkGrantConsumed(grant.GrantIdentity, candidate.RequestIdentity);

        JsonObject session = SessionPayload.Candidate(candidate, "exact", "reload-required");
        session["installationRecord"] = store.RecordLogicalPath;
        session["admissionReceipt"] = receipt;
        return OperationResultFactory.Success(
            PublicCommand.SessionInstall, OperationPhase.Completion, EffectState.Committed, candidate.RequestIdentity, candidate.InstallationIdentity,
            session: session, disclosure: SessionPayload.Disclosure, artifacts: candidate.Artifacts.Select(artifact => SessionPayload.Reference(candidate, artifact)).ToArray(), changes: publication.Changes);
    }

    private static RequestBoundAuthorityGrant LoadGrant(string workspaceRoot, SessionIntegrationCandidate candidate, SessionInstallationStore store)
    {
        if (candidate.AuthorityGrantLogicalPath is null) throw new UnauthorizedAccessException("The installation request has no exact authority grant reference.");
        string grantPath = LogicalPaths.ResolveInside(workspaceRoot, candidate.AuthorityGrantLogicalPath);
        if (!File.Exists(grantPath)) throw new UnauthorizedAccessException("The exact authority grant artifact is unavailable.");
        JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(grantPath)).AsObject();
        GovernedIdentity identity = ParseIdentity(document["identity"]!.AsObject());
        string operation = document["operations"]!.AsArray().Select(static value => value!.GetValue<string>()).Single();
        string effect = document["effects"]!.AsArray().Select(static value => value!.GetValue<string>()).Single();
        string provider = Condition(document, "provider");
        string scope = Condition(document, "scope");
        JsonObject validity = document["validity"]!.AsObject();
        return new RequestBoundAuthorityGrant(
            "program-kit.request-bound-authority-grant/v1", identity.StableKey, candidate.Request.Workspace.Identity.StableKey, operation, effect,
            document["requestBinding"]!.GetValue<string>(), provider, scope,
            ParseInstant(validity["notBefore"]!.GetValue<string>()), ParseInstant(validity["notAfter"]!.GetValue<string>()), false, store.IsGrantConsumed(identity.StableKey));
    }

    private static string Condition(JsonObject grant, string kind) => grant["conditions"]!.AsArray().Select(static value => value!.AsObject()).Single(item => string.Equals(item["kind"]!.GetValue<string>(), kind, StringComparison.Ordinal))["value"]!["value"]!.GetValue<string>();
    private static DateTimeOffset ParseInstant(string value) => DateTimeOffset.ParseExact(value, "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
    private static GovernedIdentity ParseIdentity(JsonObject value) => new(value["authority"]!.GetValue<string>(), value["kind"]!.GetValue<string>(), value["name"]!.GetValue<string>(), value["revision"]!.GetValue<string>(), value["digest"]!.GetValue<string>());
    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
