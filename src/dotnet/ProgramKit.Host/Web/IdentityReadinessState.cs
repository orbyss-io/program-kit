namespace ProgramKit.Host.Web;

/// <summary>Stores the current identity discovery and signing-key readiness result.</summary>
internal sealed class IdentityReadinessState
{
    /// <summary>Stores minus one before the first probe, zero for unavailable, and one for ready.</summary>
    private int status = -1;

    /// <summary>Gets whether discovery and signing keys were available during the latest probe.</summary>
    public bool IsReady => Volatile.Read(ref status) == 1;

    /// <summary>Atomically replaces the current signal and reports whether its value changed.</summary>
    public bool SetReady(bool value)
    {
        var next = value ? 1 : 0;
        return Interlocked.Exchange(ref status, next) != next;
    }
}
