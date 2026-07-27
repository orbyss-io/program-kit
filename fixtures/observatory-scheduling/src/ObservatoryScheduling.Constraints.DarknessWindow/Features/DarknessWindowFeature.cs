using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using ObservatoryScheduling.Core.Contracts.Constraints;

namespace ObservatoryScheduling.Constraints.DarknessWindow.Features;

/// <summary>Direct CShells registration for the ordered darkness constraint.</summary>
public sealed class DarknessWindowFeature : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddSingleton<IViewingConstraint, DarknessWindowConstraint>();
    }
}
