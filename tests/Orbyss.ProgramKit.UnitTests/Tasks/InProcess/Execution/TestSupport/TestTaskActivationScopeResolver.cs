using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Tasks.Activation;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class TestTaskActivationScopeResolver :
    ITaskActivationScopeResolver
{
    private readonly IServiceScopeFactory scopeFactory;
    private int createdScopes;

    public TestTaskActivationScopeResolver(IServiceScopeFactory scopeFactory)
    {
        this.scopeFactory = scopeFactory ??
            throw new ArgumentNullException(nameof(scopeFactory));
    }

    internal int CreatedScopes => Volatile.Read(ref createdScopes);

    public ValueTask<ITaskActivationScope> CreateScopeAsync(
        Orbyss.ProgramKit.Tasks.Activation.TaskActivationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        Interlocked.Increment(ref createdScopes);
        var scope = scopeFactory.CreateAsyncScope();
        ITaskActivationScope result =
            new TestTaskActivationScope(scope, scope.ServiceProvider);
        return ValueTask.FromResult(result);
    }
}
