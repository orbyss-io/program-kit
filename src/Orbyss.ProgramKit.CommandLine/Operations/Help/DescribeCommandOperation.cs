using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Help;

/// <summary>Returns one exact descriptor-backed command contract.</summary>
public sealed class DescribeCommandOperation : ICommandOperation
{
    private readonly IReadOnlyDictionary<string, CommandDescriptor> descriptors;
    private readonly ICommandHelpRenderer renderer;

    /// <summary>Initializes the operation from the exact finite descriptor set.</summary>
    public DescribeCommandOperation(
        IEnumerable<CommandDescriptor> descriptors,
        ICommandHelpRenderer renderer)
    {
        ArgumentNullException.ThrowIfNull(descriptors);
        this.descriptors = descriptors.ToDictionary(
            static descriptor => descriptor.Key,
            StringComparer.Ordinal);
        this.renderer = renderer ??
            throw new ArgumentNullException(nameof(renderer));
    }

    /// <inheritdoc />
    public string CommandKey => "commands.describe";

    /// <inheritdoc />
    public ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        cancellationToken.ThrowIfCancellationRequested();
        var key = invocation.Arguments[0];
        if (!descriptors.TryGetValue(key, out var descriptor))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Unknown command key '",
                    key,
                    "'. Available keys: ",
                    string.Join(", ", descriptors.Keys.Order(StringComparer.Ordinal)),
                    "."),
                "/arguments/command-key");
        }

        return ValueTask.FromResult(
            CommandOperationResult.Success(
                renderer.RenderDescriptor(
                    descriptor,
                    invocation.OptionalOption("format") ?? "text")));
    }
}
