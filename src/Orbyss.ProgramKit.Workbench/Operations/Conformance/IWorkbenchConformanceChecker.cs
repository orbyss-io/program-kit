namespace Orbyss.ProgramKit.Workbench.Operations.Conformance;

/// <summary>Checks one structured model against deterministic conformance rules.</summary>
/// <typeparam name="T">The checked model type.</typeparam>
public interface IWorkbenchConformanceChecker<in T>
{
    /// <summary>Returns stable diagnostics in deterministic rule order.</summary>
    ProgramKitValidationResult Check(T value);
}
