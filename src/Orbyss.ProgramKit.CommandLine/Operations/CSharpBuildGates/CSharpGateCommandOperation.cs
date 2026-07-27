using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.CommandLine.Operations.CSharpBuildGates;

/// <summary>One exact CLI path over the shared finite gate command service.</summary>
public sealed class CSharpGateCommandOperation : ICommandOperation
{
    private static readonly HashSet<string> Keys = new(
    [
        "csharp-gate.validate-definition",
        "csharp-gate.render-definition",
        "csharp-gate.scaffold",
        "csharp-gate.bind",
        "csharp-gate.verify",
    ], StringComparer.Ordinal);

    private readonly ICSharpGateCommandService service;

    /// <summary>Initializes one exact command-key adapter.</summary>
    public CSharpGateCommandOperation(
        string commandKey,
        ICSharpGateCommandService service)
    {
        if (!Keys.Contains(commandKey))
        {
            throw new ArgumentException(
                "The command key is outside the finite C# gate catalog.",
                nameof(commandKey));
        }

        CommandKey = commandKey;
        this.service = service ??
            throw new ArgumentNullException(nameof(service));
    }

    /// <inheritdoc />
    public string CommandKey { get; }

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        try
        {
            return await service.ExecuteAsync(
                CommandKey,
                invocation,
                cancellationToken).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (CSharpBuildGateOperationException exception)
        {
            return Failure(
                "PKCG071",
                exception.Message,
                string.Concat("/layers/", exception.Layer));
        }
        catch (Exception exception) when (
            exception is IOException or
            InvalidOperationException or
            ArgumentException)
        {
            return Failure("PKCG072", exception.Message, "/input");
        }
    }

    private static CommandOperationResult Failure(
        string id,
        string message,
        string path) =>
        new(
            CommandExitCode.UsageOrInputFailure,
            default,
            [new CommandDiagnostic(id, "error", message, path)]);
}
