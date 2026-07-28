using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>
/// Exact alpha artifact-input manifest including host-keyed Console generation inputs.
/// </summary>
public sealed record DotNetArtifactInputManifestAlpha1(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("inputs")] ImmutableArray<DotNetArtifactInputEntry> Inputs,
    [property: JsonPropertyName("hostDocuments")]
    ImmutableArray<DotNetHostDocumentInput> HostDocuments,
    [property: JsonPropertyName("consoleGenerations")]
    ImmutableArray<DotNetConsoleGenerationInputBinding> ConsoleGenerations)
{
    /// <summary>Projects the shared exact-input portion used by the resolver.</summary>
    public DotNetArtifactInputManifest ToArtifactInputManifest() =>
        new(Schema, Version, Inputs, HostDocuments);
}
