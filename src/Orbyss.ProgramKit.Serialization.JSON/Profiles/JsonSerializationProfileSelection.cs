using System.Collections.Immutable;
using Orbyss.ProgramKit.Serialization.Json.Contributions;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Binds an exact profile to the exact contributions selected for one host registry.</summary>
public sealed record JsonSerializationProfileSelection(
    JsonSerializationProfileRef Profile,
    ImmutableArray<JsonSerializationContributionRef> Contributions);
