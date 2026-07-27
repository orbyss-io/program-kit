using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

internal sealed class BlockingRegistryFactory :
    IProgramKitJsonRegistryFactory,
    IDisposable
{
    private readonly ManualResetEventSlim entered = new(initialState: false);
    private readonly IProgramKitJsonRegistryFactory inner;
    private readonly ManualResetEventSlim release = new(initialState: false);
    private int createCallCount;

    internal BlockingRegistryFactory(IProgramKitJsonRegistryFactory inner)
    {
        this.inner = inner;
    }

    internal int CreateCallCount => Volatile.Read(ref createCallCount);

    public IProgramKitJsonRegistry Create(
        ImmutableArray<JsonSerializationProfile> profiles,
        ImmutableArray<JsonProfileOwnedMechanics> profileOwnedMechanics,
        ImmutableArray<JsonSerializationContributionSelection> contributionSelections)
    {
        Interlocked.Increment(ref createCallCount);
        entered.Set();
        release.Wait();
        return inner.Create(
            profiles,
            profileOwnedMechanics,
            contributionSelections);
    }

    internal bool WaitUntilEntered(TimeSpan timeout) => entered.Wait(timeout);

    internal void Release() => release.Set();

    public void Dispose()
    {
        release.Set();
        release.Dispose();
        entered.Dispose();
    }
}
