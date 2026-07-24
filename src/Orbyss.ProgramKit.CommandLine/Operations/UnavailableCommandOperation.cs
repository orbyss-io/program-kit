using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>Fail-closed placeholder for a command whose backing work unit is not installed.</summary>
public sealed class UnavailableCommandOperation : ICommandOperation
{
    private readonly string backingWorkUnit;

    /// <summary>Initializes an explicit unavailable operation registration.</summary>
    public UnavailableCommandOperation(string commandKey, string backingWorkUnit)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(commandKey);
        ArgumentException.ThrowIfNullOrWhiteSpace(backingWorkUnit);
        CommandKey = commandKey;
        this.backingWorkUnit = backingWorkUnit;
    }

    /// <inheritdoc />
    public string CommandKey { get; }

    /// <inheritdoc />
    public ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult(
            new CommandOperationResult(
                CommandExitCode.UsageOrInputFailure,
                default,
                [
                    new CommandDiagnostic(
                        CommandDiagnosticIds.OperationUnavailable,
                        "error",
                        $"The operation backend is owned by {backingWorkUnit} and is not registered.",
                        "/command"),
                ]));
    }
}
