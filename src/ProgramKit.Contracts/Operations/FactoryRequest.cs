using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;

namespace Orbyss.ProgramKit.Contracts.Operations;

public enum FactoryOperation
{
    Explain,
    Construct,
    Evaluate,
}

public enum ConstructionMode
{
    New,
    Repair,
}

public enum RequestedEffect
{
    None,
    CandidateOnly,
    Committed,
}

public sealed record ExpectedState(string ClosureDigest, string LiveStateDigest);

public sealed record FactoryRequest(
    string Schema,
    string CanonicalProfile,
    FactoryOperation Operation,
    ConstructionMode? ConstructionMode,
    ArtifactReference RootBundle,
    GovernedIdentity WorkspaceIdentity,
    EvaluationContext EvaluationContext,
    RequestedEffect RequestedEffect,
    IReadOnlyList<ExactSelection> Selections,
    ArtifactReference? AuthorityGrant,
    ExpectedState? ExpectedState,
    ArtifactReference? Continuation);
