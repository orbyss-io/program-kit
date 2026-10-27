using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.CShellsInitializerOwnership;

/// <summary>Separates a generation-owned disposable resource from its non-owning admission.</summary>
[ShellFeature("ProgramKit.Examples.CShellsInitializerOwnership")]
public sealed class ResourceFeature : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<SyntheticResourceOwner>();
        services.AddShellInitializer<ResourceAdmission>(LifecyclePhase.Prepare, order: 200);
    }
}
