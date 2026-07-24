using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Tasks.Activation;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class TestTaskActivationScope : ITaskActivationScope
{
    private readonly AsyncServiceScope scope;

    internal TestTaskActivationScope(
        AsyncServiceScope scope,
        IServiceProvider services)
    {
        this.scope = scope;
        Services = services ??
            throw new ArgumentNullException(nameof(services));
    }

    public IServiceProvider Services { get; }

    public ValueTask DisposeAsync() => scope.DisposeAsync();
}
