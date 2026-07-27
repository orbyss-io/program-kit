using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>
/// Carries a human-supplied decision. Program Kit validates this record but never creates the
/// principal, authority, evidence, decision, correlation, or decision time.
/// </summary>
public sealed record DesignPlanApprovalRecord(
    ArtifactReference Design,
    ArtifactReference Plan,
    string AcceptedScope,
    PrincipalReference ApprovingPrincipal,
    AuthorityReference Authority,
    ImmutableArray<HumanDecisionEvidence> DecisionEvidence,
    string CorrelationId,
    DateTimeOffset DecisionTime,
    DesignPlanApprovalDecision Decision,
    ImmutableArray<ApprovalCondition> Conditions,
    ApprovalSupersession Supersession);
