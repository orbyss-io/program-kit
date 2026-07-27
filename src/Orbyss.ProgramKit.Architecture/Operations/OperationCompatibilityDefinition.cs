using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

/// <summary>The compatibility dimensions exposed by an operation.</summary>
public sealed record OperationCompatibilityDefinition(
    ImmutableArray<CompatibilityDimension> Dimensions,
    string ChangePolicy,
    ImmutableArray<ArtifactReference> MigrationReferences);
