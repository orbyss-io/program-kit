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
        var optionsBuilder = services.AddOptions<LabelApiOptions>();
        var configuration = settings.GetConfigurationRoot();
        var section = configuration.GetSection("Sample:Api");
        optionsBuilder
            .Bind(section)
            .Validate(value => value.Prefix.Length is > 0 and <= 32, "Sample:Api:Prefix is required.");
        var requestProfile = new JsonProfileKey("sample-label-request");
        var requestRequirement = new JsonProfileRequirement(JsonProfileKeys.StrictRequest, maximumBytes: 1024);
        services.AddJsonRequestContract<LabelRequest>(requestProfile, requestRequirement);
        var responseProfile = new JsonProfileKey("sample-label-response");
        var responseRequirement = new JsonProfileRequirement(JsonProfileKeys.TolerantResponse, maximumBytes: 2048);
        services.AddJsonResponseContract<LabelResponse>(responseProfile, responseRequirement);
        services.AddScoped<LabelEndpoint>(CreateEndpoint);
    }

    /// <summary>Publishes typed wire contracts; service parameters are explicitly excluded from request binding.</summary>
    public static void Map(IEndpointRouteBuilder endpoints)
    {
        endpoints
            .MapGet("/api/sample-label", ReadAsync)
            .WithName("ReadSampleLabel")
            .RequireAuthorization()
            .WithJsonResponse<LabelResponse>()
            .Produces<FoundationProblemEnvelope>(401, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(403, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(500, "application/problem+json")
            .Produces<FoundationProblemEnvelope>(503, "application/problem+json");
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

    /// <summary>Resolves operation dependencies only in the admitted request scope.</summary>
    private static LabelEndpoint CreateEndpoint(System.IServiceProvider provider)
    {
        var operations = provider.GetRequiredService<ILabelOperations>();
        var requests = provider.GetRequiredService<IJsonRequestReader<LabelRequest>>();
        var responses = provider.GetRequiredService<IJsonResponseFactory<LabelResponse>>();
        var options = provider.GetRequiredService<IOptions<LabelApiOptions>>();
        return new LabelEndpoint(
            operations: operations,
            requests: requests,
            responses: responses,
            options: options
        );
    }

    /// <summary>Delegates the admitted bodyless read without changing its transport metadata.</summary>
    private static Task<IResult> ReadAsync([FromServices] LabelEndpoint endpoint, HttpContext http) =>
        endpoint.ReadAsync(http);

    /// <summary>Delegates the admitted write without changing its transport metadata.</summary>
    private static Task<IResult> WriteAsync([FromServices] LabelEndpoint endpoint, HttpContext http) =>
        endpoint.WriteAsync(http);
}

