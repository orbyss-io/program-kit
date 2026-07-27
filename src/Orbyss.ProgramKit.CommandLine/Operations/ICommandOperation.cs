using Orbyss.ProgramKit.CommandLine.Commands.Parsing;

namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>Adapts one exact command path to an existing Program Kit operation.</summary>
public interface ICommandOperation
{
    /// <summary>Gets the exact command descriptor key.</summary>
    string CommandKey { get; }

    /// <summary>Executes the already parsed operation request.</summary>
    ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken);
}
