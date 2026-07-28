using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.DotNet.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Frozen command transport for exact generated-host refresh.</summary>
public sealed class DotNetRefreshHostCommandOperation : ICommandOperation
{
    private readonly IDotNetHostRefreshService refreshService;
    private readonly IDotNetHostRefreshSerializer refreshSerializer;

    /// <summary>Initializes the transport with its backed refresh behavior.</summary>
    public DotNetRefreshHostCommandOperation(
        IDotNetHostRefreshService refreshService,
        IDotNetHostRefreshSerializer refreshSerializer)
    {
        this.refreshService = refreshService ??
            throw new ArgumentNullException(nameof(refreshService));
        this.refreshSerializer = refreshSerializer ??
            throw new ArgumentNullException(nameof(refreshSerializer));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.refresh-host";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            var result = await refreshService.RefreshAsync(
                invocation.RequiredOption("request"),
                invocation.OptionalOption("preview") is not null,
                invocation.OptionalOption("build-consumer") is not null,
                invocation.OptionalOption("repair-generated-output") is not null,
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success(
                refreshSerializer.WriteResult(result));
        }
        catch (DotNetHostRefreshException exception)
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
        catch (DotNetKitException exception)
        {
            return Failure(
                CommandExitCode.ConformanceFailure,
                exception.DiagnosticId,
                exception.Message,
                exception.Path);
        }
        catch (Exception exception) when (
            exception is IOException or
            UnauthorizedAccessException or
            InvalidDataException or
            InvalidOperationException or
            NotSupportedException or
            PathTooLongException)
        {
            return Failure(
                CommandExitCode.UsageOrInputFailure,
                "PKREF016",
                "The refresh input or filesystem operation is invalid.",
                "/request");
        }
    }

    private static CommandOperationResult Failure(
        CommandExitCode exitCode,
        string diagnosticId,
        string message,
        string path) =>
        new(
            exitCode,
            default,
            [
                new CommandDiagnostic(
                    diagnosticId,
                    "error",
                    message,
                    path),
            ]);
}
