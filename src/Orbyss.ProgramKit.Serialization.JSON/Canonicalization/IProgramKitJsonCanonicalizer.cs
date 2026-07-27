using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Canonicalization;

/// <summary>
/// Produces strict canonical JSON through the selected Program Kit profile
/// mechanics.
/// </summary>
public interface IProgramKitJsonCanonicalizer
{
    /// <summary>Validates and canonicalizes one complete UTF-8 JSON value.</summary>
    CanonicalJsonValue Canonicalize(
        ReadOnlySpan<byte> utf8Json,
        JsonSerializationLimits limits);

    /// <summary>Canonicalizes one finite binary64 value.</summary>
    CanonicalJsonValue CanonicalizeNumber(double value);
}
