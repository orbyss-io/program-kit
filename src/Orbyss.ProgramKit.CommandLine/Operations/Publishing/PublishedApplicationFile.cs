using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>One exact application output in a local publish leaf.</summary>
public sealed record PublishedApplicationFile(
    [property: JsonPropertyName("relativePath")] string RelativePath,
    [property: JsonPropertyName("size")] long Size,
    [property: JsonPropertyName("digest")] Sha256Digest Digest);
