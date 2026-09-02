using CShells.Features;
using CShells.Lifecycle;
using Nuplane.Loading;
using ProgramKit.Host.Bundles;
using ProgramKit.Host.Feed;

namespace ProgramKit.Host.Shells;

/// <summary>Activates configured shells before the host reports readiness.</summary>
internal sealed class EagerShellActivationHostedService(
    IShellRegistry registry,
    IRuntimeFeatureCatalog featureCatalog,
    IConfiguration configuration,
    ApplicationBundle bundle,
    IPackageLoadStateCatalog packageLoadStates,
    NuplaneAssemblyProvider assemblyProvider,
    EagerShellActivationState state,
    ILogger<EagerShellActivationHostedService> logger) : IHostedService
{
    /// <inheritdoc />
    public async Task StartAsync(CancellationToken cancellationToken)
    {
        if (configuration.GetValue("ProgramKit:Boot:EagerShellActivation", defaultValue: true) is false)
        {
            state.Complete();
            return;
        }

        var failFast = configuration.GetValue("ProgramKit:Boot:FailOnShellActivationError", defaultValue: true);
        var loadState = await packageLoadStates.GetLoadStateAsync(cancellationToken).ConfigureAwait(false);
        foreach (var feature in bundle.Manifest.Features)
        {
            var package = loadState.Packages.SingleOrDefault(
                item => string.Equals(item.PackageId, feature.PackageId, StringComparison.OrdinalIgnoreCase));
            if (package is null || !package.Discoverable)
                throw new InvalidOperationException(
                    $"Application feature '{feature.Identity}' package '{feature.PackageId}' is not discoverable " +
                    $"after startup reconciliation (status={package?.Status.ToString() ?? "missing"}, " +
                    $"loadMode={package?.LoadMode.ToString() ?? "unknown"}).");
        }
        var availableAssemblies = (await assemblyProvider.GetAssembliesAsync(null!, cancellationToken)
            .ConfigureAwait(false)).ToArray();
        foreach (var feature in bundle.Manifest.Features)
        {
            var attributedTypes = availableAssemblies
                .SelectMany(GetLoadableTypes)
                .Where(type => type.GetCustomAttributesData().Any(attribute =>
                        attribute.AttributeType.FullName == "CShells.Features.ShellFeatureAttribute"
                        && attribute.ConstructorArguments.Count > 0
                        && string.Equals(
                            attribute.ConstructorArguments[0].Value as string,
                            feature.Identity,
                            StringComparison.Ordinal)))
                .ToArray();
            if (attributedTypes.Length != 1 || !typeof(IShellFeature).IsAssignableFrom(attributedTypes[0]))
            {
                var candidateInterface = attributedTypes.SingleOrDefault()?.GetInterfaces()
                    .FirstOrDefault(type => type.FullName == typeof(IShellFeature).FullName);
                throw new InvalidOperationException(
                    $"Application feature '{feature.Identity}' did not resolve to exactly one host-compatible " +
                    $"IShellFeature type (attributed={attributedTypes.Length}, " +
                    $"assignable={(attributedTypes.Length == 1 && typeof(IShellFeature).IsAssignableFrom(attributedTypes[0]))}, " +
                    $"featureContract={candidateInterface?.AssemblyQualifiedName ?? "missing"}, " +
                    $"hostContract={typeof(IShellFeature).AssemblyQualifiedName}).");
            }
        }
        await featureCatalog.RefreshAsync(cancellationToken).ConfigureAwait(false);
        var shellNames = configuration.GetSection("CShells:Shells").GetChildren()
            .Select(child => child.Key)
            .Where(name => !string.IsNullOrWhiteSpace(name))
            .ToArray();
        if (shellNames.Length == 0)
            throw new InvalidOperationException("No shells are configured under 'CShells:Shells'.");

        foreach (var name in shellNames)
        {
            try
            {
                await registry.GetOrActivateAsync(name, cancellationToken).ConfigureAwait(false);
                logger.LogInformation("Activated shell {ShellName} during host startup.", name);
            }
            catch (Exception exception) when (!failFast && exception is not OperationCanceledException)
            {
                logger.LogError(exception, "Shell {ShellName} failed eager activation; lazy activation remains available.", name);
            }
        }
        state.Complete();
    }

    /// <inheritdoc />
    public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;

    /// <summary>Returns the types that can be inspected from a reconciled package assembly.</summary>
    private static IEnumerable<Type> GetLoadableTypes(System.Reflection.Assembly assembly)
    {
        try
        {
            return assembly.GetTypes();
        }
        catch (System.Reflection.ReflectionTypeLoadException exception)
        {
            return exception.Types.OfType<Type>();
        }
    }
}
