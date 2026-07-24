using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.Execution;

/// <summary>Runs one complete command invocation over explicit operation registrations.</summary>
public interface ICommandApplication
{
    /// <summary>Executes OS tokens and writes only through the supplied console boundary.</summary>
    ValueTask<CommandExitCode> RunAsync(
        IReadOnlyList<string> tokens,
        CancellationToken cancellationToken);
}
