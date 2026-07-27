using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>CLI transport for explicit provider-wrapper initialization.</summary>
public sealed class InitializeCapabilitiesCommandOperation : ICommandOperation
{
    private readonly ICapabilityInitializer initializer;

    /// <summary>Initializes the command with exact initialization behavior.</summary>
    public InitializeCapabilitiesCommandOperation(
        ICapabilityInitializer initializer)
    {
        this.initializer = initializer ??
            throw new ArgumentNullException(nameof(initializer));
    }

    /// <inheritdoc />
    public string CommandKey => "capabilities.initialize";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            await initializer.InitializeAsync(
                invocation.RequiredOption("provider"),
                invocation.RequiredOption("workspace-root"),
                invocation.RequiredOption("program-kit-root"),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success();
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
