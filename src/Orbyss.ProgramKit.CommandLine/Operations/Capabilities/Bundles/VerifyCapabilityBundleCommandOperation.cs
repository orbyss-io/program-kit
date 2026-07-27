using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>CLI transport for exact-byte capability bundle verification.</summary>
public sealed class VerifyCapabilityBundleCommandOperation : ICommandOperation
{
    private readonly ICapabilityBundleVerifier verifier;

    /// <summary>Initializes the operation with its bundle verification behavior.</summary>
    public VerifyCapabilityBundleCommandOperation(
        ICapabilityBundleVerifier verifier)
    {
        this.verifier = verifier ??
            throw new ArgumentNullException(nameof(verifier));
    }

    /// <inheritdoc />
    public string CommandKey => "capabilities.verify-bundle";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            await verifier.VerifyAsync(
                invocation.Arguments[0],
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
