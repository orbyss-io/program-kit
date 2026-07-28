using System.Text.Json.Serialization;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

[JsonSourceGenerationOptions(
    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    NumberHandling = JsonNumberHandling.Strict,
    PropertyNameCaseInsensitive = false,
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(DotNetHostGenerationRequestDocument))]
[JsonSerializable(typeof(DotNetHostConsumerBuildRequest))]
[JsonSerializable(typeof(DotNetHostRefreshResult))]
internal sealed partial class DotNetHostRefreshJsonContext :
    JsonSerializerContext;
