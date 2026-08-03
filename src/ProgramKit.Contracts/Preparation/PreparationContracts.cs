using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Preparation;

public sealed record PreparationRequest(
    string Schema,
    string CanonicalProfile,
    ArtifactReference RootBundle,
    GovernedIdentity WorkspaceIdentity,
    ConstructionMode ConstructionMode,
    RequestedEffect DesiredEffect,
    IReadOnlyList<ExactSelection> Selections,
    EvaluationContext EvaluationContext,
    ArtifactReference ExpectedLock);

public sealed record PreparationProposal(
    string Schema,
    string CanonicalProfile,
    string RequestBinding,
    string ClosureDigest,
    string LiveStateDigest,
    IReadOnlyList<GovernedIdentity> Subjects,
    FactoryOperation Operation,
    ConstructionMode ConstructionMode,
    RequestedEffect MaximumEffect,
    JsonObject Explanation,
    IReadOnlyList<string> AuthorityRequirements,
    JsonObject UngrantedProjection,
    IReadOnlyList<EvidenceReference> Evidence,
    string Digest);
