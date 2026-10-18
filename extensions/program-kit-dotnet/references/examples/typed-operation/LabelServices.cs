using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Called by the owning runtime feature; does not activate or resolve a provider.</summary>
public static class LabelServices
{
    /// <summary>Registers the application's scoped label capability.</summary>
    public static void Configure(IServiceCollection services) => services.AddScoped<ILabelOperations, LabelOperations>();
}
