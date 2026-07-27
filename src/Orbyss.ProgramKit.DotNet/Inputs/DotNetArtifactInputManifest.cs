using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Finite allow-list for exact generation inputs below an explicit read root.</summary>
public sealed record DotNetArtifactInputManifest(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("inputs")] ImmutableArray<DotNetArtifactInputEntry> Inputs,
    [property: JsonPropertyName("hostDocuments")]
    ImmutableArray<DotNetHostDocumentInput> HostDocuments);
