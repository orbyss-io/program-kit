namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Selects one exact consumer-owned gate and its exact activation matrix.</summary>
public sealed record StaticConformanceGateSelection(
    ArtifactReference Gate,
    ArtifactReference ActivationMatrix);
