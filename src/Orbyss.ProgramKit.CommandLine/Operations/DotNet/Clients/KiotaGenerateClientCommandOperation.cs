using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Explicit local-input command transport for pinned Kiota generation.</summary>
public sealed class KiotaGenerateClientCommandOperation : ICommandOperation
{
    private readonly IKiotaForeignClientGenerator generator;

    /// <summary>Initializes the adapter with its exact generation behavior.</summary>
    public KiotaGenerateClientCommandOperation(
        IKiotaForeignClientGenerator generator)
    {
        this.generator = generator ??
            throw new ArgumentNullException(nameof(generator));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.generate-client";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            _ = await generator.GenerateAsync(
                new KiotaForeignClientGenerationRequest(
                    invocation.RequiredOption("openapi"),
                    invocation.RequiredOption("output"),
                    invocation.RequiredOption("tool-manifest"),
                    invocation.RequiredOption("tool-package"),
                    invocation.RequiredOption("namespace-name"),
                    invocation.RequiredOption("class-name"),
                    [],
                    []),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success();
        }
        catch (KiotaGenerationException exception)
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
