namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Constrains secret access during an execution.</summary>
public enum SecretAccessPolicy
{
    /// <summary>Forbids secret access.</summary>
    Denied,
    /// <summary>Permits only explicitly named external secret references.</summary>
    ExplicitReferencesOnly,
}
