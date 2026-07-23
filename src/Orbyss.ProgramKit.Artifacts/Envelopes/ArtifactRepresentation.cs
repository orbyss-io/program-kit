using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Envelopes;

/// <summary>Binds the exact serialization and canonicalization profiles.</summary>
/// <param name="SerializationProfileRef">The exact serialization profile.</param>
/// <param name="CanonicalizationProfileRef">The exact canonicalization profile.</param>
/// <param name="CanonicalMediaType">The canonical media type.</param>
public sealed record ArtifactRepresentation(
    ProfileReference SerializationProfileRef,
    ProfileReference CanonicalizationProfileRef,
    string CanonicalMediaType);
