using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

namespace Orbyss.ProgramKit.Workbench.Operations.Projections;

/// <summary>Default exact-reference projection freshness checker.</summary>
public sealed class ProjectionFreshnessChecker : IProjectionFreshnessChecker
{
    /// <inheritdoc />
    public ProgramKitValidationResult Check(ImmutableArray<ProjectionBinding> bindings)
    {
        if (bindings.IsDefault)
        {
            return ProgramKitValidationResult.From(
            [
                WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.StaleProjection,
                    "Projection bindings must be initialized.",
                    "/bindings"),
            ]);
        }

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        for (var index = 0; index < bindings.Length; index++)
        {
            var binding = bindings[index];
            if (binding is null || binding.Declared is null || binding.Current is null)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.StaleProjection,
                    "Each projection binding requires declared and current exact references.",
                    string.Concat("/bindings/", index)));
                continue;
            }

            if (binding.Declared != binding.Current)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.StaleProjection,
                    "The generated projection no longer matches its current exact input.",
                    string.Concat("/bindings/", index, "/current")));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
