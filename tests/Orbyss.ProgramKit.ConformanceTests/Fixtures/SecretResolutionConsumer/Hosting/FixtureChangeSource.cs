using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

namespace Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

/// <summary>Fixture provider adapter that emits metadata-only signals.</summary>
public sealed class FixtureChangeSource : IFixtureChangeSource
{
    private Action<SecretChangeSignal>? callback;

    /// <summary>Gets whether the generated callback subscription was disposed.</summary>
    public bool SubscriptionDisposed { get; private set; }

    /// <inheritdoc />
    public IDisposable Subscribe(
        ProgramKitIdentifier referenceIdentity,
        Action<SecretChangeSignal> callback)
    {
        ArgumentNullException.ThrowIfNull(callback);
        _ = referenceIdentity;
        this.callback = callback;
        return new FixtureChangeSubscription(DisposeSubscription);
    }

    /// <summary>Emits one metadata-only provider change.</summary>
    public void Emit(SecretChangeSignal signal)
    {
        ArgumentNullException.ThrowIfNull(signal);
        callback?.Invoke(signal);
    }

    internal void DisposeSubscription()
    {
        callback = null;
        SubscriptionDisposed = true;
    }
}
