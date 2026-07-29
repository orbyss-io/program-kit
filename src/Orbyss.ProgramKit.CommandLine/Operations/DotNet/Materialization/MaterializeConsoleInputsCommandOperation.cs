using System.Text;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Finite CLI adapter for explicit Console input materialization.</summary>
public sealed class MaterializeConsoleInputsCommandOperation :
    ICommandOperation
{
    private readonly IConsoleInputMaterializer materializer;

    /// <summary>Initializes the operation with its exact materializer.</summary>
    public MaterializeConsoleInputsCommandOperation(
        IConsoleInputMaterializer materializer)
    {
        this.materializer = materializer ??
            throw new ArgumentNullException(nameof(materializer));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.materialize-console-inputs";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            var result = await materializer.MaterializeAsync(
                invocation.Arguments[0],
                invocation.RequiredOption("workspace-root"),
                invocation.RequiredOption("output"),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success(
                Encoding.UTF8.GetBytes(
                    string.Concat(
                        "Console inputs ",
                        result.Status.ToString().ToLowerInvariant(),
                        ": ",
                        result.OutputRoot,
                        Environment.NewLine,
                        "Next: program-kit dotnet generate-host console --shell ",
                        result.ShellPath,
                        " --host ",
                        result.HostIdentity,
                        " --artifact-manifest ",
                        result.ArtifactManifestPath,
                        " --output <generated-host-output>",
                        Environment.NewLine)));
        }
        catch (ConsoleInputMaterializationException exception)
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
