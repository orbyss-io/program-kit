using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Publishing;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

[JsonSourceGenerationOptions(
    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    NumberHandling = JsonNumberHandling.Strict,
    PropertyNameCaseInsensitive = false,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(WorkspacePackageManifest))]
[JsonSerializable(typeof(LocalPackageRootManifest))]
[JsonSerializable(typeof(LocalPublishManifest))]
[JsonSerializable(typeof(LocalPublishManifestDigestProjection))]
[JsonSerializable(typeof(VersionMapDocument))]
[JsonSerializable(typeof(VersionSelectionDocument))]
[JsonSerializable(typeof(NuGetLockFile))]
internal sealed partial class LocalOperationsJsonContext : JsonSerializerContext;
