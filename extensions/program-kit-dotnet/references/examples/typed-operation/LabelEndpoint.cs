using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Json.AspNetCore;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Resolved only for an admitted operation; cold OpenAPI export must not call it.</summary>
public sealed class LabelEndpoint(
    ILabelOperations operations,
    IJsonRequestReader<LabelRequest> requests,
    IJsonResponseFactory<LabelResponse> responses,
    IOptions<LabelApiOptions> options
)
{
    /// <summary>The small bodyless read returns the same stored resource representation.</summary>
    public async Task<IResult> ReadAsync(HttpContext http)
    {
        var prefix = options.Value.Prefix;
        var result = await operations.ReadAsync(http.RequestAborted);
        var response = new LabelResponse(prefix + result);
        return responses.Create(response);
    }

    /// <summary>Admits strict JSON before any durable write; no automatic submission retry.</summary>
    public async Task<IResult> WriteAsync(HttpContext http)
    {
        var request = await requests.ReadAsync(http, http.RequestAborted);
        var result = await operations.UpdateAsync(request.Policy, http.RequestAborted);
        var response = new LabelResponse(options.Value.Prefix + result);
        return responses.Create(response);
    }
}
