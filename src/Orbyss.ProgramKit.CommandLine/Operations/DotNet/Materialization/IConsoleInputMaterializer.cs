namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Materializes exact typed Console generation inputs.</summary>
public interface IConsoleInputMaterializer
{
    /// <summary>Builds, evaluates, validates, and materializes one input set.</summary>
    ValueTask<ConsoleInputMaterializationResult> MaterializeAsync(
        string requestPath,
        string workspaceRoot,
        string outputRoot,
        CancellationToken cancellationToken);
}
