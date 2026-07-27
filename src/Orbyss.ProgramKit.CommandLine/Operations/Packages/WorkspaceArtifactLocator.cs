using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Binds one exact artifact revision to a normalized source-root-relative file.</summary>
public sealed record WorkspaceArtifactLocator(
    [property: JsonPropertyName("revision")] ArtifactReference Revision,
    [property: JsonPropertyName("relativePath")] string RelativePath);
