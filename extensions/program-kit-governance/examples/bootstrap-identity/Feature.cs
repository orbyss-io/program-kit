using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace ProgramKit.Compatibility.Identity;

// Synthetic, bodyless permission boundary: no consumer membership or business effect.
[ShellFeature("Compatibility.Identity")]
public sealed class IdentityFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services) { }
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints.MapGet("/", () => Results.Text("Compatibility fixture")).AllowAnonymous();
        endpoints.MapGet("/api/permission-probe", () => Results.NoContent())
            .RequireAuthorization("permission:compatibility.read");
    }
}
