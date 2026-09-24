using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.WebDefaults;
namespace ProgramKit.Compatibility;

[ShellFeature("Compatibility.Default")]
public sealed class DefaultFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services) => services.AddSingleton<IProbePort, DefaultPort>();
    private sealed class DefaultPort : IProbePort { public string Read() => "default"; }
}
[ShellFeature("Compatibility.Alternate")]
public sealed class AlternateFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services) => services.AddSingleton<IProbePort, AlternatePort>();
    private sealed class AlternatePort : IProbePort { public string Read() => "alternate"; }
}
[ShellFeature("Compatibility.Api")]
public sealed class ApiFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services) { }
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        var group = endpoints.MapGroup("").WithMetadata(new WebResponseMetadata(Feature: "Compatibility.Api"));
        group.MapGet("/probe", (IProbePort port) => new ProbeResponse(port.Read()));
        group.MapPost("/probe", async (HttpContext http, JsonProfileCatalog profiles) =>
            await profiles.Get("strict-request").ReadAsync<ProbeRequest>(http.Request.Body, http.RequestAborted));
    }
}
public sealed record ProbeResponse(string Value);
public sealed record ProbeRequest(string Name);
