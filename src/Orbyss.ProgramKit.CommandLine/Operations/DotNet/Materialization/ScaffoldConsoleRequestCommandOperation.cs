using System.Text;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Finite CLI adapter for Console request scaffolding.</summary>
public sealed class ScaffoldConsoleRequestCommandOperation : ICommandOperation
{
    private readonly IConsoleRequestScaffolder scaffolder;

    /// <summary>Initializes the operation with its exact scaffolder.</summary>
    public ScaffoldConsoleRequestCommandOperation(
        IConsoleRequestScaffolder scaffolder)
    {
        this.scaffolder = scaffolder ??
            throw new ArgumentNullException(nameof(scaffolder));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.scaffold-console-request";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        try
        {
            var output = await scaffolder.ScaffoldAsync(
                invocation.Arguments[0],
                invocation.RequiredOption("workspace-root"),
                invocation.RequiredOption("consumer-project"),
                invocation.RequiredOption("output"),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success(
                Encoding.UTF8.GetBytes(
                    string.Concat(
                        "Console materialization request scaffolded: ",
                        Path.GetFullPath(output),
                        Environment.NewLine,
                        "Next: program-kit dotnet materialize-console-inputs ",
                        output,
                        " --workspace-root . --output .program-kit/console-inputs --build-consumer",
                        Environment.NewLine)));
        }
        catch (ConsoleRequestScaffoldingException exception)
        {
            return new CommandOperationResult(
                exception.ExitCode,
                default,
                [
                    new CommandDiagnostic(
                        "PKCIS001",
                        "error",
                        exception.Message,
                        exception.Path),
                ]);
        }
    }
}
