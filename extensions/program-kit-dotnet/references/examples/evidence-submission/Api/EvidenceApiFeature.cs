using CShells;
using CShells.AspNetCore.Features;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;

namespace ProgramKit.Examples.Evidence;

/// <summary>Owns typed wire registration, endpoint metadata and activation admission.</summary>
[ShellFeature("Evidence.Api", DependsOn = [typeof(FoundationJsonFeature)])]
public sealed class EvidenceApiFeature(ShellSettings settings) : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        var configuration = settings.GetConfigurationRoot();
        var section = configuration.GetSection("Evidence:Api");
        var options = services.AddOptions<EvidenceApiOptions>();
        options
            .Bind(section)
            .Validate(value => value.Desk.Length is > 0 and <= 40, "Evidence desk is required.");
        services.AddShellInitializer<EvidenceOptionsAdmission>(LifecyclePhase.Prepare, 0);
        var requestKey = new JsonProfileKey("evidence-request");
        var request = JsonContractFactory.Request<EvidenceRequest>(maximumBytes: 32768, profile: requestKey);
        services.AddJsonContract(request);
        var responseKey = new JsonProfileKey("evidence-response");
        var response = JsonContractFactory.Response<EvidenceResponse>(maximumBytes: 2048, profile: responseKey);
        services.AddJsonContract(response);
        var inputContract = JsonContractFactory.Response<EvidenceInputContract>(maximumBytes: 2048, profile: responseKey);
        services.AddJsonContract(inputContract);
        services.AddScoped<EvidenceEndpoint>();
    }

    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints
            .MapGet("/api/evidence-input", InputContract)
            .WithName("ReadEvidenceInputContract")
            .RequireAuthorization()
            .WithJsonResponse<EvidenceInputContract>();
        endpoints
            .MapPost("/api/evidence", PrepareAsync)
            .WithName("PrepareEvidence")
            .RequireAuthorization()
            .WithJsonRequest<EvidenceRequest>()
            .WithJsonResponse<EvidenceResponse>()
            .ProducesProblem(400)
            .ProducesProblem(413);
        endpoints
            .MapPost("/api/evidence/{identity}/accept", AcceptAsync)
            .WithName("AcceptEvidence")
            .RequireAuthorization()
            .WithJsonResponse<EvidenceResponse>()
            .ProducesProblem(404);
        endpoints
            .MapGet("/api/evidence/{identity}", FindAsync)
            .WithName("FindEvidence")
            .RequireAuthorization()
            .WithJsonResponse<EvidenceResponse>()
            .ProducesProblem(404);
    }

    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private static IResult InputContract([FromServices] IJsonResponseFactory<EvidenceInputContract> responses)
    {
        var maximumBytes = EvidencePacket.MaximumContentBytes;
        var maximumTitle = EvidencePacket.MaximumTitleLength;
        var contract = new EvidenceInputContract(maximumBytes, maximumTitle);
        return responses.Create(contract);
    }

    /// <summary>Admits and retains one immutable owned preparation.</summary>
    private static Task<IResult> PrepareAsync([FromServices] EvidenceEndpoint endpoint, HttpContext http) =>
        endpoint.PrepareAsync(http);

    /// <summary>Accepts the retained owned identity without repeating its established effect.</summary>
    private static Task<IResult> AcceptAsync([FromServices] EvidenceEndpoint endpoint, HttpContext http) =>
        endpoint.AcceptAsync(http);

    /// <summary>Observes the existing owned submission without a new business effect.</summary>
    private static Task<IResult> FindAsync([FromServices] EvidenceEndpoint endpoint, HttpContext http) =>
        endpoint.FindAsync(http);
}
