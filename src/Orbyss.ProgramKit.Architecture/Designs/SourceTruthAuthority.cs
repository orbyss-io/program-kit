using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>An exact source that has authority over part of a design.</summary>
public sealed record SourceTruthAuthority(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ArtifactReference Source,
    string SourcePath,
    string Governs);
