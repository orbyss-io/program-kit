using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Quality;

namespace Orbyss.ProgramKit.Planning;

/// <summary>Identifies the lifecycle state of an implementation plan without implying human approval.</summary>
public enum ImplementationPlanState
{
    /// <summary>The plan remains under construction.</summary>
    Draft,
    /// <summary>The plan is complete enough for an explicit human decision.</summary>
    ReadyForHumanDecision,
    /// <summary>A later plan revision has replaced this plan.</summary>
    Superseded,
}

/// <summary>Defines one source-controlled or external dependency consumed by a work unit.</summary>
public sealed record PlanDependency(
    ArtifactReference Artifact,
    string Purpose);

/// <summary>Defines one compatibility expectation evaluated by a work unit.</summary>
public sealed record PlanCompatibilityRequirement(
    ProgramKitIdentifier SubjectId,
    SemanticVersionRange AcceptedVersions,
    string ExpectedDisposition);

/// <summary>Defines a process invocation as an executable plus already-tokenized arguments.</summary>
public sealed record PlanVerificationCommand(
    string Executable,
    ImmutableArray<string> Arguments,
    string WorkingDirectory,
    string ExpectedObservation);

/// <summary>Defines one bounded and independently verifiable implementation unit.</summary>
public sealed record PlanWorkUnit(
    string WorkUnitId,
    string RequiredOutcome,
    int Sequence,
    string? ParallelGroupId,
    ImmutableArray<string> DependsOn,
    ImmutableArray<ArtifactReference> Inputs,
    ImmutableArray<ArtifactReference> Outputs,
    ImmutableArray<string> AllowedEdits,
    ImmutableArray<PlanDependency> SourceDependencies,
    ImmutableArray<PlanDependency> ExternalDependencies,
    ImmutableArray<ArtifactReference> Migrations,
    ImmutableArray<PlanCompatibilityRequirement> Compatibility,
    ImmutableArray<string> StopConditions,
    ImmutableArray<PlanVerificationCommand> Verification,
    ImmutableArray<TestSpecificationSelection> SelectedTests);

/// <summary>Names work units that may run concurrently after their external dependencies are satisfied.</summary>
public sealed record PlanParallelGroup(
    string ParallelGroupId,
    ImmutableArray<string> WorkUnitIds);

/// <summary>Records an unresolved human or external decision without silently choosing an answer.</summary>
public sealed record PlanUnresolvedDecision(
    string DecisionId,
    string Question,
    bool BlocksImplementation);

/// <summary>Provides the required end-to-end trace for one design requirement.</summary>
public sealed record RequirementTrace(
    string RequirementId,
    ProgramKitIdentifier OwnerId,
    ArtifactReference ContractOrArtifact,
    ImmutableArray<string> WorkUnitIds,
    string ImplementationOutcome,
    ImmutableArray<ArtifactReference> DependencyOrExtensionImpact,
    ImmutableArray<TestSpecificationSelection> Tests,
    ImmutableArray<ArtifactReference> Evidence,
    string ObservableAcceptanceOutcome);

/// <summary>
/// Describes implementation separately from, and by exact reference to, its source design.
/// </summary>
public sealed record ImplementationPlanDocument(
    ArtifactReference Design,
    ProgramKitIdentifier OwnerId,
    ImplementationPlanState State,
    ImmutableArray<string> RequirementIds,
    ImmutableArray<PlanWorkUnit> WorkUnits,
    ImmutableArray<PlanParallelGroup> ParallelGroups,
    ImmutableArray<RequirementTrace> Trace,
    ImmutableArray<PlanUnresolvedDecision> UnresolvedDecisions);

/// <summary>Identifies a principal supplied by the human-session boundary.</summary>
public sealed record PrincipalReference(
    string Kind,
    string Provider,
    string Identifier,
    string Role);

/// <summary>Identifies the exact source of authority asserted by a supplied human decision.</summary>
public sealed record AuthorityReference(
    string Kind,
    ArtifactReference Source,
    string JsonPointer,
    ProgramKitIdentifier OwnerId);

/// <summary>References evidence supplied with a human decision.</summary>
public sealed record HumanDecisionEvidence(
    string Kind,
    string Provider,
    string ReferenceId,
    Sha256Digest? Digest);

/// <summary>Identifies the only decisions accepted by the design/plan approval contract.</summary>
public enum DesignPlanApprovalDecision
{
    /// <summary>The human approved the exact design and plan.</summary>
    Approved,
    /// <summary>The human rejected the exact design and plan.</summary>
    Rejected,
    /// <summary>The human requires changes before approval.</summary>
    ChangesRequired,
}

/// <summary>Identifies the state of one explicitly supplied approval condition.</summary>
public enum ApprovalConditionState
{
    /// <summary>The condition remains unresolved.</summary>
    Open,
    /// <summary>The condition has been satisfied with evidence.</summary>
    Satisfied,
    /// <summary>The condition was explicitly waived with evidence.</summary>
    Waived,
}

/// <summary>Records one approval condition and the evidence used to close it, when applicable.</summary>
public sealed record ApprovalCondition(
    string ConditionId,
    string Description,
    ApprovalConditionState State,
    ArtifactReference? ResolutionEvidence);

/// <summary>Identifies whether an approval record remains active.</summary>
public enum ApprovalSupersessionState
{
    /// <summary>The approval remains the active decision for its exact inputs.</summary>
    Active,
    /// <summary>A later approval record supersedes this record.</summary>
    Superseded,
}

/// <summary>Records explicit approval supersession without mutating the prior decision.</summary>
public sealed record ApprovalSupersession(
    ApprovalSupersessionState State,
    ArtifactReference? SupersededBy);

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
