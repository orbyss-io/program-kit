using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>Collects one explicit shell-scoped JSON composition before freezing.</summary>
public interface IProgramKitJsonBuilder
{
    /// <summary>Adds one exact profile without profile-owned executable mechanics.</summary>
    IProgramKitJsonBuilder AddProfile(JsonSerializationProfile profile);

    /// <summary>Adds a new profile revision and its owned mechanics atomically.</summary>
    IProgramKitJsonBuilder AddOwnedProfile(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics mechanics);

    /// <summary>Selects one exact contribution for one exact profile.</summary>
    IProgramKitJsonBuilder AddJsonSerializationContribution(
        JsonSerializationProfileRef profileReference,
        JsonSerializationContribution contribution);

    /// <summary>Validates and atomically freezes the complete composition.</summary>
    IProgramKitJsonRegistry Freeze();
}
