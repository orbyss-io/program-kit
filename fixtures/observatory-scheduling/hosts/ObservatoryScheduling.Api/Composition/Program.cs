using CShells.AspNetCore.Extensions;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Composition;
using Orbyss.ProgramKit.Modularity.Contributions;
using Orbyss.ProgramKit.Modularity.InProcess.Contributions;
using Orbyss.ProgramKit.Modularity.InProcess.Middleware;
using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Modularity.Ordering;
using Orbyss.ProgramKit.Tasks.Hosting.Composition;
using Orbyss.ProgramKit.Tasks.InProcess.Composition;
using ObservatoryScheduling.Constraints.DarknessWindow.Features;
using ObservatoryScheduling.Core.Configuration;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Scheduling.Api.Features;
using ObservatoryScheduling.Scheduling.FirstAvailable.Composition;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;
using ObservatoryScheduling.Visibility.Fixed.Features;

namespace ObservatoryScheduling.Api.Composition;

internal static class Program
{
    private static async Task Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);
        ConfigureFixtureServices(builder.Services);
        builder.WebHost.ConfigureKestrel(
            static options => options.ListenLocalhost(43101));
        builder.AddShells(
            static cshells =>
                cshells.AddShell(
                    "observatory-api",
                    static shell =>
                    {
                        shell.WithFeature<StaticVisibilityFeature>();
                        shell.WithFeature<DarknessWindowFeature>();
                        shell.WithFeature<FirstAvailableFeature>();
                        shell.WithFeature<SchedulingApiFeature>();
                    }));
        var app = builder.Build();
        MapHealth(app);
        app.MapShells();
        await app.RunAsync().ConfigureAwait(false);
    }

    private static void ConfigureFixtureServices(IServiceCollection services)
    {
        services.AddSingleton<
            IProgramKitMiddlewarePipeline<ViewingRequest, ViewingSession?>>(
            static _ => CreateSchedulingPipeline());
        services.AddSingleton<IDomainContributionPublisher>(
            static _ => CreateContributionPublisher());
        services.AddFirstAvailableTaskActivation("observatory-api");
        services.UseInProcessTaskRuntime(
            new InProcessTaskRuntimeOptions
            {
                RuntimeRevision = FirstAvailableTaskContracts.RuntimeRevision,
            });
        services.AddProgramKitTaskHosting(new TaskHostingOptions());
    }

    private static InProcessMiddlewarePipeline<ViewingRequest, ViewingSession?>
        CreateSchedulingPipeline()
    {
        var validator = new ArtifactReferenceValidator();
        var factory = new MiddlewareRegistryFactory(validator);
        var descriptor = new ModularityRegistrationDescriptor(
            ObservatoryRevisions.Reference(
                "pkid:middleware:fixture:first-available-selection"),
            ObservatoryRevisions.Reference(
                "pkid:package:fixture:observatory-scheduling-first-available").Identity,
            ModularityOrderDescriptor.Default);
        var registry = factory.Create(
            [
                new MiddlewareRegistration<ViewingRequest, ViewingSession?>(
                    descriptor,
                    new FirstAvailableSelectionMiddleware()),
            ]);
        return new InProcessMiddlewarePipeline<ViewingRequest, ViewingSession?>(
            registry);
    }

    private static InProcessDomainContributionPublisher
        CreateContributionPublisher()
    {
        var validator = new ArtifactReferenceValidator();
        var factory = new DomainContributionRegistryFactory(validator);
        return new InProcessDomainContributionPublisher(factory.Create([]));
    }

    private static void MapHealth(WebApplication app)
    {
        var liveness = new HealthCheckOptions
        {
            AllowCachingResponses = false,
            Predicate = static _ => false,
            ResultStatusCodes =
            {
                [HealthStatus.Healthy] = StatusCodes.Status200OK,
                [HealthStatus.Degraded] = StatusCodes.Status200OK,
                [HealthStatus.Unhealthy] = StatusCodes.Status503ServiceUnavailable,
            },
        };
        var readiness = new HealthCheckOptions
        {
            AllowCachingResponses = false,
            Predicate = static registration =>
                registration.Tags.Contains("ready", StringComparer.Ordinal),
            ResultStatusCodes =
            {
                [HealthStatus.Healthy] = StatusCodes.Status200OK,
                [HealthStatus.Degraded] = StatusCodes.Status200OK,
                [HealthStatus.Unhealthy] = StatusCodes.Status503ServiceUnavailable,
            },
        };
        _ = app.MapHealthChecks("/health/live", liveness);
        _ = app.MapHealthChecks("/health/ready", readiness);
    }
}
