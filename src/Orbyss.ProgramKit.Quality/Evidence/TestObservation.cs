using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Evidence;

/// <summary>Records one typed observation without embedding an untyped JSON value.</summary>
public sealed record TestObservation(
    string Name,
    string Value,
    ArtifactReference? Attachment);
