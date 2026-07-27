namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Produces complete in-memory outputs without publishing them.</summary>
/// <typeparam name="T">The structured generator input.</typeparam>
public interface IWorkbenchGenerator<in T>
{
    /// <summary>Generates a finite complete output set.</summary>
    ValueTask<ImmutableArray<GeneratedOutput>> GenerateAsync(
        T input,
        CancellationToken cancellationToken);
}
