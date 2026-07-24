using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Explicit manifest-bound transport for API, Console, and Worker generation.</summary>
public sealed class DotNetGenerateHostCommandOperation : ICommandOperation
{
    private readonly IDotNetHostGenerationCommandService generationService;

    /// <summary>Initializes the adapter with its exact-input generation behavior.</summary>
    public DotNetGenerateHostCommandOperation(
        IDotNetHostGenerationCommandService generationService)
    {
        this.generationService = generationService ??
            throw new ArgumentNullException(nameof(generationService));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.generate-host";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            _ = await generationService.GenerateAsync(
                new DotNetHostGenerationCommandRequest(
                    invocation.RequiredOption("shell"),
                    invocation.RequiredOption("host"),
                    invocation.RequiredOption("artifact-manifest"),
                    invocation.RequiredOption("output"),
                    ParseKind(invocation.Arguments[0])),
                cancellationToken).ConfigureAwait(false);
            return CommandOperationResult.Success();
        }
        catch (DotNetKitException exception)
        {
            return new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
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

    private static DotNetHostKind ParseKind(string value) =>
        value switch
        {
            "api" => DotNetHostKind.Api,
            "console" => DotNetHostKind.Console,
            "worker" => DotNetHostKind.Worker,
            _ => throw new InvalidDataException("The host kind is unsupported."),
        };
}
