using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Json.AspNetCore;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Resolved only for an admitted operation; cold OpenAPI export must not call it.</summary>
public sealed class LabelEndpoint(ILabelStore store, IJsonRequestReader<LabelRequest> requests,
    IJsonResponseFactory<LabelResponse> responses, IOptions<LabelApiOptions> options)
{
    /// <summary>The small bodyless read returns the same stored resource representation.</summary>
    public async Task<IResult> ReadAsync(HttpContext http) => responses.Create(
        new(options.Value.Prefix + await store.ReadAsync(http.RequestAborted)));

    /// <summary>Admits strict JSON before any durable write; no automatic submission retry.</summary>
    public async Task<IResult> WriteAsync(HttpContext http)
    {
        var request = await requests.ReadAsync(http, http.RequestAborted);
        await store.WriteAsync(request.Policy, http.RequestAborted);
        return responses.Create(new(options.Value.Prefix + await store.ReadAsync(http.RequestAborted)));
    }
}
