using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>Exact serialization profiles and contributions selected by a host.</summary>
public sealed record DotNetJsonSerializationSelection(
    [property: JsonPropertyName("profiles")] ImmutableArray<JsonSerializationProfileRef> Profiles,
    [property: JsonPropertyName("contributions")] ImmutableArray<JsonSerializationContributionRef> Contributions);
