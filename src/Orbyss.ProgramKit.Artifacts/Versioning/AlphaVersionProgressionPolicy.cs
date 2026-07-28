namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Replaceable mechanics for validating pre-stable ordinal proposals.</summary>
/// <param name="PolicyRevision">Exact selected policy revision.</param>
/// <param name="CoreVersion">SemVer core shared by policy-produced text.</param>
/// <param name="PrereleaseLabel">Prerelease label placed before the ordinal.</param>
/// <param name="InitialOrdinal">First ordinal for a new identity.</param>
/// <param name="OrdinalStep">Required ordinal increment for changed bytes.</param>
/// <param name="ReplacementPolicyContract">Contract used to replace this policy.</param>
public sealed record AlphaVersionProgressionPolicy(
    ArtifactReference PolicyRevision,
    SemanticVersion CoreVersion,
    string PrereleaseLabel,
    int InitialOrdinal,
    int OrdinalStep,
    ProgramKitIdentifier ReplacementPolicyContract);
