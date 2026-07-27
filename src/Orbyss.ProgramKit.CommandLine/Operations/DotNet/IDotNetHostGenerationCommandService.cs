namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Loads exact host inputs and performs bounded transactional generation.</summary>
public interface IDotNetHostGenerationCommandService
{
    /// <summary>Generates exactly one manifest-bound host.</summary>
    ValueTask<DotNetHostGenerationCommandResult> GenerateAsync(
        DotNetHostGenerationCommandRequest request,
        CancellationToken cancellationToken);
}
