using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>One explicitly selected source project and its exact package output contract.</summary>
public sealed record WorkspacePackageEntry(
    [property: JsonPropertyName("sourceProjectIdentity")]
    ProgramKitIdentifier SourceProjectIdentity,
    [property: JsonPropertyName("sourceProjectPath")] string SourceProjectPath,
    [property: JsonPropertyName("packageRevision")] ArtifactReference PackageRevision,
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("packageRole")] string PackageRole,
    [property: JsonPropertyName("expectedTarget")] string ExpectedTarget,
    [property: JsonPropertyName("packageOutputPath")] string PackageOutputPath);
