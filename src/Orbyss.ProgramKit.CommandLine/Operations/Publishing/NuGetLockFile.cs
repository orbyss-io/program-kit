using System.Collections.Immutable;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Typed bounded view of a generated NuGet packages.lock.json.</summary>
internal sealed record NuGetLockFile(
    [property: JsonPropertyName("version")] int Version,
    [property: JsonPropertyName("dependencies")]
    ImmutableDictionary<string, ImmutableDictionary<string, NuGetLockLibrary>>
        Dependencies);
