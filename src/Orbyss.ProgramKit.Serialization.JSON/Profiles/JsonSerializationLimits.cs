using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Bounds one strict JSON operation and each complete buffered object.</summary>
/// <param name="MaxUtf8Bytes">Maximum input and canonical-output bytes.</param>
/// <param name="MaxDepth">Maximum object/array nesting depth, never greater than 64.</param>
/// <param name="MaxTokens">Maximum reader tokens.</param>
/// <param name="MaxObjectMembers">Maximum members in any one object.</param>
/// <param name="MaxBufferedObjectBytes">
/// Maximum complete canonical object bytes, including braces, commas, names,
/// separators, and values, retained while sorting one object.
/// </param>
public sealed record JsonSerializationLimits(
    long MaxUtf8Bytes,
    int MaxDepth,
    long MaxTokens,
    int MaxObjectMembers,
    long MaxBufferedObjectBytes)
{
    /// <summary>Gets conservative deterministic baseline limits.</summary>
    public static JsonSerializationLimits Default { get; } =
        new(1_048_576, 64, 1_000_000, 16_384, 1_048_576);

    internal void EnsureValid(string path = "/limits")
    {
        if (MaxUtf8Bytes <= 0 ||
            MaxDepth is < 1 or > 64 ||
            MaxTokens <= 0 ||
            MaxObjectMembers <= 0 ||
            MaxBufferedObjectBytes <= 0 ||
            MaxBufferedObjectBytes > MaxUtf8Bytes)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "JSON limits must be positive, depth must be from 1 through 64, and the complete object buffer cannot exceed the byte limit.",
                path);
        }
    }

    internal bool FitsWithin(JsonSerializationLimits maximum) =>
        MaxUtf8Bytes <= maximum.MaxUtf8Bytes &&
        MaxDepth <= maximum.MaxDepth &&
        MaxTokens <= maximum.MaxTokens &&
        MaxObjectMembers <= maximum.MaxObjectMembers &&
        MaxBufferedObjectBytes <= maximum.MaxBufferedObjectBytes;
}
