using CShells.Lifecycle;

namespace ProgramKit.Host.Shells;

/// <summary>Activates configured shells before the host reports readiness.</summary>
internal sealed class EagerShellActivationHostedService(
    IShellRegistry registry,
    IConfiguration configuration,
    ILogger<EagerShellActivationHostedService> logger) : IHostedService
{
    /// <inheritdoc />
    public async Task StartAsync(CancellationToken cancellationToken)
    {
        if (configuration.GetValue("ProgramKit:Boot:EagerShellActivation", defaultValue: true) is false)
            return;

        var failFast = configuration.GetValue("ProgramKit:Boot:FailOnShellActivationError", defaultValue: true);
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
    }

    /// <inheritdoc />
    public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;
}
