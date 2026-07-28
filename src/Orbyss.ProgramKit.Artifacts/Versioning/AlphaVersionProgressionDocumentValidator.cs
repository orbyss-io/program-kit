using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Validates structural semantics of a policy-bound alpha proposal.</summary>
public sealed class AlphaVersionProgressionDocumentValidator :
    IProgramKitSemanticValidator<AlphaVersionProgressionDocument>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(AlphaVersionProgressionDocument value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "An alpha version progression document is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        ValidatePolicy(value.Policy, diagnostics);
        ValidateProposal(value.Proposal, diagnostics);
        return diagnostics.ToResult();
    }

    private static void ValidatePolicy(
        AlphaVersionProgressionPolicy policy,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (policy is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "An exact replaceable progression policy is required.",
                "/policy");
            return;
        }

        diagnostics.Add(ArtifactReferenceValidator.Validate(
            policy.PolicyRevision,
            "/policy/policyRevision"));
        if (policy.PolicyRevision is not null &&
            !string.Equals(
                policy.PolicyRevision.Identity.Kind,
                "policy",
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "The selected policy revision must have PKID kind 'policy'.",
                "/policy/policyRevision/identity");
        }

        diagnostics.Add(SemanticVersion.Validate(
            policy.CoreVersion.Value,
            "/policy/coreVersion"));
        var coreVersion = policy.CoreVersion.Value ?? string.Empty;
        if (coreVersion.Contains('-') ||
            coreVersion.Contains('+'))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "The policy core version cannot contain prerelease or build text.",
                "/policy/coreVersion");
        }

        if (!ArtifactValidationText.IsKebabCase(policy.PrereleaseLabel))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "The prerelease label must be lowercase kebab case.",
                "/policy/prereleaseLabel");
        }

        if (policy.InitialOrdinal <= 0 || policy.OrdinalStep <= 0)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "Initial ordinal and ordinal step must be positive.",
                "/policy");
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(
            policy.ReplacementPolicyContract.Value,
            "/policy/replacementPolicyContract"));
        if (!string.Equals(
                policy.ReplacementPolicyContract.Kind,
                "contract",
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "The replacement-policy identity must have PKID kind 'contract'.",
                "/policy/replacementPolicyContract");
        }
    }

    private static void ValidateProposal(
        AlphaVersionProgressionProposal proposal,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (proposal is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "An explicit progression proposal is required.",
                "/proposal");
            return;
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(
            proposal.Identity.Value,
            "/proposal/identity"));
        diagnostics.Add(SemanticVersion.Validate(
            proposal.ProposedVersion.Value,
            "/proposal/proposedVersion"));
        diagnostics.Add(Sha256Digest.Validate(
            proposal.ProposedDigest.Value,
            "/proposal/proposedDigest"));
        if (!Enum.IsDefined(proposal.Intent) ||
            !Enum.IsDefined(proposal.CompatibilityDisposition) ||
            !Enum.IsDefined(proposal.MigrationDisposition) ||
            string.IsNullOrWhiteSpace(proposal.Rationale))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "Proposal intent, dispositions, and rationale must be explicit.",
                "/proposal");
        }

        var hasCurrentVersion = proposal.CurrentVersion is not null;
        var hasCurrentDigest = proposal.CurrentDigest is not null;
        var hasCurrentOrdinal = proposal.CurrentOrdinal is not null;
        if (hasCurrentVersion != hasCurrentDigest ||
            hasCurrentVersion != hasCurrentOrdinal)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "Current version, digest, and ordinal must be supplied together or all omitted.",
                "/proposal");
        }

        if (proposal.CurrentVersion is not null)
        {
            diagnostics.Add(SemanticVersion.Validate(
                proposal.CurrentVersion.Value.Value,
                "/proposal/currentVersion"));
        }

        if (proposal.CurrentDigest is not null)
        {
            diagnostics.Add(Sha256Digest.Validate(
                proposal.CurrentDigest.Value.Value,
                "/proposal/currentDigest"));
        }

        if (proposal.CurrentOrdinal is <= 0)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
                "A supplied current ordinal must be positive.",
                "/proposal/currentOrdinal");
        }

        DefaultArtifactEnvelopeValidator.ValidateReferences(
            proposal.MigrationReferences,
            "/proposal/migrationReferences",
            expectedKind: "migration",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
            diagnostics);
    }
}
