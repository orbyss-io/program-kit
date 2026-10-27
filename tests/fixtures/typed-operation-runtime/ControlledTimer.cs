/// <summary>Models only the one-shot timer semantics needed by the selected native deadline.</summary>
internal sealed class ControlledTimer(
    ControlledClock clock,
    TimerCallback callback,
    object? state
) : ITimer
{
    /// <summary>Holds the next scheduled timestamp, or no active callback.</summary>
    private long? due;
    /// <summary>Reschedules the one-shot timer and rejects unrelated periodic usage.</summary>
    public bool Change(TimeSpan dueTime, TimeSpan period)
    {
        if (period != Timeout.InfiniteTimeSpan) throw new NotSupportedException("Fixture only models one-shot deadlines");
        due = dueTime == Timeout.InfiniteTimeSpan ? null : clock.Ticks + dueTime.Ticks;
        return true;
    }
    /// <summary>Delivers a due callback once.</summary>
    public void Fire(long now)
    {
        if (due is null || due > now) return;
        due = null; callback(state);
    }
    /// <summary>Cancels future delivery.</summary>
    public void Dispose() => due = null;
    /// <summary>Completes synchronous owned-timer cleanup through the async contract.</summary>
    public ValueTask DisposeAsync() { Dispose(); return ValueTask.CompletedTask; }
}
