using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>An exact immutable reference to one JSON serialization profile revision.</summary>
/// <param name="Identity">The profile identity.</param>
/// <param name="Version">The independent profile version.</param>
/// <param name="Digest">The digest of the exact self-reference-free profile-source bytes.</param>
public sealed record JsonSerializationProfileRef(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest);
