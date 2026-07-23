using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>An explicit precondition for applying a migration.</summary>
/// <param name="Code">A stable kebab-case precondition code.</param>
/// <param name="Description">A human-reviewable condition description.</param>
/// <param name="EvidenceReferences">Exact evidence required to establish the condition.</param>
public sealed record MigrationPrecondition(
    string Code,
    string Description,
    ImmutableArray<ArtifactReference> EvidenceReferences);
