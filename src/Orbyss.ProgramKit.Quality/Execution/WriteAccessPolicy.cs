namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Constrains filesystem writes during an execution.</summary>
public enum WriteAccessPolicy
{
    /// <summary>Forbids filesystem writes.</summary>
    Denied,
    /// <summary>Permits writes only to the selected temporary output.</summary>
    TemporaryOutputOnly,
    /// <summary>Permits writes only beneath explicit roots.</summary>
    ExplicitRoots,
}
