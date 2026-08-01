using System;
using System.Security.Cryptography;

namespace Orbyss.ProgramKit.Kernel.Canonicalization;

public static class Digests
{
    public static string Sha256(ReadOnlySpan<byte> bytes) =>
        $"sha256:{Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()}";
}
