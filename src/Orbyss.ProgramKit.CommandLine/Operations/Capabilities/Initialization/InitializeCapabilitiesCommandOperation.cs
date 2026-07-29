using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using System.Text;

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
            var result = await initializer.InitializeAsync(
                invocation.RequiredOption("provider"),
                invocation.RequiredOption("workspace-root"),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success(
                Encoding.UTF8.GetBytes(
                    string.Concat(
                        "Program Kit ",
                        result.Provider,
                        " wrappers: created=",
                        result.Created,
                        ", updated=",
                        result.Updated,
                        ", unchanged=",
                        result.Unchanged,
                        "; lock=",
                        result.LockPath,
                        ". Next: program-kit capabilities catalog --workspace-root . --format text",
                        Environment.NewLine)));
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
