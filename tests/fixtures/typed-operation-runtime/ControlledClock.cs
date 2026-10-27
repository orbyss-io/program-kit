/// <summary>Controls native monotonic timestamps and timer delivery without wall-clock waits.</summary>
internal sealed class ControlledClock : TimeProvider
{
    /// <summary>Retains owned one-shot timers for deterministic callback delivery.</summary>
    private readonly List<ControlledTimer> timers = [];
    /// <summary>Models a delayed timer thread while monotonic time continues.</summary>
    public bool DelayCallbacks;
    /// <summary>Stores the current monotonic timestamp used by timer scheduling.</summary>
    internal long Ticks { get; private set; }
    /// <summary>Expresses timestamps in TimeSpan ticks.</summary>
    public override long TimestampFrequency => TimeSpan.TicksPerSecond;
    /// <summary>Returns the controlled monotonic timestamp.</summary>
    public override long GetTimestamp() => Ticks;
    /// <summary>Provides a stable wall-clock view for the native clock contract.</summary>
    public override DateTimeOffset GetUtcNow() => DateTimeOffset.UnixEpoch.AddTicks(Ticks);
    /// <summary>Creates the one-shot timer used by the native cancellation deadline.</summary>
    public override ITimer CreateTimer(
        TimerCallback callback,
        object? state,
        TimeSpan dueTime,
        TimeSpan period
    )
    {
        var timer = new ControlledTimer(
            this,
            callback,
            state
        );
        timers.Add(timer);
        timer.Change(dueTime, period);
        return timer;
    }
    /// <summary>Advances time and optionally delivers due callbacks.</summary>
    public void Advance(TimeSpan duration)
    {
        Ticks += duration.Ticks;
        if (DelayCallbacks)
            return;
        foreach (var timer in timers.ToArray())
            timer.Fire(Ticks);
    }
}
