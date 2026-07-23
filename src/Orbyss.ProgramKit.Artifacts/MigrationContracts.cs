using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts;

/// <summary>The mechanism used to move from a source revision to a target revision.</summary>
public enum MigrationMode
{
    /// <summary>Transforms a durable artifact into a new artifact.</summary>
    ArtifactTransform,

    /// <summary>Transforms configuration into a new configuration revision.</summary>
    ConfigurationTransform,

    /// <summary>Provides source-level migration guidance.</summary>
    SourceGuidance,

    /// <summary>Regenerates an output from upgraded canonical inputs.</summary>
    Regenerate,

    /// <summary>Upgrades an exact package selection.</summary>
    PackageUpgrade,

    /// <summary>Temporarily adapts incompatible runtime revisions.</summary>
    RuntimeAdapter,
}

/// <summary>The declared data-loss behavior of a migration.</summary>
public enum MigrationLossPolicy
{
    /// <summary>The migration preserves all represented meaning.</summary>
    Lossless,

    /// <summary>Any loss is explicit, reviewed, and described by preconditions.</summary>
    ExplicitlyLossy,

    /// <summary>The migration must fail rather than lose represented meaning.</summary>
    RejectLoss,
}

/// <summary>The behavior required when a migration cannot complete.</summary>
public enum MigrationFailurePolicy
{
    /// <summary>Fail before writing a target value.</summary>
    FailBeforeWrite,

    /// <summary>Roll back target writes atomically.</summary>
    AtomicRollback,

    /// <summary>Preserve the source, reject the target, and report the failure.</summary>
    PreserveSourceAndReport,
}

/// <summary>An explicit precondition for applying a migration.</summary>
/// <param name="Code">A stable kebab-case precondition code.</param>
/// <param name="Description">A human-reviewable condition description.</param>
/// <param name="EvidenceReferences">Exact evidence required to establish the condition.</param>
public sealed record MigrationPrecondition(
    string Code,
    string Description,
    ImmutableArray<ArtifactReference> EvidenceReferences);

/// <summary>Defines one explicit, independently versioned migration.</summary>
/// <param name="SourceIdentity">The semantic identity accepted as input.</param>
/// <param name="SourceRange">The accepted source revision range.</param>
/// <param name="Target">The exact target revision.</param>
/// <param name="Mode">The migration mechanism.</param>
/// <param name="Preconditions">Ordered preconditions.</param>
/// <param name="LossPolicy">The explicit loss policy.</param>
/// <param name="IsDeterministic">Whether equal exact inputs produce equal exact outputs.</param>
/// <param name="IsIdempotent">Whether applying the migration repeatedly is safe.</param>
/// <param name="FailurePolicy">The behavior on failure.</param>
/// <param name="ImplementationReference">The exact implementation or guidance artifact.</param>
/// <param name="FixtureReferences">Positive and negative migration fixtures.</param>
public sealed record MigrationDefinition(
    ProgramKitIdentifier SourceIdentity,
    SemanticVersionRange SourceRange,
    ArtifactReference Target,
    MigrationMode Mode,
    ImmutableArray<MigrationPrecondition> Preconditions,
    MigrationLossPolicy LossPolicy,
    bool IsDeterministic,
    bool IsIdempotent,
    MigrationFailurePolicy FailurePolicy,
    ArtifactReference ImplementationReference,
    ImmutableArray<ArtifactReference> FixtureReferences);

/// <summary>The terminal disposition assigned to an impacted version node.</summary>
public enum MigrationTerminalDisposition
{
    /// <summary>The node is unaffected and carries explicit proof.</summary>
    UnaffectedWithProof,

    /// <summary>The node is compatible after all declared actions complete.</summary>
    CompatibleAfterActions,

    /// <summary>The node requires a major upgrade.</summary>
    MajorUpgrade,

    /// <summary>The node must be redesigned.</summary>
    Redesign,

    /// <summary>The node requires human semantic review.</summary>
    ManualReview,

    /// <summary>The migration cannot currently proceed.</summary>
    Blocked,
}

/// <summary>An ordered action required by a migration assessment.</summary>
public enum MigrationRequiredAction
{
    /// <summary>Repeat relevant tests.</summary>
    Retest,

    /// <summary>Regenerate derived outputs.</summary>
    Regenerate,

    /// <summary>Recompile affected source.</summary>
    Recompile,

    /// <summary>Repackage or recreate an immutable lock.</summary>
    RepackageOrRelock,

    /// <summary>Transform a durable artifact.</summary>
    MigrateArtifact,

    /// <summary>Transform configuration.</summary>
    MigrateConfiguration,

    /// <summary>Add an explicit compatibility adapter.</summary>
    AddAdapter,

    /// <summary>Drain or migrate pending work.</summary>
    DrainOrMigratePendingWork,
}

/// <summary>A retained causal path from a changed root to an impacted revision.</summary>
/// <param name="ChangedRoot">The changed root revision.</param>
/// <param name="EdgeIds">Ordered version-map edge identities.</param>
public sealed record MigrationCausalPath(
    ArtifactReference ChangedRoot,
    ImmutableArray<ProgramKitIdentifier> EdgeIds);

/// <summary>The complete terminal assessment of one reached revision.</summary>
/// <param name="Observed">The exact observed revision.</param>
/// <param name="Target">The exact target revision.</param>
/// <param name="OwnerId">The owner of the disposition.</param>
/// <param name="Disposition">The terminal disposition.</param>
/// <param name="RequiredActions">Ordered actions required by the disposition.</param>
/// <param name="RequiredEvidence">Exact evidence needed to prove the disposition.</param>
/// <param name="CausalPaths">All retained paths from changed roots.</param>
/// <param name="Rationale">A human-reviewable rationale.</param>
public sealed record MigrationImpact(
    ArtifactReference Observed,
    ArtifactReference Target,
    ProgramKitIdentifier OwnerId,
    MigrationTerminalDisposition Disposition,
    ImmutableArray<MigrationRequiredAction> RequiredActions,
    ImmutableArray<ArtifactReference> RequiredEvidence,
    ImmutableArray<MigrationCausalPath> CausalPaths,
    string Rationale);

/// <summary>An atomic migration cohort, including a strongly connected component when necessary.</summary>
/// <param name="Id">The stable cohort identity.</param>
/// <param name="Members">Exact target revisions migrated atomically.</param>
public sealed record MigrationCohort(
    ProgramKitIdentifier Id,
    ImmutableArray<ArtifactReference> Members);

/// <summary>One dependency-safe migration wave.</summary>
/// <param name="Ordinal">The zero-based wave ordinal.</param>
/// <param name="Cohorts">Atomic cohorts in deterministic order.</param>
public sealed record MigrationWave(
    int Ordinal,
    ImmutableArray<MigrationCohort> Cohorts);

/// <summary>An immutable, action-complete migration impact assessment.</summary>
/// <param name="VersionMapReference">The exact immutable version map.</param>
/// <param name="VersionSelectionReference">The exact immutable selection.</param>
/// <param name="ChangedRevisions">All changed root revisions.</param>
/// <param name="Impacts">One terminal impact per reached revision.</param>
/// <param name="Waves">Dependency-safe migration waves.</param>
public sealed record MigrationAssessment(
    ArtifactReference VersionMapReference,
    ArtifactReference VersionSelectionReference,
    ImmutableArray<ArtifactReference> ChangedRevisions,
    ImmutableArray<MigrationImpact> Impacts,
    ImmutableArray<MigrationWave> Waves);
