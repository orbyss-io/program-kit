using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Ownership;

/// <summary>
/// The canonical identity and owner PKID kinds for one supported artifact kind.
/// </summary>
public sealed record SupportedArtifactKindOwnership(
    SupportedArtifactKind ArtifactKind,
    ArtifactOwnershipClassification Classification,
    ImmutableArray<string> ArtifactIdentityKinds,
    ImmutableArray<string> OwnerIdentityKinds,
    string CanonicalOwnership);
