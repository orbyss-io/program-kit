using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>CLI transport for strict capability index projection.</summary>
public sealed class RenderCapabilityCatalogCommandOperation : ICommandOperation
{
    private readonly ICapabilityCatalogRenderer renderer;

    /// <summary>Initializes the operation with its rendering behavior.</summary>
    public RenderCapabilityCatalogCommandOperation(
        ICapabilityCatalogRenderer renderer)
    {
        this.renderer = renderer ??
            throw new ArgumentNullException(nameof(renderer));
    }

    /// <inheritdoc />
    public string CommandKey => "capabilities.render-catalog";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            var output = await renderer.RenderAsync(
                invocation.Arguments[0],
                invocation.RequiredOption("output"),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success(output);
        }
        catch (CapabilityOperationException exception)
        {
            return new CommandOperationResult(
                exception.ExitCode,
                default,
                [
                    new CommandDiagnostic(
                        exception.DiagnosticId,
                        "error",
                        exception.Message,
                        exception.Path),
                ]);
        }
    }
}
