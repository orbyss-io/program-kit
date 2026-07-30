using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Resolves one approved binding without changing plan scope or authority.
/// </summary>
public static class PlanArtifactBindingResolver
{
    /// <summary>
    /// Produces exact execution evidence only when the selected artifact
    /// satisfies the complete approved binding.
    /// </summary>
    public static PlanArtifactBindingResolution Resolve(
        PlanArtifactBinding? binding,
        ArtifactReference? selectedArtifact,
        ArtifactReference? compatibilityEvidence)
    {
        if (binding is null || selectedArtifact is null)
        {
            return Blocked(
                "An approved binding and exact selected artifact are required.");
        }

        return binding.ResolutionMode switch
        {
            PlanArtifactBindingResolutionMode.ApprovalFixed =>
                ResolveApprovalFixed(
                    binding,
                    selectedArtifact,
                    compatibilityEvidence),
            PlanArtifactBindingResolutionMode.ExecutionResolved =>
                ResolveExecutionResolved(
                    binding,
                    selectedArtifact,
                    compatibilityEvidence),
            _ => Blocked("The binding resolution mode is undefined."),
        };
    }

    private static PlanArtifactBindingResolution ResolveApprovalFixed(
        PlanArtifactBinding binding,
        ArtifactReference selectedArtifact,
        ArtifactReference? compatibilityEvidence)
    {
        if (binding.ApprovedArtifact is null ||
            binding.ApprovedIdentity is not null ||
            binding.AcceptedVersions is not null ||
            binding.CompatibilityPolicy is not null)
        {
            return Blocked(
                "An approval-fixed binding must contain only one exact approved artifact.");
        }

        if (compatibilityEvidence is not null)
        {
            return Blocked(
                "An approval-fixed binding cannot accept compatibility evidence.");
        }

        if (binding.ApprovedArtifact != selectedArtifact)
        {
            return Blocked(
                "The selected artifact does not match the exact human-approved artifact.");
        }

        return Resolved(binding, selectedArtifact, null);
    }

    private static PlanArtifactBindingResolution ResolveExecutionResolved(
        PlanArtifactBinding binding,
        ArtifactReference selectedArtifact,
        ArtifactReference? compatibilityEvidence)
    {
        if (binding.ApprovedArtifact is not null ||
            binding.ApprovedIdentity is null ||
            binding.AcceptedVersions is null ||
            binding.CompatibilityPolicy is null)
        {
            return Blocked(
                "An execution-resolved binding requires approved identity, accepted versions, and exact compatibility policy.");
        }

        if (selectedArtifact.Identity != binding.ApprovedIdentity.Value)
        {
            return Blocked(
                "The selected artifact identity differs from the human-approved identity.");
        }

        if (!binding.AcceptedVersions.Value.Contains(selectedArtifact.Version))
        {
            return Blocked(
                "The selected artifact version is outside the human-approved compatibility range.");
        }

        if (compatibilityEvidence != binding.CompatibilityPolicy)
        {
            return Blocked(
                "The exact approved compatibility-policy evidence is required.");
        }

        return Resolved(binding, selectedArtifact, compatibilityEvidence);
    }

    private static PlanArtifactBindingResolution Resolved(
        PlanArtifactBinding binding,
        ArtifactReference selectedArtifact,
        ArtifactReference? compatibilityEvidence) =>
        new(
            new PlanArtifactBindingReceipt(
                binding,
                selectedArtifact,
                compatibilityEvidence),
            []);

    private static PlanArtifactBindingResolution Blocked(string reason) =>
        new(null, [reason]);
}
