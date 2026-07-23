using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Canonicalization;

/// <summary>
/// Opaque immutable canonical UTF-8 JSON bytes. Construction is possible only
/// through strict Program Kit canonicalization.
/// </summary>
public sealed class CanonicalJsonValue : IEquatable<CanonicalJsonValue>
{
    private readonly byte[] utf8Bytes;

    internal CanonicalJsonValue(byte[] utf8Bytes)
    {
        this.utf8Bytes = utf8Bytes;
    }

    /// <summary>Gets the canonical UTF-8 byte count.</summary>
    public int Length => utf8Bytes.Length;

    /// <summary>Gets the SHA-256 digest of the canonical bytes.</summary>
    public Sha256Digest Digest
    {
        get
        {
            var digest = System.Security.Cryptography.SHA256.HashData(utf8Bytes);
            return new Sha256Digest(
                string.Concat(
                    "sha256:",
                    Convert.ToHexString(digest).ToLowerInvariant()));
        }
    }

    /// <summary>Returns a defensive copy of the canonical UTF-8 bytes.</summary>
    public byte[] ToArray() => utf8Bytes.ToArray();

    /// <inheritdoc />
    public bool Equals(CanonicalJsonValue? other) =>
        other is not null && utf8Bytes.AsSpan().SequenceEqual(other.utf8Bytes);

    /// <inheritdoc />
    public override bool Equals(object? obj) =>
        obj is CanonicalJsonValue other && Equals(other);

    /// <inheritdoc />
    public override int GetHashCode()
    {
        var hash = new HashCode();
        hash.AddBytes(utf8Bytes);
        return hash.ToHashCode();
    }

    /// <summary>Compares two canonical values by exact bytes.</summary>
    public static bool operator ==(
        CanonicalJsonValue? left,
        CanonicalJsonValue? right) =>
        ReferenceEquals(left, right) || left is not null && left.Equals(right);

    /// <summary>Compares two canonical values by exact bytes.</summary>
    public static bool operator !=(
        CanonicalJsonValue? left,
        CanonicalJsonValue? right) =>
        !(left == right);
}
