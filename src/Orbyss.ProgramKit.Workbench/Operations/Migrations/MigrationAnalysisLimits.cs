namespace Orbyss.ProgramKit.Workbench.Operations.Migrations;

/// <summary>Finite limits for migration reverse-closure analysis.</summary>
/// <param name="MaxImpactedNodes">Maximum reached exact revisions.</param>
/// <param name="MaxCausalPaths">Maximum retained causal paths across all revisions.</param>
public sealed record MigrationAnalysisLimits(
    int MaxImpactedNodes,
    int MaxCausalPaths)
{
    /// <summary>Gets conservative baseline analysis limits.</summary>
    public static MigrationAnalysisLimits Default { get; } =
        new(4_096, 65_536);
}
