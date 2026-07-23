using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Envelopes;

/// <summary>Identifies and classifies the enveloped artifact.</summary>
/// <param name="Id">The stable artifact identity.</param>
/// <param name="Kind">The canonical kebab-case artifact kind.</param>
/// <param name="Version">The artifact's independent version.</param>
/// <param name="OwnerId">The stable owner identity.</param>
/// <param name="Status">The truthful implementation status.</param>
/// <param name="Consumers">Explicit known consumers.</param>
public sealed record ArtifactIdentity(
    ProgramKitIdentifier Id,
    string Kind,
    SemanticVersion Version,
    ProgramKitIdentifier OwnerId,
    ArtifactStatus Status,
    ImmutableArray<ProgramKitIdentifier> Consumers);
