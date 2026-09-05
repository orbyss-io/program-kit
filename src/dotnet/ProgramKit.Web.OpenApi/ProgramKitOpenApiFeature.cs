using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace ProgramKit.Web.OpenApi;

/// <summary>Registers and maps the optional shell-owned Program Kit OpenAPI document.</summary>
[ShellFeature(
    name: "ProgramKit.Web.OpenApi",
    DisplayName = "Program Kit OpenAPI",
    Description = "Provides the default shell-owned OpenAPI document endpoint.")]
public sealed class ProgramKitOpenApiFeature : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services) => services.AddOpenApi("v1");

    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapOpenApi("/_program-kit/openapi/{documentName}.json");
}
