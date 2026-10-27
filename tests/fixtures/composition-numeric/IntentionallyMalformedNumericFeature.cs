using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.OpenApi;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.OpenApi;

namespace Numeric.Contract.Api;

/// <summary>Deliberately publishes contradictory numeric metadata to exercise the native contract-admission guard.</summary>
[ShellFeature("Numeric.IntentionallyMalformed", DependsOn = [typeof(FoundationJsonFeature), typeof(FoundationOpenApiFeature), typeof(EffectOnlyFeature)])]
public sealed class IntentionallyMalformedNumericFeature : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        var request = new JsonProfileKey(JsonProfileKeys.StrictRequest);
        var response = new JsonProfileKey(JsonProfileKeys.SuccessResponse);
        var input = new JsonProfileRequirement(JsonProfileKeys.StrictRequest, maximumBytes: 4096);
        var output = new JsonProfileRequirement(JsonProfileKeys.TolerantResponse, maximumBytes: 8192);
        services.AddJsonRequestContract<ScopedNullableNumericRequest>(request, input);
        services.AddJsonResponseContract<ScopedNullableNumericRequest>(response, output);
        services.Configure<OpenApiOptions>("v1", ConfigureOpenApi);
    }

    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints
            .MapPost("/intentionally-malformed-numeric", Reject)
            .WithName("Numeric_IntentionallyMalformed")
            .WithJsonRequest<ScopedNullableNumericRequest>()
            .WithJsonResponse<ScopedNullableNumericRequest>()
            .Produces<NumericProblem>(400, "application/problem+json")
            .Produces<NumericProblem>(500, "application/problem+json");
    }

    /// <summary>Registers the isolated fixture defect after normal Foundation schema policy.</summary>
    private static void ConfigureOpenApi(OpenApiOptions options) =>
        options.AddSchemaTransformer<IntentionallyMalformedNumericSchemaTransformer>();

    /// <summary>Forbids business execution in this metadata-only negative fixture.</summary>
    private static IResult Reject(HttpContext http) => throw new InvalidOperationException("NUMERIC_BUSINESS_EFFECT_EXECUTED");
}
