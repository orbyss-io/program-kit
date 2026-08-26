using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Tasks;

[ShellFeature(
    name: "ProgramKitTasks",
    DisplayName = "Program Kit Tasks",
    Description = "Owns startup, background, and recurring work for one shell generation.")]
public sealed class ProgramKitTasksFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<ShellTaskManager>();
        services.AddSingleton<IShellTaskManager>(provider => provider.GetRequiredService<ShellTaskManager>());
        services.AddShellInitializer<StartShellTasksInitializer>(LifecyclePhase.Start, order: 0);
        services.AddShellTerminator<StopShellTasksTerminator>(LifecyclePhase.Start, order: 0);
    }
}
