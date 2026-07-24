using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using ObservatoryScheduling.Core.Contracts.Visibility;

namespace ObservatoryScheduling.Visibility.Fixed.Features;

/// <summary>Direct CShells feature registration for the fictional static forecast.</summary>
public sealed class StaticVisibilityFeature : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddSingleton<IVisibilityForecast, StaticVisibilityForecast>();
    }
}
