using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Local;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>CLI transport for explicit local package preparation.</summary>
public sealed class PrepareLocalPackagesCommandOperation : ICommandOperation
{
    private readonly ILocalPackagePreparationService preparationService;

    /// <summary>Initializes the operation with its package preparation behavior.</summary>
    public PrepareLocalPackagesCommandOperation(
        ILocalPackagePreparationService preparationService)
    {
        this.preparationService = preparationService ??
            throw new ArgumentNullException(nameof(preparationService));
    }

    /// <inheritdoc />
    public string CommandKey => "packages.prepare-local";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            _ = await preparationService.PrepareAsync(
                new LocalPackagePreparationRequest(
                    invocation.RequiredOption("workspace-manifest"),
                    invocation.RequiredOption("output")),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success();
        }
        catch (LocalOperationException exception)
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
