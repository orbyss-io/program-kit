using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

public sealed record SessionProviderConformanceProfile(
    GovernedIdentity Identity,
    IReadOnlyList<string> RequiredOperations,
    IReadOnlyList<string> RequiredScopes,
    string ResultSchema,
    bool RequireGeneratedOwnership,
    bool RequireCleanStructuredResult,
    bool RequireAuthorityPreservation,
    bool RequireDisclosurePreservation,
    bool RequireFreshSessionClassification);

public sealed record SessionProviderConformanceFailure(string Code, string Subject, string Expected, string Observed);

public sealed record SessionProviderConformanceReport(
    bool Conforms,
    string Profile,
    string NormalizedInputDigest,
    string ObservationDigest,
    IReadOnlyList<SessionProviderConformanceFailure> Failures);

public sealed record SessionSemanticObservation(
    string Channel,
    PublicCommand Command,
    OperationOutcome Outcome,
    EffectState EffectState,
    PrimaryDisposition PrimaryDisposition,
    string ResultSchema,
    bool AuthorityPreserved,
    bool DisclosurePreserved,
    bool WorkingScopePreserved,
    bool FreshSessionClassified);

public static class SessionProviderConformanceProfiles
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public static SessionProviderConformanceProfile RepositoryWorkspaceV1 { get; } = new(
        new GovernedIdentity("orbyss.program-kit", "session-provider-conformance", "repository-workspace-v1", "1.0.0", EmptyDigest),
        new[] { "explain", "construct", "evaluate", "session-explain", "session-install", "session-verify", "session-remove" },
        new[] { "workspace" },
        "program-kit.operation-result/v1",
        true,
        true,
        true,
        true,
        true);
}
