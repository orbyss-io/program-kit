using System.Globalization;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Json.AspNetCore;

namespace ProgramKit.Examples.Evidence;

/// <summary>HTTP admission/mapping only. The application/provider own transitions and effects.</summary>
public sealed class EvidenceEndpoint(
    IEvidenceSubmissions submissions,
    IJsonRequestReader<EvidenceRequest> requests,
    IJsonResponseFactory<EvidenceResponse> responses,
    IOptions<EvidenceApiOptions> options
)
{
    /// <summary>Admits and retains one immutable owned preparation.</summary>
    public async Task<IResult> PrepareAsync(HttpContext http)
    {
        var request = await requests.ReadAsync(http, http.RequestAborted);
        EvidencePacket packet;
        try
        {
            var date = DateOnly.ParseExact(
                request.Date,
                "yyyy-MM-dd",
                CultureInfo.InvariantCulture
            );
            var content = Convert.FromBase64String(request.Content);
            packet = EvidencePacket.Create(
                request.Title,
                date,
                content
            );
        }
        catch (Exception error) when (error is FormatException or ArgumentException)
        {
            return Results.Problem(statusCode: 400, title: "Evidence input is invalid.");
        }
        var owner = http.User.Identity!.Name!;
        var result = await submissions.PrepareAsync(
            owner,
            packet,
            http.RequestAborted
        );
        return Map(result);
    }

    /// <summary>Accepts the retained owned identity without repeating its established effect.</summary>
    public async Task<IResult> AcceptAsync(HttpContext http)
    {
        var owner = http.User.Identity!.Name!;
        var identity = (string)http.Request.RouteValues["identity"]!;
        var result = await submissions.AcceptAsync(
            owner,
            identity,
            http.RequestAborted
        );
        return result is null ? Missing() : Map(result);
    }

    /// <summary>Observes the existing owned submission without a new business effect.</summary>
    public async Task<IResult> FindAsync(HttpContext http)
    {
        var owner = http.User.Identity!.Name!;
        var identity = (string)http.Request.RouteValues["identity"]!;
        var result = await submissions.FindAsync(
            owner,
            identity,
            http.RequestAborted
        );
        return result is null ? Missing() : Map(result);
    }

    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private static IResult Missing() => Results.Problem(statusCode: 404, title: "Evidence unavailable.");

    /// <summary>Keeps the named admission or projection step within its owning type.</summary>
    private IResult Map(EvidenceReceipt receipt)
    {
        var date = receipt.Date.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        var desk = options.Value.Desk;
        var response = new EvidenceResponse(
            receipt.Id,
            receipt.Title,
            date,
            receipt.Hash,
            receipt.Accepted,
            desk
        );
        return responses.Create(response);
    }
}
