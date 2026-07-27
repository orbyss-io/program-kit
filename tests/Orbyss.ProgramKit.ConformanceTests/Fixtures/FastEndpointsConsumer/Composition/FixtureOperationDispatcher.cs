using GeneratedHost.Hosting;
using Microsoft.AspNetCore.Http;

namespace GeneratedHost.Composition;

internal sealed class FixtureOperationDispatcher :
    IProgramKitFastEndpointOperationDispatcher
{
    public ValueTask DispatchAsync(
        string operationRevision,
        HttpContext context,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (operationRevision == "failure")
        {
            throw new InvalidOperationException(
                "This message must never enter the response.");
        }

        context.Response.StatusCode = StatusCodes.Status204NoContent;
        return ValueTask.CompletedTask;
    }
}
