using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Workbench.Operations.Json;

/// <summary>Performs model-first JSON operations through exact frozen profiles.</summary>
public interface IWorkbenchJsonService
{
    /// <summary>Parses one typed value through the selected profile.</summary>
    T Parse<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits);

    /// <summary>Parses and semantically validates one typed value.</summary>
    WorkbenchResult<T> Validate<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits,
        IProgramKitSemanticValidator<T> validator);

    /// <summary>Parses and rewrites one typed value as canonical JSON.</summary>
    CanonicalJsonValue Normalize<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits);

    /// <summary>Gets the digest of canonical typed JSON.</summary>
    Sha256Digest Digest<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits);
}
