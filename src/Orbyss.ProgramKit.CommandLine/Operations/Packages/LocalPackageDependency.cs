using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>One dependency declared by a prepared nupkg for one target framework.</summary>
public sealed record LocalPackageDependency(
    [property: JsonPropertyName("targetFramework")] string TargetFramework,
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("versionRange")] string VersionRange);
