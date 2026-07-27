using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Human-supplied v3 classification for one exact v2 work-unit ID.</summary>
public sealed record PlanWorkUnitV3Binding(
    string WorkUnitId,
    PlanWorkUnitKind WorkUnitKind,
    ArtifactReference? ActivationMatrix,
    ArtifactReference? VerificationProfile);
