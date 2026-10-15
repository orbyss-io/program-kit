using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using Orbyss.Foundation.Web.OpenApi;
using System.Text.Json.Serialization;

namespace Numeric.Contract.Api;

[ShellFeature("Numeric.Contract", DependsOn = [typeof(FoundationJsonFeature), typeof(FoundationOpenApiFeature), typeof(EffectOnlyFeature)])]
public sealed class NumericFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddJsonRequestContract<ScopedNumericRequest>(new(JsonProfileKeys.StrictRequest),
            new(JsonProfileKeys.StrictRequest, maximumBytes: 4096));
        services.AddJsonResponseContract<ScopedNumericRequest>(new(JsonProfileKeys.SuccessResponse),
            new(JsonProfileKeys.TolerantResponse, maximumBytes: 8192));
        services.AddScoped<NumericEndpoint>();
        services.AddSingleton<IHostedService>(_ => throw new InvalidOperationException("NUMERIC_BUSINESS_EXECUTION_STARTED"));
    }
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapPost("/numeric", (HttpContext http, [FromServices] NumericEndpoint endpoint) => endpoint.Handle(http))
            .WithName("Numeric_Create")
            .WithJsonRequest<ScopedNumericRequest>().WithJsonResponse<ScopedNumericRequest>()
            .Produces<NumericProblem>(400, "application/problem+json")
            .Produces<NumericProblem>(401, "application/problem+json")
            .Produces<NumericProblem>(403, "application/problem+json")
            .Produces<NumericProblem>(500, "application/problem+json");
}

public sealed class NumericEndpoint
{
    public IResult Handle(HttpContext http) => throw new InvalidOperationException("NUMERIC_BUSINESS_EFFECT_EXECUTED");
}

[JsonNumberHandling(JsonNumberHandling.Strict)]
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record ScopedNumericRequest(decimal Amount, int Count,
    decimal[] Amounts, ScopedNumericChild Child);
[ShellFeature("Numeric.NullableContract", DependsOn = [typeof(FoundationJsonFeature), typeof(FoundationOpenApiFeature), typeof(EffectOnlyFeature)])]
public sealed class NullableNumericFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddJsonRequestContract<ScopedNullableNumericRequest>(new(JsonProfileKeys.StrictRequest),
            new(JsonProfileKeys.StrictRequest, maximumBytes: 4096));
        services.AddJsonResponseContract<ScopedNullableNumericRequest>(new(JsonProfileKeys.SuccessResponse),
            new(JsonProfileKeys.TolerantResponse, maximumBytes: 8192));
    }
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapPost("/nullable-numeric", (HttpContext http) => Reject(http))
            .WithName("Numeric_NullableProbe")
            .WithJsonRequest<ScopedNullableNumericRequest>().WithJsonResponse<ScopedNullableNumericRequest>()
            .Produces<NumericProblem>(400, "application/problem+json").Produces<NumericProblem>(500, "application/problem+json");
    private static IResult Reject(HttpContext http) => throw new InvalidOperationException("NUMERIC_BUSINESS_EFFECT_EXECUTED");
}
[JsonNumberHandling(JsonNumberHandling.Strict)]
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record ScopedNullableNumericRequest([property: JsonNumberHandling(JsonNumberHandling.Strict)] int? OptionalCount);
[JsonNumberHandling(JsonNumberHandling.Strict)]
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record ScopedNumericChild(long Revision);
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
[JsonNumberHandling(JsonNumberHandling.Strict)]
public sealed record NumericProblem(string Type, string Title, int Status, string Code,
    string CorrelationId, string TraceId, NumericFieldError[] FieldErrors,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Detail = null);
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record NumericFieldError(string Field, string Code, string Message);

// Effect-only provider: selected as a real dependency, with no routes or
// connection inputs. Cold metadata composition must not invoke registration.
[ShellFeature("Numeric.EffectOnly")]
public sealed class EffectOnlyFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services) =>
        throw new InvalidOperationException("NUMERIC_EFFECT_ONLY_CONFIGURE_SERVICES_RAN");
}
