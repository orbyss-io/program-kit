namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Constrains network access during an execution.</summary>
public enum NetworkAccessPolicy
{
    /// <summary>Forbids network access.</summary>
    Denied,
    /// <summary>Permits only loopback access.</summary>
    LoopbackOnly,
    /// <summary>Permits only explicitly listed destinations.</summary>
    ExplicitAllowList,
}
