using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

/// <summary>Performs model-first JSON reads and canonical writes through exact profiles.</summary>
public interface IProgramKitJsonSerializer
{
    /// <summary>Reads one typed model through an exact frozen profile.</summary>
    T Read<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits);

    /// <summary>Writes one typed model as strict canonical UTF-8 JSON.</summary>
    CanonicalJsonValue Write<T>(
        T value,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits);
}
