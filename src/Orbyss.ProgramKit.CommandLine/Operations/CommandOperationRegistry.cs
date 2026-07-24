using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations;

/// <summary>Fail-closed registry built from an explicit finite operation sequence.</summary>
public sealed class CommandOperationRegistry : ICommandOperationRegistry
{
    private readonly ICommandOperationChain operations;

    /// <summary>Initializes the registry from an already explicit registration chain.</summary>
    public CommandOperationRegistry(ICommandOperationChain operations)
    {
        this.operations = operations ?? throw new ArgumentNullException(nameof(operations));
    }

    /// <inheritdoc />
    public ICommandOperation Resolve(string commandKey)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(commandKey);
        return operations.TryResolve(commandKey) is { } operation
            ? operation
            : throw new CommandInvocationException(
                $"No operation adapter is registered for '{commandKey}'.",
                "/command");
    }
}
