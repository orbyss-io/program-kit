namespace Orbyss.ProgramKit.Workbench.Operations.Projections;

/// <summary>Detects projections whose exact source bindings are stale.</summary>
public interface IProjectionFreshnessChecker
{
    /// <summary>Checks every explicit input binding.</summary>
    ProgramKitValidationResult Check(ImmutableArray<ProjectionBinding> bindings);
}
