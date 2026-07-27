using Microsoft.Extensions.Hosting;

namespace GeneratedHost.Commands;

internal sealed class FixtureConsoleCommandDispatcher :
    IProgramKitConsoleCommandDispatcher
{
    private readonly IFixtureExitCodePolicy exitCodePolicy;
    private readonly IHostApplicationLifetime applicationLifetime;

    public FixtureConsoleCommandDispatcher(
        IFixtureExitCodePolicy exitCodePolicy,
        IHostApplicationLifetime applicationLifetime)
    {
        this.exitCodePolicy = exitCodePolicy;
        this.applicationLifetime = applicationLifetime;
    }

    public async ValueTask<int> DispatchAsync(
        GeneratedConsoleParseResult parseResult,
        CancellationToken cancellationToken)
    {
        var mode = parseResult.Options["mode"][0];
        var value = parseResult.Options["value"][0];
        if (string.Equals(mode, "throw", StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Fixture dispatcher failure after host start.");
        }

        if (string.Equals(mode, "cancel", StringComparison.Ordinal))
        {
            applicationLifetime.StopApplication();
            await Task.Yield();
        }

        global::System.Console.Out.WriteLine(
            string.Concat(
                "dispatch|command=",
                parseResult.Command,
                "|argument=",
                parseResult.Arguments[0],
                "|mode=",
                mode,
                "|value=",
                value,
                "|cancelled=",
                cancellationToken.IsCancellationRequested
                    ? "true"
                    : "false",
                "|service=constructor-injected"));
        return exitCodePolicy.Resolve(parseResult.Arguments[0]);
    }
}
