using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Ownership;

/// <summary>Resolves canonical ownership rules for supported artifact kinds.</summary>
public interface ISupportedArtifactKindOwnershipResolver
{
    /// <summary>Gets all rules in supported-kind declaration order.</summary>
    ImmutableArray<SupportedArtifactKindOwnership> All { get; }

    /// <summary>Resolves the canonical ownership rule for a supported kind.</summary>
    SupportedArtifactKindOwnership Resolve(SupportedArtifactKind artifactKind);

    /// <summary>Returns whether an artifact identity kind is valid for the supported kind.</summary>
    bool SupportsArtifactIdentity(
        SupportedArtifactKind artifactKind,
        string identityKind);

    /// <summary>Returns whether an owner identity kind is valid for the supported kind.</summary>
    bool SupportsOwnerIdentity(
        SupportedArtifactKind artifactKind,
        string ownerKind);
}
