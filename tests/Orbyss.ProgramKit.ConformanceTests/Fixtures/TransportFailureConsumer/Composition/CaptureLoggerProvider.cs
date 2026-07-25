using System.Collections.Concurrent;
using Microsoft.Extensions.Logging;

namespace GeneratedHost.Composition;

internal sealed class CaptureLoggerProvider : ILoggerProvider
{
    internal ConcurrentQueue<string> Messages { get; } = new();

    public ILogger CreateLogger(string categoryName) =>
        new CaptureLogger(Messages);

    public void Dispose()
    {
    }
}
