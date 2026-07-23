namespace Orbyss.ProgramKit.Workbench.Operations.Dependencies;

/// <summary>Analyzes explicit structured dependency inputs without ambient discovery.</summary>
/// <typeparam name="TInput">The dependency input model.</typeparam>
/// <typeparam name="TResult">The deterministic graph result.</typeparam>
public interface IWorkbenchDependencyAnalyzer<in TInput, out TResult>
{
    /// <summary>Builds one deterministic dependency result.</summary>
    TResult Analyze(TInput input);
}
