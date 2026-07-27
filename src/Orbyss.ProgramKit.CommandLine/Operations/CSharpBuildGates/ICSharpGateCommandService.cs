using Orbyss.ProgramKit.CommandLine.Commands.Parsing;

namespace Orbyss.ProgramKit.CommandLine.Operations.CSharpBuildGates;

/// <summary>Finite file/serialization transport for the five gate operations.</summary>
public interface ICSharpGateCommandService
{
    /// <summary>Executes one already parsed exact gate command.</summary>
    ValueTask<CommandOperationResult> ExecuteAsync(
        string commandKey,
        CommandInvocation invocation,
        CancellationToken cancellationToken);
}
