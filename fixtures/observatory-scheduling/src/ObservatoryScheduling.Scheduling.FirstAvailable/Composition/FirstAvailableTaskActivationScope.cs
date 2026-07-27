using CShells.Lifecycle;
using Orbyss.ProgramKit.Tasks.Activation;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Composition;

internal sealed class FirstAvailableTaskActivationScope :
    ITaskActivationScope
{
    private readonly IShellScope scope;

    internal FirstAvailableTaskActivationScope(
        IShellScope scope,
        IServiceProvider services)
    {
        this.scope = scope;
        Services = services ??
            throw new ArgumentNullException(nameof(services));
    }

    public IServiceProvider Services { get; }

    public ValueTask DisposeAsync() => scope.DisposeAsync();
}
