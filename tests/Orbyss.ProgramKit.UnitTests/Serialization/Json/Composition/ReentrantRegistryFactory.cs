using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class ReentrantRegistryFactory : IProgramKitJsonRegistryFactory
{
    private readonly Func<IProgramKitJsonRegistry> freeze;

    internal ReentrantRegistryFactory(
        Func<IProgramKitJsonRegistry> freeze)
    {
        ArgumentNullException.ThrowIfNull(freeze);
        this.freeze = freeze;
    }

    public IProgramKitJsonRegistry Create(
        ImmutableArray<JsonSerializationProfile> profiles,
        ImmutableArray<JsonProfileOwnedMechanics> profileOwnedMechanics,
        ImmutableArray<JsonSerializationContributionSelection> contributionSelections) =>
        freeze();
}
