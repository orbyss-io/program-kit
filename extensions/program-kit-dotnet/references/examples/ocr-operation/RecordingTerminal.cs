namespace ProgramKit.Examples.Ocr;

/// <summary>Offline terminal transport with no socket, DNS, credential or provider access.</summary>
public sealed class RecordingTerminal(Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>> respond) : HttpMessageHandler
{
    private int calls;
    /// <summary>Gets actual terminal dispatches; handler admission is counted separately.</summary>
    public int Calls => Volatile.Read(ref calls);
    /// <inheritdoc />
    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        Interlocked.Increment(ref calls);
        return respond(request,cancellationToken);
    }
}
