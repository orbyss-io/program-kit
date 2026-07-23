using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Converters;
using Orbyss.ProgramKit.Serialization.Json.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

internal static class JsonMetaComposition
{
    internal static ImmutableArray<Type> EnumConverterTargetTypes { get; } =
    [
        typeof(ArtifactStatus),
        typeof(CompatibilityDimension),
        typeof(CompatibilityClassification),
        typeof(JsonProfileExtensibility),
        typeof(JsonProfileSourceKind),
        typeof(JsonSerializationContributionKind),
    ];

    internal static JsonProfileOwnedMechanics CreateOwnedMechanics() =>
        new(
            ProgramKitJsonProfiles.JsonMeta.Reference,
            new ProgramKitIdentifier("pkid:package:program-kit:serialization-json"),
            ProgramKitJsonMetaContext.Default,
            isBuiltIn: true,
            converters:
            [
                new JsonProfileOwnedConverter(
                    new KebabCaseEnumJsonConverter<ArtifactStatus>()),
                new JsonProfileOwnedConverter(
                    new KebabCaseEnumJsonConverter<CompatibilityDimension>()),
                new JsonProfileOwnedConverter(
                    new KebabCaseEnumJsonConverter<CompatibilityClassification>()),
                new JsonProfileOwnedConverter(
                    new KebabCaseEnumJsonConverter<JsonProfileExtensibility>()),
                new JsonProfileOwnedConverter(
                    new KebabCaseEnumJsonConverter<JsonProfileSourceKind>()),
                new JsonProfileOwnedConverter(
                    new KebabCaseEnumJsonConverter<JsonSerializationContributionKind>()),
            ]);
}
