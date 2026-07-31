using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Exact deterministic evidence for one approved binding resolution.
/// </summary>
public sealed record PlanArtifactBindingReceipt(
    PlanArtifactBinding ApprovedBinding,
    ArtifactReference SelectedArtifact,
    ArtifactReference? CompatibilityEvidence);
