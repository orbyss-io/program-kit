namespace Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

internal sealed class FixtureChangeSubscription : IDisposable
{
    private Action? dispose;

    internal FixtureChangeSubscription(Action dispose)
    {
        this.dispose = dispose;
    }

    /// <inheritdoc />
    public void Dispose()
    {
        dispose?.Invoke();
        dispose = null;
    }
}
