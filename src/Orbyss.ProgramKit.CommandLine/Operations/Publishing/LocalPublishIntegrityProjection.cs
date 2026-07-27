using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Integrity projection used only while the digest field is omitted.</summary>
internal sealed record LocalPublishIntegrityProjection(
    [property: JsonPropertyName("algorithm")] string Algorithm);
