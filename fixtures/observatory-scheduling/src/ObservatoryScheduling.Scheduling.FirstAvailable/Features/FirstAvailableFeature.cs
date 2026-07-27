using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using ObservatoryScheduling.Core.Contracts.Scheduling;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Direct CShells feature registration for first-available scheduling.</summary>
public sealed class FirstAvailableFeature : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddTransient<FirstAvailableSelectionMiddleware>();
        services.AddTransient<IFirstAvailableScheduler, FirstAvailableScheduler>();
        FirstAvailableTaskRegistrations.Register(services);
    }
}
