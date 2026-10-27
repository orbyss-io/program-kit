using System;
using System.Threading.Tasks;
using CShells;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;

namespace ProgramKit.Examples.TypedOperation.Operations.WriteLabel;

/// <summary>Owns WriteLabel admission, route metadata and request-scoped execution.</summary>
internal sealed class Endpoint(
    ILabelOperations operations,
    IJsonRequestReader<LabelRequest> requests,
    IJsonResponseFactory<LabelResponse> responses,
    IOptions<LabelApiOptions> options
)
{
    /// <summary>Registers this operation's deferred request factory.</summary>
    internal static void Configure(IServiceCollection services)
    {
        var profile = new JsonProfileKey("sample-label-request");
        var requirement = new JsonProfileRequirement(JsonProfileKeys.StrictRequest, maximumBytes: 1024);
        services.AddJsonRequestContract<LabelRequest>(profile, requirement);
        services.AddScoped<Endpoint>(CreateEndpoint);
    }

    /// <summary>Maps this operation with its stable identity and material outcomes.</summary>
    internal static void Map(IEndpointRouteBuilder endpoints)
    {
        endpoints
            .MapPost("/api/sample-label", WriteAsync)
            .WithName("WriteSampleLabel")
            .RequireAuthorization()
            .WithJsonRequest<LabelRequest>()
            .WithJsonResponse<LabelResponse>()
            .Produces<FoundationProblemEnvelope>(400, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(401, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(403, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(413, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(415, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(500, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(503, "application/problem+json");
    }

    /// <summary>Adapts this admitted request to the owned application capability.</summary>
    internal async Task<IResult> HandleAsync(HttpContext http)
    {
        var prefix = options.Value.Prefix;
        var request = await requests.ReadAsync(http, http.RequestAborted);
        var result = await operations.UpdateAsync(request.Policy, http.RequestAborted);
        var response = new LabelResponse(prefix + result);
        return responses.Create(response);
    }

    /// <summary>Resolves dependencies only in the admitted request scope.</summary>
    private static Endpoint CreateEndpoint(System.IServiceProvider provider)
    {
        var operations = provider.GetRequiredService<ILabelOperations>();
        var requests = provider.GetRequiredService<IJsonRequestReader<LabelRequest>>();
        var responses = provider.GetRequiredService<IJsonResponseFactory<LabelResponse>>();
        var options = provider.GetRequiredService<IOptions<LabelApiOptions>>();
        return new Endpoint(
            operations: operations,
            requests: requests,
            responses: responses,
            options: options
        );
    }

    /// <summary>Preserves explicit service binding at the HTTP boundary.</summary>
    private static Task<IResult> WriteAsync([FromServices] Endpoint endpoint, HttpContext http) => endpoint.HandleAsync(http);
}
