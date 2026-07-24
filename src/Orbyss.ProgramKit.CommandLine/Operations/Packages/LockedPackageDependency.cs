using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>One exact dependency range recorded for a reviewed external package.</summary>
public sealed record LockedPackageDependency(
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("versionRange")] string VersionRange);
