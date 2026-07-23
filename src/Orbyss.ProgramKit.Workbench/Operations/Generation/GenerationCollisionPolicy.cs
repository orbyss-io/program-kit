namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Controls collisions below an explicitly declared output root.</summary>
public enum GenerationCollisionPolicy
{
    /// <summary>
    /// Fail when the declared output root already exists; this permits one
    /// same-volume directory rename to publish the complete output set.
    /// </summary>
    Fail,
}
