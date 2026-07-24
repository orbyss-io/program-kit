using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>Duplicate-preserving exact registration link built before any lookup projection.</summary>
public sealed class CommandOperationChain : ICommandOperationChain
{
    private readonly ICommandOperation operation;
    private readonly ICommandOperationChain? next;

    /// <summary>Initializes one registration link and rejects an already present exact key.</summary>
    public CommandOperationChain(
        ICommandOperation operation,
        ICommandOperationChain? next)
    {
        this.operation = operation ?? throw new ArgumentNullException(nameof(operation));
        this.next = next;
        if (string.IsNullOrWhiteSpace(operation.CommandKey) ||
            next?.Contains(operation.CommandKey) == true)
        {
            throw new InvalidOperationException(
                string.Concat(
                    CommandDiagnosticIds.DuplicateOperation,
                    ": command operation registrations must be explicit and unique."));
        }
    }

    /// <inheritdoc />
    public bool Contains(string commandKey) =>
        string.Equals(operation.CommandKey, commandKey, StringComparison.Ordinal) ||
        next?.Contains(commandKey) == true;

    /// <inheritdoc />
    public ICommandOperation? TryResolve(string commandKey) =>
        string.Equals(operation.CommandKey, commandKey, StringComparison.Ordinal)
            ? operation
            : next?.TryResolve(commandKey);
}
