using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.ProblemDetails;

namespace ProgramKit.Examples.TypedOperation.Operations.ReadLabel;

/// <summary>Owns ReadLabel admission, route metadata and request-scoped execution.</summary>
internal sealed class Endpoint(
    ILabelOperations operations,
    IJsonResponseFactory<LabelResponse> responses,
    IOptions<LabelApiOptions> options
)
{
    /// <summary>Owns the stable HTTP route.</summary>
    internal const string Route = "/api/sample-label";

    /// <summary>Owns the published operation identity.</summary>
    internal const string Name = "ReadSampleLabel";

    /// <summary>Declares actual native JSON/authentication and application failure statuses.</summary>
    private static readonly int[] failureStatuses =
    [
        StatusCodes.Status401Unauthorized,
        StatusCodes.Status403Forbidden,
        StatusCodes.Status500InternalServerError,
        StatusCodes.Status503ServiceUnavailable,
    ];

    /// <summary>Registers this operation's deferred request factory.</summary>
    internal static void Configure(IServiceCollection services)
    {
        services.AddJsonContract(LabelResponse.Contract);

        services.AddJsonEndpoint<Endpoint>();
    }

    /// <summary>Maps this operation with its stable identity and material outcomes.</summary>
    internal static void Map(IEndpointRouteBuilder endpoints)
    {
        endpoints
            .MapGet(Route, ReadAsync)
            .WithName(Name)
            .RequireAuthorization()
            .WithJsonResponse(LabelResponse.Contract)
            .ProducesFoundationProblemStatuses(failureStatuses);
    }

    /// <summary>Adapts this admitted request to the owned application capability.</summary>
    internal async Task<IResult> HandleAsync(HttpContext http)
    {
        var prefix = options.Value.Prefix;

        var result = await operations.ReadAsync(http.RequestAborted);
        var response = new LabelResponse(prefix + result);

        return responses.Create(response);
    }

    /// <summary>Preserves explicit service binding at the HTTP boundary.</summary>
    private static Task<IResult> ReadAsync([FromServices] Endpoint endpoint, HttpContext http) => endpoint.HandleAsync(http);
}
