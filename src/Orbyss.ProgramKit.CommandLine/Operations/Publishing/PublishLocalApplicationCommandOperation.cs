using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Local;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>CLI transport for exact-host isolated local application publishing.</summary>
public sealed class PublishLocalApplicationCommandOperation : ICommandOperation
{
    private readonly ILocalApplicationPublisher publisher;

    /// <summary>Initializes the operation with its local publish behavior.</summary>
    public PublishLocalApplicationCommandOperation(
        ILocalApplicationPublisher publisher)
    {
        this.publisher = publisher ??
            throw new ArgumentNullException(nameof(publisher));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.publish-local";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            _ = await publisher.PublishAsync(
                new LocalApplicationPublishRequest(
                    invocation.RequiredOption("shell"),
                    invocation.RequiredOption("host"),
                    invocation.RequiredOption("artifact-manifest"),
                    invocation.RequiredOption("package-manifest"),
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
