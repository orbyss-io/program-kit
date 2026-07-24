namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Defines whether middleware runs before acceptance or per attempt.</summary>
public enum TaskMiddlewarePhase
{
    /// <summary>Runs once before task acceptance.</summary>
    Dispatch,
    /// <summary>Runs once per handler attempt.</summary>
    Execution,
}
