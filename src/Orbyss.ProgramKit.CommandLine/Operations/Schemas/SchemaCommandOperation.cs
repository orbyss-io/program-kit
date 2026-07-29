using Orbyss.ProgramKit.CommandLine.Commands.Parsing;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Finite schema list/read transport.</summary>
public sealed class SchemaCommandOperation : ICommandOperation
{
    private readonly string commandKey;
    private readonly ISchemaCatalog catalog;

    /// <summary>Initializes one exact schema command adapter.</summary>
    public SchemaCommandOperation(string commandKey, ISchemaCatalog catalog)
    {
        this.commandKey = commandKey ??
            throw new ArgumentNullException(nameof(commandKey));
        this.catalog = catalog ??
            throw new ArgumentNullException(nameof(catalog));
    }

    /// <inheritdoc />
    public string CommandKey => commandKey;

    /// <inheritdoc />
    public ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        cancellationToken.ThrowIfCancellationRequested();
        var content = commandKey switch
        {
            "schemas.list" => catalog.Render(
                invocation.OptionalOption("format") ?? "text"),
            "schemas.read" => catalog.Resolve(invocation.Arguments[0])
                .Content.ToArray(),
            _ => throw new InvalidOperationException(
                "The schema command key is not registered."),
        };
        return ValueTask.FromResult(CommandOperationResult.Success(content));
    }
}
