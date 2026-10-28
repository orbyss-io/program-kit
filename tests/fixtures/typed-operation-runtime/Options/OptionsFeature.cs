using CShells;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.TypedOperation.OptionsProbe;

/// <summary>Wraps the actual shipped options owner and observes later native lifecycle execution.</summary>
[ShellFeature("TypedLabelOptionsProbe")]
public sealed class OptionsFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        LabelApiOptions.Configure(services, settings);
        services.AddScoped<IShellInitializer, EffectInitializer>();
    }
}
