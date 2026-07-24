using System.Text.Json.Serialization;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;

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
[JsonSerializable(typeof(OpenConsoleDocument))]
[JsonSerializable(typeof(OpenWorkerDocument))]
internal sealed partial class DotNetShellJsonContext : JsonSerializerContext;
