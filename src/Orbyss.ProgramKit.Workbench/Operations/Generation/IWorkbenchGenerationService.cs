namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Coordinates bounded all-or-nothing output publication.</summary>
/// <typeparam name="T">The generator input type.</typeparam>
public interface IWorkbenchGenerationService<T>
{
    /// <summary>Generates, validates, stages, and atomically publishes outputs.</summary>
    ValueTask<WorkbenchResult<GenerationReceipt>> GenerateAsync(
        GenerationRequest<T> request,
        CancellationToken cancellationToken);
}
