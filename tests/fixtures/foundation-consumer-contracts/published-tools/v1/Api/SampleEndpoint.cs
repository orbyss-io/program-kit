using Microsoft.AspNetCore.Http;
using Orbyss.Foundation.Json.AspNetCore;
using PublishedTools.Contract.Core;

namespace PublishedTools.Contract.Api;

/// <summary>Instance endpoint dependencies are resolved only by a real operation request.</summary>
public sealed class SampleEndpoint(UnstartedDataSource source, IJsonRequestReader<SampleRequest> requests,
    IJsonResponseFactory<SampleResponse> responses)
{
    /// <summary>This qualification never calls the operation or initializes its storage.</summary>
    public async Task<IResult> HandleAsync(HttpContext http)
    {
        _ = source;
        var request = await requests.ReadAsync(http, http.RequestAborted);
        var snapshot = new SampleSnapshot(new([request.Text]));
        return responses.Create(new(snapshot.Values));
    }
}
