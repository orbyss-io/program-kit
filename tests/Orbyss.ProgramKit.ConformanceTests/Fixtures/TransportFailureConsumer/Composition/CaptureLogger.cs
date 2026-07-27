using System.Collections.Concurrent;
using Microsoft.Extensions.Logging;

namespace GeneratedHost.Composition;

internal sealed class CaptureLogger : ILogger
{
    private readonly ConcurrentQueue<string> _messages;

    internal CaptureLogger(ConcurrentQueue<string> messages)
    {
        _messages = messages;
    }

    public IDisposable? BeginScope<TState>(TState state)
        where TState : notnull =>
        null;

    public bool IsEnabled(LogLevel logLevel) => true;

    public void Log<TState>(
        LogLevel logLevel,
        EventId eventId,
        TState state,
        Exception? exception,
        Func<TState, Exception?, string> formatter)
    {
        if (eventId.Id == 19001)
        {
            _messages.Enqueue(formatter(state, exception));
        }
    }
}
