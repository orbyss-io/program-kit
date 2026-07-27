using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>Defines the observation names and optional attachment contract required in evidence.</summary>
public sealed record TestEvidenceShape(
    ArtifactReference Schema,
    ImmutableArray<string> RequiredObservations,
    bool AllowsAttachments);
