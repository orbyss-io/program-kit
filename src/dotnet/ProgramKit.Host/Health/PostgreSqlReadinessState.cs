namespace ProgramKit.Host.Health;

/// <summary>Stores a redacted operational PostgreSQL readiness result.</summary>
internal sealed class PostgreSqlReadinessState
{
    /// <summary>The current fixed redacted status value.</summary>
    private volatile string _status = "not-configured";

    /// <summary>Gets whether the configured operational dependency is ready.</summary>
    public bool IsReady => _status is "ready" or "not-configured";

    /// <summary>Gets the fixed redacted status.</summary>
    public string Status => _status;

    /// <summary>Updates readiness without retaining exception or connection details.</summary>
    public void Set(bool ready) => _status = ready ? "ready" : "not-ready";
}
