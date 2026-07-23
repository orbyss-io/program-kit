using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Binds an exact specification to an exact execution profile.</summary>
public sealed record TestSpecificationSelection(
    ArtifactReference Specification,
    ProfileReference Profile);
