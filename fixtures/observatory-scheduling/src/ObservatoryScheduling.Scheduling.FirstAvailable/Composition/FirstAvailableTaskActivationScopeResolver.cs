using CShells.Lifecycle;
using Orbyss.ProgramKit.Tasks.Activation;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Composition;

internal sealed class FirstAvailableTaskActivationScopeResolver :
    ITaskActivationScopeResolver
{
    private readonly IShellRegistry shellRegistry;
    private readonly string shellName;

    public FirstAvailableTaskActivationScopeResolver(
        IShellRegistry shellRegistry,
        string shellName)
    {
        this.shellRegistry = shellRegistry ??
            throw new ArgumentNullException(nameof(shellRegistry));
        if (string.IsNullOrWhiteSpace(shellName))
        {
            throw new ArgumentException(
                "A shell name is required.",
                nameof(shellName));
        }

        this.shellName = shellName;
    }

    public ValueTask<ITaskActivationScope> CreateScopeAsync(
        TaskActivationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        if (request.ActivationIdentity !=
                FirstAvailableTaskContracts.Binding.ActivationIdentity ||
            request.OwningFeatureRevision !=
                FirstAvailableTaskContracts.FeatureRevision ||
            request.HandlerRevision !=
                FirstAvailableTaskContracts.HandlerRevision)
        {
            throw new InvalidOperationException(
                "The first-available feature cannot resolve the requested task activation.");
        }

        var shell = shellRegistry.GetActive(shellName) ??
            throw new InvalidOperationException(
                $"The selected CShell '{shellName}' is not active.");
        var scope = shell.BeginScope();
        ITaskActivationScope result =
            new FirstAvailableTaskActivationScope(
                scope,
                scope.ServiceProvider);
        return ValueTask.FromResult(result);
    }
}
