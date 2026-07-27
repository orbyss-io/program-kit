using System.Collections.Immutable;
using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

internal sealed record FrozenJsonProfile(
    JsonSerializationProfile Descriptor,
    JsonSerializerOptions Options,
    ImmutableArray<Type> RootMetadataTargetTypes);
