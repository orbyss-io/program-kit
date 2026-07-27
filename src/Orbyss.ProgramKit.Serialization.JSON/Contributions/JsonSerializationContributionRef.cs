using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>An exact immutable reference to one JSON contribution revision.</summary>
/// <param name="Identity">The contribution identity.</param>
/// <param name="Version">The independent contribution version.</param>
/// <param name="Digest">The digest of the exact contribution descriptor bytes.</param>
public sealed record JsonSerializationContributionRef(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest);
