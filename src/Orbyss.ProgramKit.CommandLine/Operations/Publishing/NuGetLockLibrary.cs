using System.Collections.Immutable;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>One exact package selection in a NuGet lock target.</summary>
internal sealed record NuGetLockLibrary(
    [property: JsonPropertyName("type")] string Type,
    [property: JsonPropertyName("resolved")] string Resolved,
    [property: JsonPropertyName("contentHash")] string ContentHash,
    [property: JsonPropertyName("requested")] string? Requested = null,
    [property: JsonPropertyName("dependencies")]
    ImmutableDictionary<string, string>? Dependencies = null);
