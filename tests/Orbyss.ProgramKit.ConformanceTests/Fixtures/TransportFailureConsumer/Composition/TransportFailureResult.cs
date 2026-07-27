namespace GeneratedHost.Composition;

/// <summary>Captured observable result from the transport-failure fixture.</summary>
public sealed class TransportFailureResult
{
    /// <summary>Initializes one captured result.</summary>
    public TransportFailureResult(
        bool handled,
        int statusCode,
        string body,
        int logCount,
        string logText,
        int measurementCount)
    {
        Handled = handled;
        StatusCode = statusCode;
        Body = body;
        LogCount = logCount;
        LogText = logText;
        MeasurementCount = measurementCount;
    }

    /// <summary>Gets whether an exception handler claimed the failure.</summary>
    public bool Handled { get; }

    /// <summary>Gets the final HTTP response status.</summary>
    public int StatusCode { get; }

    /// <summary>Gets the final response body.</summary>
    public string Body { get; }

    /// <summary>Gets the count of sanitized failure log events.</summary>
    public int LogCount { get; }

    /// <summary>Gets the captured sanitized log text.</summary>
    public string LogText { get; }

    /// <summary>Gets the count of failure outcome measurements.</summary>
    public int MeasurementCount { get; }
}
