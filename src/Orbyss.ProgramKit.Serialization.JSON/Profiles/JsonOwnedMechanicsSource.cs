using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Binds a profile revision to one exact owned implementation source.</summary>
public sealed record JsonOwnedMechanicsSource(
    string RelativePath,
    Sha256Digest Digest);
