using CShells.Lifecycle;
using ProgramKit.Host.Bundles;

namespace ProgramKit.Host.Health;

/// <summary>Maps Program Kit liveness, readiness, and bundle-inspection endpoints.</summary>
internal static class HealthEndpoints
{
    /// <summary>Maps the Program Kit operational endpoints.</summary>
    /// <param name="endpoints">The endpoint route builder.</param>
    /// <returns>The supplied endpoint route builder.</returns>
    public static IEndpointRouteBuilder MapProgramKitHealth(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGet("/health/live", () => Results.Ok(new { status = "live" }));
        endpoints.MapGet("/_program-kit/bundle", (ApplicationBundle bundle) => Results.Ok(new
        {
            id = bundle.Manifest.BundleId,
            version = bundle.Manifest.Version,
            digest = bundle.Digest,
            hostApi = bundle.Manifest.HostApi
        }));
        endpoints.MapGet("/health/ready", (IShellRegistry registry, IConfiguration configuration, ApplicationBundle bundle) =>
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
            var ready = shells.Length > 0 && shells.All(shell => shell.active);
            return Results.Json(
                new
                {
                    status = ready ? "ready" : "not-ready",
                    bundle = new { id = bundle.Manifest.BundleId, version = bundle.Manifest.Version, digest = bundle.Digest },
                    shells
                },
                statusCode: ready ? StatusCodes.Status200OK : StatusCodes.Status503ServiceUnavailable);
        });
        return endpoints;
    }
}
