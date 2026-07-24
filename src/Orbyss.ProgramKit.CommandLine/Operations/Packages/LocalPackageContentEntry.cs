using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>One exact normalized file inside a prepared nupkg archive.</summary>
public sealed record LocalPackageContentEntry(
    [property: JsonPropertyName("relativePath")] string RelativePath,
    [property: JsonPropertyName("size")] long Size,
    [property: JsonPropertyName("digest")] Sha256Digest Digest);
