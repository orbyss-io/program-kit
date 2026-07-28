using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>An explicit proposed revision checked by the selected alpha policy.</summary>
/// <param name="Identity">Stable Program Kit-owned governed identity.</param>
/// <param name="Intent">Explicit version intent; must be owned-artifact revision.</param>
/// <param name="CurrentVersion">Current exact revision, or null for a new identity.</param>
/// <param name="CurrentDigest">Current exact digest, or null for a new identity.</param>
/// <param name="CurrentOrdinal">Current revision ordinal, or null for a new identity.</param>
/// <param name="ProposedVersion">Human- or caller-selected proposed revision.</param>
/// <param name="ProposedDigest">Digest of the proposed canonical bytes.</param>
/// <param name="CanonicalBytesChanged">Whether canonical bytes differ from current.</param>
/// <param name="CompatibilityDisposition">Explicit compatibility classification.</param>
/// <param name="MigrationDisposition">Explicit migration classification.</param>
/// <param name="MigrationReferences">Exact required migration definitions.</param>
/// <param name="Rationale">Non-empty classification rationale.</param>
public sealed record AlphaVersionProgressionProposal(
    ProgramKitIdentifier Identity,
    VersionIntent Intent,
    SemanticVersion? CurrentVersion,
    Sha256Digest? CurrentDigest,
    int? CurrentOrdinal,
    SemanticVersion ProposedVersion,
    Sha256Digest ProposedDigest,
    bool CanonicalBytesChanged,
    VersionCompatibilityDisposition CompatibilityDisposition,
    VersionMigrationDisposition MigrationDisposition,
    ImmutableArray<ArtifactReference> MigrationReferences,
    string Rationale);
