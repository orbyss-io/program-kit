using Orbyss.ProgramKit.CommandLine.Commands.Parsing;

namespace Orbyss.ProgramKit.CommandLine.Operations.Diagnostics;

/// <summary>Read-only adapter for the finite diagnostic catalog.</summary>
public sealed class DiagnosticExplainCommandOperation : ICommandOperation
{
    private readonly IDiagnosticExplanationCatalog catalog;

    /// <summary>Initializes the adapter.</summary>
    public DiagnosticExplainCommandOperation(
        IDiagnosticExplanationCatalog catalog)
    {
        this.catalog = catalog ??
            throw new ArgumentNullException(nameof(catalog));
    }

    /// <inheritdoc />
    public string CommandKey => "diagnostics.explain";

    /// <inheritdoc />
    public ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        cancellationToken.ThrowIfCancellationRequested();
        var explanation = catalog.Resolve(invocation.Arguments[0]);
        var output = catalog.Render(
            explanation,
            invocation.OptionalOption("format") ?? "text");
        return ValueTask.FromResult(
            CommandOperationResult.Success(output));
    }
}
