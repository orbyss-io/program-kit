using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.OpenApi;

namespace PublishedTools.Contract.Api;

/// <summary>Exercises actual public Build descriptor emission and official exporter composition.</summary>
[ShellFeature("PublishedTools.Contract", DependsOn = [typeof(FoundationJsonFeature), typeof(FoundationOpenApiFeature)])]
public sealed class ContractFeature : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddSingleton<IJsonProfileExtension, ValueSequenceJsonExtension>();
        services.AddJsonRequestContract<SampleRequest>(new(JsonProfileKeys.StrictRequest),
            new(JsonProfileKeys.StrictRequest, maximumBytes: 4096));
        services.AddJsonResponseContract<SampleResponse>(new(JsonProfileKeys.SuccessResponse),
            new(JsonProfileKeys.TolerantResponse, maximumBytes: 8192));
        services.AddSingleton<UnstartedDataSource>();
        services.AddScoped<SampleEndpoint>();
        services.AddSingleton<IHostedService>(_ => throw new InvalidOperationException("PUBLISHED_TOOL_APPLICATION_INITIALIZER_RAN"));
    }

    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapPost("/sample", (HttpContext http, SampleEndpoint endpoint) => endpoint.HandleAsync(http))
            .WithName("PublishedTools_CreateSample")
            .WithJsonRequest<SampleRequest>().WithJsonResponse<SampleResponse>();
}
