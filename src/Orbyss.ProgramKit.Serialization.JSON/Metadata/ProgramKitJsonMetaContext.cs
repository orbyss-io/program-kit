using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Metadata;

[JsonSourceGenerationOptions(
    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
    GenerationMode = JsonSourceGenerationMode.Metadata,
    NumberHandling = JsonNumberHandling.Strict,
    PropertyNameCaseInsensitive = false,
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    RespectNullableAnnotations = true,
    RespectRequiredConstructorParameters = true,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(ArtifactReference))]
[JsonSerializable(typeof(ProfileReference))]
[JsonSerializable(typeof(ArtifactContract))]
[JsonSerializable(typeof(ArtifactIdentity))]
[JsonSerializable(typeof(ArtifactCompatibility))]
[JsonSerializable(typeof(ArtifactProvenance))]
[JsonSerializable(typeof(ArtifactRepresentation))]
[JsonSerializable(typeof(ArtifactIntegrity))]
[JsonSerializable(typeof(JsonSerializationProfileRef))]
[JsonSerializable(typeof(JsonSerializationContributionRef))]
[JsonSerializable(typeof(JsonSerializationRules))]
[JsonSerializable(typeof(JsonSerializationLimits))]
[JsonSerializable(typeof(JsonSerializationProfile))]
[JsonSerializable(typeof(JsonSerializationProfileSelection))]
[JsonSerializable(typeof(JsonOwnedMechanicsSource))]
[JsonSerializable(typeof(JsonProfileSourceDescriptor))]
[JsonSerializable(typeof(JsonSerializationContributionDescriptor))]
[JsonSerializable(typeof(ArtifactEnvelope<JsonSerializationProfileSelection>))]
internal sealed partial class ProgramKitJsonMetaContext : JsonSerializerContext;
