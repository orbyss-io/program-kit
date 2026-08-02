using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed class ExplainSessionIntegrationOperation
{
    private readonly SessionIntegrationServices services;

    public ExplainSessionIntegrationOperation(SessionIntegrationServices services)
    {
        this.services = services;
    }

    public OperationResult Execute(string workspaceRoot, string requestPath)
    {
        services.SourceGuard.DemandConsumerWorkspace(workspaceRoot);
        SessionIntegrationCandidate candidate = new SessionIntegrationCandidateBuilder(services).Build(workspaceRoot, requestPath, SessionLifecycleOperation.Explain);
        JsonObject session = SessionPayload.Candidate(candidate, "absent", "not-evaluated");
        session["authorityRequiredFor"] = "session-install";
        session["authorityRequestBinding"] = candidate.RequestCoreIdentity;
        return OperationResultFactory.Success(
            PublicCommand.SessionExplain,
            OperationPhase.Explanation,
            EffectState.None,
            candidate.RequestIdentity,
            session: session,
            disclosure: SessionPayload.Disclosure,
            artifacts: candidate.Artifacts.Select(artifact => SessionPayload.Reference(candidate, artifact)).ToArray());
    }
}

internal static class SessionPayload
{
    public static readonly DisclosureEntry[] Disclosure =
    {
        new("workspace", DisclosureClassification.RepositoryRelative, "absolute path withheld"),
        new("provider", DisclosureClassification.Public, "exact identity reported"),
        new("cliRelease", DisclosureClassification.Public, "package identity reported"),
    };

    public static JsonObject Candidate(SessionIntegrationCandidate candidate, string state, string availability) => new()
    {
        ["state"] = state,
        ["sessionAvailability"] = availability,
        ["provider"] = candidate.Provider.Manifest.ProviderIdentity.StableKey,
        ["adapter"] = candidate.Provider.Manifest.AdapterIdentity.StableKey,
        ["definition"] = candidate.Provider.Manifest.DefinitionBinding.StableKey,
        ["scope"] = candidate.Request.Scope,
        ["cliRelease"] = candidate.Request.CliRelease.PackageVersion,
        ["requestCoreIdentity"] = candidate.RequestCoreIdentity,
        ["requestIdentity"] = candidate.RequestIdentity,
        ["expectedInstallationState"] = candidate.ExpectedLiveState,
        ["candidateSetDigest"] = candidate.SetDigest,
        ["installationIdentity"] = candidate.InstallationIdentity,
        ["projections"] = new JsonArray(candidate.Artifacts.Select(artifact => new JsonObject
        {
            ["logicalPath"] = artifact.LogicalPath,
            ["mediaType"] = artifact.MediaType,
            ["digest"] = Digests.Sha256(artifact.Content),
            ["ownership"] = "generated-owned",
        }).ToArray()),
    };

    public static ArtifactReference Reference(SessionIntegrationCandidate candidate, Providers.ProjectedSessionArtifact artifact) => new(
        new Contracts.Identity.GovernedIdentity("orbyss.program-kit", "session-projection", artifact.LogicalPath, candidate.Provider.Manifest.Revision, Digests.Sha256(artifact.Content)),
        artifact.MediaType, artifact.LogicalPath, Digests.Sha256(artifact.Content), ArtifactOwnership.GeneratedOwned);
}
