namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Human-supplied binding semantics for one exact alpha.4 work-unit ID.
/// </summary>
public sealed record PlanWorkUnitAlpha5Binding(
    string WorkUnitId,
    PlanArtifactBinding? ActivationMatrix,
    PlanArtifactBinding? VerificationProfile);
