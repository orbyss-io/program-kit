using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Resolution;

public sealed record ResolvedItem(string Role, GovernedIdentity Identity, ArtifactReference Artifact, string Availability);

public sealed record ResolvedRelationship(
    GovernedIdentity Assertion,
    GovernedIdentity From,
    GovernedIdentity To,
    string Status,
    GovernedIdentity Contract,
    GovernedIdentity? Mapping,
    IReadOnlyList<TraceReference> Trace);

public sealed record ResolutionLock(
    string Schema,
    string CanonicalProfile,
    GovernedIdentity Identity,
    string RequestDigest,
    ArtifactReference RootBundle,
    IReadOnlyList<ResolvedItem> ResolvedItems,
    IReadOnlyList<ResolvedRelationship> Relationships,
    IReadOnlyList<ExactSelection> Providers,
    IReadOnlyList<GovernedIdentity> Profiles,
    string ClosureDigest,
    string? ConstructionIdentity,
    JsonObject CanonicalDocument);

public sealed record IntegrationResolutionExplanation(
    string Schema,
    string CanonicalProfile,
    string RequestDigest,
    string LockDigest,
    GovernedIdentity Root,
    IReadOnlyList<JsonObject> SemanticCoverage,
    IReadOnlyList<JsonObject> Relationships,
    IReadOnlyList<JsonObject> Selections,
    IReadOnlyList<JsonObject> Seams,
    IReadOnlyList<JsonObject> ArtifactPlan,
    IReadOnlyList<JsonObject> Gates,
    IReadOnlyList<JsonObject> Evidence,
    IReadOnlyList<JsonObject> Blockers,
    IReadOnlyList<JsonObject> Trace,
    JsonObject CanonicalDocument);
