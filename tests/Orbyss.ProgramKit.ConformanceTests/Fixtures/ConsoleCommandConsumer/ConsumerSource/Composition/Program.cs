using GeneratedHost.Commands;
using GeneratedHost.Hosting;
using Microsoft.Extensions.DependencyInjection;

namespace GeneratedHost.Composition;

internal static partial class Program
{
    static partial void ConfigureProgramKitConsoleServices(
        IServiceCollection services)
    {
        services.AddSingleton<
            IFixtureLifecycleRecorder,
            FileFixtureLifecycleRecorder>();
        services.AddHostedService<FixtureHostedService>();
        services.AddSingleton<
            IFixtureExitCodePolicy,
            FixtureExitCodePolicy>();

        var registration = Environment.GetEnvironmentVariable(
            "PROGRAM_KIT_CONSOLE_FIXTURE_REGISTRATION");
        if (string.Equals(
                registration,
                "missing",
                StringComparison.Ordinal))
        {
            return;
        }

        services.AddSingleton<
            IProgramKitConsoleCommandDispatcher,
            FixtureConsoleCommandDispatcher>();
        if (string.Equals(
                registration,
                "duplicate",
                StringComparison.Ordinal))
        {
            services.AddSingleton<
                IProgramKitConsoleCommandDispatcher,
                FixtureConsoleCommandDispatcher>();
        }
    }
}
