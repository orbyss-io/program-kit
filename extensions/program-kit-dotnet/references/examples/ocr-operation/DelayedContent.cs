using System.Net;

namespace ProgramKit.Examples.Ocr;

/// <summary>Recording-only acknowledgement body used to observe a real cancellation boundary.</summary>
public sealed class DelayedContent(CancellationToken deadline) : HttpContent
{
    /// <inheritdoc />
    protected override Task SerializeToStreamAsync(Stream stream, TransportContext? context)
        => Task.Delay(Timeout.InfiniteTimeSpan,deadline);
    /// <inheritdoc />
    protected override bool TryComputeLength(out long length) { length=0;return false; }
}
