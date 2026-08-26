using CShells.Lifecycle;

namespace ProgramKit.Tasks;

public sealed class StartShellTasksInitializer(IShellTaskManager taskManager) : IShellInitializer
{
    public Task InitializeAsync(CancellationToken cancellationToken) => taskManager.StartAsync(cancellationToken);
}
