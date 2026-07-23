using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>Selects one executable contribution for one exact profile revision.</summary>
public sealed record JsonSerializationContributionSelection(
    JsonSerializationProfileRef Profile,
    JsonSerializationContribution Contribution);
