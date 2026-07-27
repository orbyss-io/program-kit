using Microsoft.Extensions.Hosting;

namespace GeneratedHost.Hosting;

internal sealed class FixtureHostedService : IHostedService
{
    private readonly IFixtureLifecycleRecorder recorder;

    public FixtureHostedService(IFixtureLifecycleRecorder recorder)
    {
        this.recorder = recorder;
    }

    public Task StartAsync(CancellationToken cancellationToken)
    {
        recorder.Record("start");
        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        recorder.Record(
            string.Concat(
                "stop|cancellable=",
                cancellationToken.CanBeCanceled
                    ? "true"
                    : "false"));
        return Task.CompletedTask;
    }
}
