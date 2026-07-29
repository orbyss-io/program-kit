using System.Text.Json.Serialization;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;

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
[JsonSerializable(typeof(CapabilityInitializationLock))]
[JsonSerializable(typeof(LegacyCapabilityInitializationLock))]
[JsonSerializable(typeof(ConsumerCapabilityCatalogDocument))]
internal sealed partial class CapabilityInitializationJsonContext :
    JsonSerializerContext;
