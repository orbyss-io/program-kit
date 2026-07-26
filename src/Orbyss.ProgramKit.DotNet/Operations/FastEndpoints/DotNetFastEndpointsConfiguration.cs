using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Operations.FastEndpoints;

/// <summary>
/// Exact optional FastEndpoints syntax-adapter selection for one API host.
/// </summary>
public sealed record DotNetFastEndpointsConfiguration(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("shellAdapterPackage")] DotNetPackageReference ShellAdapterPackage,
    [property: JsonPropertyName("fastEndpointsPackage")] DotNetPackageReference FastEndpointsPackage);
