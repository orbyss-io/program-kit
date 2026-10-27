using ProgramKit.Examples.TypedOperation;

/// <summary>Non-cooperating fake port makes runtime completion freshness independently observable.</summary>
internal sealed class Store(ControlledClock clock) : ILabelStore
{
    /// <summary>Represents a durable effect that expiry cannot undo.</summary>
    public string Value = "ready";
    /// <summary>Counts dispatched writes to detect retries.</summary>
    public int Writes;
    /// <summary>Counts observations to detect dispatch after expiry.</summary>
    public int Reads;
    /// <summary>Advances monotonic time while the fake write ignores cancellation.</summary>
    public TimeSpan WriteCost;
    /// <summary>Advances monotonic time while the fake read ignores cancellation.</summary>
    public TimeSpan ReadCost;
    /// <summary>Retains the actual write token for identity assertions.</summary>
    public CancellationToken WriteToken;
    /// <summary>Retains the actual read token for identity assertions.</summary>
    public CancellationToken ReadToken;
    /// <summary>Observes cancellation before the runtime checks the returned result's freshness.</summary>
    public bool TokenWasCanceledAtReturn;
    /// <summary>Injects caller cancellation independently from expiry.</summary>
    public CancellationTokenSource? CancelDuringRead;
    /// <summary>Commits a fake effect without obeying cancellation so the runtime must check freshness.</summary>
    public Task WriteAsync(string value, CancellationToken token)
    {
        Writes++;
        WriteToken = token;
        Value = value;
        clock.Advance(WriteCost);
        return Task.CompletedTask;
    }
    /// <summary>Returns a potentially stale result without obeying cancellation.</summary>
    public Task<string> ReadAsync(CancellationToken token)
    {
        Reads++;
        ReadToken = token;
        clock.Advance(ReadCost);
        CancelDuringRead?.Cancel();
        TokenWasCanceledAtReturn = token.IsCancellationRequested;
        return Task.FromResult(Value);
    }
    /// <summary>Clears observations while preserving the last committed value.</summary>
    public void Reset()
    {
        Writes = Reads = 0;
        WriteCost = ReadCost = TimeSpan.Zero;
        CancelDuringRead = null;
        TokenWasCanceledAtReturn = false;
    }
}
