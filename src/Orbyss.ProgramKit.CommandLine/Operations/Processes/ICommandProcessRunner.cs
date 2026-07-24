namespace Orbyss.ProgramKit.CommandLine.Operations.Processes;

/// <summary>Executes exact shell-free child-process requests.</summary>
public interface ICommandProcessRunner
{
    /// <summary>Runs one explicit process and captures its output.</summary>
    ValueTask<CommandProcessResult> RunAsync(
        CommandProcessRequest request,
        CancellationToken cancellationToken);
}
