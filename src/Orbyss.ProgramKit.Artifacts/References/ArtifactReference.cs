using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.References;

/// <summary>An exact immutable reference to one semantic revision.</summary>
/// <param name="Identity">The stable semantic identity.</param>
/// <param name="Version">The independent semantic version.</param>
/// <param name="Digest">The digest of the exact referenced bytes.</param>
public sealed record ArtifactReference(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest);
