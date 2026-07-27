using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Canonical hash manifest for one locally published application leaf.</summary>
public sealed record LocalPublishManifest(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("hostIdentity")] ProgramKitIdentifier HostIdentity,
    [property: JsonPropertyName("hostVersion")] SemanticVersion HostVersion,
    [property: JsonPropertyName("projectName")] string ProjectName,
    [property: JsonPropertyName("sdkVersion")] string SdkVersion,
    [property: JsonPropertyName("targetFramework")] string TargetFramework,
    [property: JsonPropertyName("runtimeIdentifier")] string? RuntimeIdentifier,
    [property: JsonPropertyName("configuration")] string Configuration,
    [property: JsonPropertyName("deploymentMode")] string DeploymentMode,
    [property: JsonPropertyName("shellRevision")] ArtifactReference ShellRevision,
    [property: JsonPropertyName("generatorRevision")] ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("inputVersionMapRevision")]
    ArtifactReference InputVersionMapRevision,
    [property: JsonPropertyName("inputVersionSelectionRevision")]
    ArtifactReference InputVersionSelectionRevision,
    [property: JsonPropertyName("shellLockDigest")] Sha256Digest ShellLockDigest,
    [property: JsonPropertyName("packageRootManifestDigest")]
    Sha256Digest PackageRootManifestDigest,
    [property: JsonPropertyName("packageSelectionDigest")]
    Sha256Digest PackageSelectionDigest,
    [property: JsonPropertyName("files")]
    ImmutableArray<PublishedApplicationFile> Files,
    [property: JsonPropertyName("integrity")] ArtifactIntegrity Integrity);
