using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace ObservatoryScheduling.Core.Configuration;

/// <summary>Stable fictional revision identities shared by the fixture projects.</summary>
public static class ObservatoryRevisions
{
    /// <summary>Creates a deterministic fixture reference for one named semantic revision.</summary>
    public static ArtifactReference Reference(
        string identity,
        string version = "1.0.0")
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(identity);
        ArgumentException.ThrowIfNullOrWhiteSpace(version);
        var digest = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                SHA256.HashData(
                    Encoding.UTF8.GetBytes(
                        string.Concat(identity, "@", version)))));
        return new ArtifactReference(
            new ProgramKitIdentifier(identity),
            new SemanticVersion(version),
            new Sha256Digest(digest));
    }
}
