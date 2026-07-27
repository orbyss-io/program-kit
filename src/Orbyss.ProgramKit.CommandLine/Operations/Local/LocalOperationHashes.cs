using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.Local;

/// <summary>Fixed content hashing mechanics for local package and publish operations.</summary>
internal static class LocalOperationHashes
{
    internal static Sha256Digest Sha256(ReadOnlySpan<byte> content) =>
        new(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(content))));

    internal static string NuGetContentHash(ReadOnlySpan<byte> content) =>
        Convert.ToBase64String(SHA512.HashData(content));
}
