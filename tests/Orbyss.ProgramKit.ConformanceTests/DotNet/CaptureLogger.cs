using Microsoft.Extensions.Logging;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

internal sealed class CaptureLogger<TCategory> : ILogger<TCategory>
{
    internal List<(EventId EventId, LogLevel Level, string Message)> Entries { get; } = [];
    internal List<IReadOnlyDictionary<string, object?>> Scopes { get; } = [];

    public IDisposable? BeginScope<TState>(TState state)
        where TState : notnull
    {
        if (state is IReadOnlyDictionary<string, object?> fields)
        {
            Scopes.Add(fields);
        }

        return null;
    }

    public bool IsEnabled(LogLevel logLevel) => true;

    public void Log<TState>(
        LogLevel logLevel,
        EventId eventId,
        TState state,
        Exception? exception,
        Func<TState, Exception?, string> formatter) =>
        Entries.Add((eventId, logLevel, formatter(state, exception)));
}
