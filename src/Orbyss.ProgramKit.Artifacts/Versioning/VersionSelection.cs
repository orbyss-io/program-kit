using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Binds one observed revision to one human-selected target revision.</summary>
/// <param name="Identity">The selected semantic identity.</param>
/// <param name="Observed">The exact observed revision.</param>
/// <param name="Target">The exact target revision.</param>
/// <param name="OwnerId">The owner responsible for the selection.</param>
public sealed record VersionSelection(
    ProgramKitIdentifier Identity,
    ArtifactReference Observed,
    ArtifactReference Target,
    ProgramKitIdentifier OwnerId);
