using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Removal;

/// <summary>CLI transport for explicit exact provider uninitialization.</summary>
public sealed class UninitializeCapabilitiesCommandOperation :
    ICommandOperation
{
    private readonly ICapabilityUninitializer uninitializer;

    /// <summary>Creates the command over exact removal behavior.</summary>
    public UninitializeCapabilitiesCommandOperation(
        ICapabilityUninitializer uninitializer)
    {
        this.uninitializer = uninitializer ??
            throw new ArgumentNullException(nameof(uninitializer));
    }

    /// <inheritdoc />
    public string CommandKey => "capabilities.uninitialize";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            await uninitializer.UninitializeAsync(
                invocation.RequiredOption("provider"),
                invocation.RequiredOption("workspace-root"),
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
