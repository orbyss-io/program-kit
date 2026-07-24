using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Orbyss.ProgramKit.Tasks.Activation;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Composition;

/// <summary>Registers the host-to-shell activation bridge for this feature.</summary>
public static class FirstAvailableTaskActivationServiceCollectionExtensions
{
    /// <summary>
    /// Maps first-available task activation to one explicitly selected CShell.
    /// </summary>
    public static IServiceCollection AddFirstAvailableTaskActivation(
        this IServiceCollection services,
        string shellName)
    {
        ArgumentNullException.ThrowIfNull(services);
        if (string.IsNullOrWhiteSpace(shellName))
        {
            throw new ArgumentException(
                "A shell name is required.",
                nameof(shellName));
        }

        services.TryAddSingleton<ITaskActivationScopeResolver>(
            provider => new FirstAvailableTaskActivationScopeResolver(
                provider.GetRequiredService<IShellRegistry>(),
                shellName));
        return services;
    }
}
