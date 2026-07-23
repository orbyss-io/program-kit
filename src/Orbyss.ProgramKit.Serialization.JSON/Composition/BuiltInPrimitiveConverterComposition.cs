using System.Collections.Immutable;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Serialization.Json.Converters;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

internal static class BuiltInPrimitiveConverterComposition
{
    internal static ImmutableArray<Type> PrimitiveConverterTargetTypes { get; } =
    [
        typeof(ProgramKitIdentifier),
        typeof(SemanticVersion),
        typeof(SemanticVersionRange),
        typeof(Sha256Digest),
    ];

    internal static ImmutableArray<Type> GetBuiltInConverterTargetTypes(
        JsonSerializationProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        return PrimitiveConverterTargetTypes;
    }

    internal static void AddPrimitiveConverters(JsonSerializerOptions options)
    {
        ArgumentNullException.ThrowIfNull(options);
        options.Converters.Add(new ProgramKitIdentifierJsonConverter());
        options.Converters.Add(new SemanticVersionJsonConverter());
        options.Converters.Add(new SemanticVersionRangeJsonConverter());
        options.Converters.Add(new Sha256DigestJsonConverter());
    }
}
