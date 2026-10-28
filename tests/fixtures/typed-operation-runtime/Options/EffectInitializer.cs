using CShells.Lifecycle;

namespace ProgramKit.Examples.TypedOperation.OptionsProbe;

/// <summary>Observes a protected later-phase action without doing work in its constructor.</summary>
[LifecycleOrder(LifecyclePhase.Start, 0)]
internal sealed class EffectInitializer(EffectObservation observation) : IShellInitializer
{
    /// <inheritdoc />
    public Task InitializeAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        observation.Starts++;

        return Task.CompletedTask;
    }
}
