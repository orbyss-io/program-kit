using CShells.Lifecycle;
using ProgramKit.Host.Bundles;
using ProgramKit.Host.Web;

namespace ProgramKit.Host.Health;

/// <summary>Maps Program Kit liveness, readiness, and bundle-inspection endpoints.</summary>
internal static class HealthEndpoints
{
    /// <summary>Maps the Program Kit operational endpoints.</summary>
    /// <param name="endpoints">The endpoint route builder.</param>
    /// <returns>The supplied endpoint route builder.</returns>
    public static IEndpointRouteBuilder MapProgramKitHealth(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGet("/health/live", () => Results.Ok(new { status = "live" })).AllowAnonymous();
        endpoints.MapGet("/_program-kit/bundle", (ApplicationBundle bundle) => Results.Ok(new
        {
            id = bundle.Manifest.BundleId,
            version = bundle.Manifest.Version,
            digest = bundle.Digest,
            hostApi = bundle.Manifest.HostApi
        }));
        endpoints.MapGet("/health/ready", (IShellRegistry registry, IConfiguration configuration, IdentityReadinessState identity) =>
        {
            var shells = configuration.GetSection("CShells:Shells").GetChildren()
                .Select(child => child.Key)
                .Where(name => !string.IsNullOrWhiteSpace(name))
                .Select(name =>
                {
                    var active = registry.GetActive(name);
                    return new
                    {
                        name,
                        state = active?.State.ToString() ?? "Inactive",
                        generation = active?.Descriptor.Generation,
                        active = active?.State == ShellLifecycleState.Active
                    };
                })
                .ToArray();
            var shellsReady = shells.Length > 0 && shells.All(shell => shell.active);
            var ready = shellsReady && identity.IsReady;
            return Results.Json(
                new
                {
                    status = ready ? "ready" : "not-ready",
                    checks = new
                    {
                        runtime = shellsReady ? "ready" : "not-ready",
                        identity = identity.IsReady ? "ready" : "not-ready"
                    }
                },
                statusCode: ready ? StatusCodes.Status200OK : StatusCodes.Status503ServiceUnavailable);
        }).AllowAnonymous();
        return endpoints;
    }
}
