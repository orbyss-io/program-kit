namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>States whether planned output bytes already exist.</summary>
public enum PlannedArtifactState
{
    /// <summary>The output identity is planned, but no output bytes exist yet.</summary>
    Prospective,

    /// <summary>The output bytes exist and their exact integrity digest is asserted.</summary>
    Materialized,
}
