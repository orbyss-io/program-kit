using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Defines one source-controlled or external dependency consumed by a work unit.</summary>
public sealed record PlanDependency(
    ArtifactReference Artifact,
    string Purpose);
