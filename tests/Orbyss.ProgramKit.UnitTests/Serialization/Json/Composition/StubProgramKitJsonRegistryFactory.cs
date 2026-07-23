using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class StubProgramKitJsonRegistryFactory :
    IProgramKitJsonRegistryFactory
{
    private readonly IProgramKitJsonRegistry registry;

    internal StubProgramKitJsonRegistryFactory(
        IProgramKitJsonRegistry registry)
    {
        this.registry = registry;
    }

    public IProgramKitJsonRegistry Create(
        ImmutableArray<JsonSerializationProfile> profiles,
        ImmutableArray<JsonProfileOwnedMechanics> profileOwnedMechanics,
        ImmutableArray<JsonSerializationContributionSelection> contributionSelections)
    {
        CreateCallCount++;
        return registry;
    }

    internal int CreateCallCount { get; private set; }
}
