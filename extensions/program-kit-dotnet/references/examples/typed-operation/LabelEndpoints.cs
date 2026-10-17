using System.Threading.Tasks;
using CShells;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Called by the selected API feature; never resolve providers during registration.</summary>
public static class LabelEndpoints
{
    /// <summary>Registers complete strict request/response contracts and deferred operation dependencies.</summary>
    public static void Configure(IServiceCollection services, ShellSettings settings)
    {
        services.AddOptions<LabelApiOptions>().Bind(settings.GetConfigurationRoot().GetSection("Sample:Api"))
            .Validate(value => value.Prefix.Length is > 0 and <= 32, "Sample:Api:Prefix is required.");
        services.AddJsonRequestContract<LabelRequest>(new("sample-label-request"),
            new(JsonProfileKeys.StrictRequest, maximumBytes: 1024));
        services.AddJsonResponseContract<LabelResponse>(new("sample-label-response"),
            new(JsonProfileKeys.TolerantResponse, maximumBytes: 2048));
        services.AddScoped(provider => new LabelEndpoint(provider.GetRequiredService<ILabelStore>(),
            provider.GetRequiredService<IJsonRequestReader<LabelRequest>>(),
            provider.GetRequiredService<IJsonResponseFactory<LabelResponse>>(),
            provider.GetRequiredService<IOptions<LabelApiOptions>>()));
    }

    /// <summary>Publishes typed wire contracts; service parameters are explicitly excluded from request binding.</summary>
    public static void Map(IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGet("/api/sample-label", ([FromServices] LabelEndpoint endpoint, HttpContext http) => endpoint.ReadAsync(http))
            .WithName("ReadSampleLabel").RequireAuthorization().WithJsonResponse<LabelResponse>()
            .Produces<FoundationProblemEnvelope>(401, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(403, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(500, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(503, "application/problem+json");
        endpoints.MapPost("/api/sample-label", ([FromServices] LabelEndpoint endpoint, HttpContext http) => endpoint.WriteAsync(http))
            .WithName("WriteSampleLabel").RequireAuthorization().WithJsonRequest<LabelRequest>().WithJsonResponse<LabelResponse>()
            .Produces<FoundationProblemEnvelope>(400, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(401, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(403, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(413, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(415, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(500, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(503, "application/problem+json");
    }
}

