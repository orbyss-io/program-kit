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
        var group = endpoints.MapGroup("");
        var metadata = new WebResponseMetadata(Feature: "Compatibility.Api");
        group = group.WithMetadata(metadata);
        Func<IProbePort, ProbeResponse> readProbe = ReadProbe;
        group.MapGet("/probe", readProbe);
        Func<HttpContext, JsonProfileCatalog, Task<ProbeRequest>> readRequest = ReadRequestAsync;
        group.MapPost("/probe", readRequest);
    }

    /// <summary>Reads the selected provider without changing its owned result.</summary>
    private static ProbeResponse ReadProbe(IProbePort port)
    {
        var value = port.Read();
        return new ProbeResponse(value);
    }

    /// <summary>Reads with the selected profile and caller cancellation; asynchronous faults remain captured.</summary>
    private static async Task<ProbeRequest> ReadRequestAsync(HttpContext http, JsonProfileCatalog profiles)
    {
        var profile = profiles.Get("strict-request");
        var request = await profile.ReadAsync<ProbeRequest>(http.Request.Body, http.RequestAborted);
        return request;
    }
}
public sealed record ProbeResponse(string Value);
public sealed record ProbeRequest(string Name);
