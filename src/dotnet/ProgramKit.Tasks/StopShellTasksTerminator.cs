using CShells.Lifecycle;

namespace ProgramKit.Tasks;

public sealed class StopShellTasksTerminator(IShellTaskManager taskManager) : IShellTerminator
{
    public Task TerminateAsync(CancellationToken cancellationToken = default) => taskManager.StopAsync(cancellationToken);
}
