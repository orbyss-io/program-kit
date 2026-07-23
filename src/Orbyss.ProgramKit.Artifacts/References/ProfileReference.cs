using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.References;

/// <summary>An exact immutable reference constrained to a profile identity.</summary>
/// <param name="Identity">The profile identity.</param>
/// <param name="Version">The independent profile version.</param>
/// <param name="Digest">The digest of the exact profile bytes.</param>
public sealed record ProfileReference(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest);
