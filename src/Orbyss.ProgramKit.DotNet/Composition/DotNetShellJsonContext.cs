using System.Text.Json.Serialization;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Composition;

[JsonSourceGenerationOptions(
    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    NumberHandling = JsonNumberHandling.Strict,
    PropertyNameCaseInsensitive = false,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(DotNetShellDocument))]
[JsonSerializable(typeof(DotNetArtifactInputManifest))]
[JsonSerializable(typeof(DotNetShellLockDocument))]
[JsonSerializable(typeof(OpenApiDocumentProjection))]
[JsonSerializable(typeof(OpenConsoleDocument))]
[JsonSerializable(typeof(OpenWorkerDocument))]
[JsonSerializable(typeof(SecretResolutionContract))]
[JsonSerializable(typeof(SecretChangeSignal))]
[JsonSerializable(typeof(SecretReactionResult))]
internal sealed partial class DotNetShellJsonContext : JsonSerializerContext;
