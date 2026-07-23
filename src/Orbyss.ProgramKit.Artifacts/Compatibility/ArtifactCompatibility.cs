using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Compatibility;

/// <summary>Declares compatibility ranges, dimensions, and migration references.</summary>
/// <param name="Policy">The identity of the applied compatibility policy.</param>
/// <param name="Dimensions">Exactly one claim per classified dimension.</param>
/// <param name="ReaderRange">Versions whose representations can be read.</param>
/// <param name="WriterRange">Versions whose representations may be written.</param>
/// <param name="MigrationReferences">Explicit migration definitions.</param>
public sealed record ArtifactCompatibility(
    ProgramKitIdentifier Policy,
    ImmutableArray<CompatibilityClaim> Dimensions,
    SemanticVersionRange ReaderRange,
    SemanticVersionRange WriterRange,
    ImmutableArray<ArtifactReference> MigrationReferences);
