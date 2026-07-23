using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>An exact artifact and location from which a semantic claim was derived.</summary>
public sealed record SourceTrace(
    ArtifactReference Artifact,
    string Path);
