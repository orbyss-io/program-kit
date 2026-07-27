using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

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
