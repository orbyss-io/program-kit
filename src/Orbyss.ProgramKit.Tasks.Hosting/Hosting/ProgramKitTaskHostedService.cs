using Microsoft.Extensions.Hosting;
using Orbyss.ProgramKit.Tasks.Coordination;

namespace Orbyss.ProgramKit.Tasks.Hosting.Hosting;

internal sealed class ProgramKitTaskHostedService : IHostedService
{
    private readonly ITaskRuntimeControl runtime;
    private readonly Composition.TaskHostingOptions options;

    public ProgramKitTaskHostedService(
        ITaskRuntimeControl runtime,
        Composition.TaskHostingOptions options)
    {
        this.runtime = runtime ??
            throw new ArgumentNullException(nameof(runtime));
        this.options = options ??
            throw new ArgumentNullException(nameof(options));
    }

    public Task StartAsync(CancellationToken cancellationToken) =>
        runtime.StartAsync(cancellationToken).AsTask();

    public Task StopAsync(CancellationToken cancellationToken) =>
        runtime.StopAsync(
            options.DrainOnShutdown,
            cancellationToken).AsTask();
}
