using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>One exact browser-target implementation and package closure.</summary>
public sealed record DotNetPublicBrowserTargetAdapter(
    [property: JsonPropertyName("adapterRevision")] ArtifactReference AdapterRevision,
    [property: JsonPropertyName("targetKind")] DotNetPublicBrowserTargetKind TargetKind,
    [property: JsonPropertyName("generatorRevision")] ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("packages")] ImmutableArray<DotNetPackageReference> Packages);
