using CShells.AspNetCore.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using ObservatoryScheduling.Core.Contracts.Scheduling;

namespace ObservatoryScheduling.Scheduling.Api.Features;

/// <summary>Direct CShells API feature owning the fictional scheduling endpoint.</summary>
public sealed class SchedulingApiFeature : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
    }

    /// <inheritdoc />
    public void MapEndpoints(
        IEndpointRouteBuilder endpoints,
        IHostEnvironment? environment)
    {
        ArgumentNullException.ThrowIfNull(endpoints);
        _ = environment;
        _ = endpoints.MapPost(
            "/viewing-sessions",
            async (
                ViewingRequest request,
                IFirstAvailableScheduler scheduler,
                CancellationToken cancellationToken) =>
            {
                var session = await scheduler.ScheduleAsync(
                    request,
                    cancellationToken).ConfigureAwait(false);
                return session is null
                    ? Results.NotFound()
                    : Results.Ok(session);
            });
    }
}
