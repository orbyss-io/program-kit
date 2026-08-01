using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;

namespace Orbyss.ProgramKit.Contracts.Operations;

public enum ArtifactOwnership
{
    GeneratedOwned,
    SeededHandoff,
    ConsumerOwned,
}

public enum ClaimClass
{
    CanonicalByte,
    VerifiedEquivalent,
    CustomBounded,
}

public sealed record ArtifactReference(
    GovernedIdentity Identity,
    string MediaType,
    string LogicalPath,
    string Digest,
    ArtifactOwnership Ownership);

public sealed record TraceReference(
    ArtifactReference Source,
    string DocumentPointer,
    string ClaimKind);

public sealed record ExactSelection(
    string Role,
    GovernedIdentity Selected,
    GovernedIdentity SelectionAuthority,
    TraceReference? Trace = null);

public sealed record EvaluationContext(
    DateTimeOffset Instant,
    GovernedIdentity Source,
    string Assurance);

public sealed record EvidenceReference(
    GovernedIdentity Identity,
    GovernedIdentity Subject,
    GovernedIdentity Profile,
    ArtifactReference Artifact,
    string Freshness);

public sealed record GateResult(
    GovernedIdentity Gate,
    string Mode,
    string Status,
    IReadOnlyList<GovernedIdentity> Subjects,
    IReadOnlyList<EvidenceReference> Evidence,
    IReadOnlyList<string> DiagnosticIds);
