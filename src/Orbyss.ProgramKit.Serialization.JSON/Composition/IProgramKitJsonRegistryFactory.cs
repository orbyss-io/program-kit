using System.Collections.Immutable;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>Creates fully validated immutable JSON registries.</summary>
public interface IProgramKitJsonRegistryFactory
{
    /// <summary>Creates a registry from one complete immutable composition snapshot.</summary>
    IProgramKitJsonRegistry Create(
        ImmutableArray<JsonSerializationProfile> profiles,
        ImmutableArray<JsonProfileOwnedMechanics> profileOwnedMechanics,
        ImmutableArray<JsonSerializationContributionSelection> contributionSelections);
}
