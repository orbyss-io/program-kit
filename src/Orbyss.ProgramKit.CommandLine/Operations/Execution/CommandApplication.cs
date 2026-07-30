using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.CommandLine.Operations.Help;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Execution;

/// <summary>Default exception-contained command dispatcher and exit-code mapper.</summary>
public sealed class CommandApplication : ICommandApplication
{
    private readonly ICommandParser parser;
    private readonly ICommandOperationRegistry operations;
    private readonly ICommandConsole console;
    private readonly ICommandDiagnosticFormatter formatter;
    private readonly ICommandHelpRenderer help;

    /// <summary>Initializes the application with all behavior supplied explicitly.</summary>
    public CommandApplication(
        ICommandParser parser,
        ICommandOperationRegistry operations,
        ICommandConsole console,
        ICommandDiagnosticFormatter formatter,
        ICommandHelpRenderer help)
    {
        this.parser = parser ?? throw new ArgumentNullException(nameof(parser));
        this.operations = operations ?? throw new ArgumentNullException(nameof(operations));
        this.console = console ?? throw new ArgumentNullException(nameof(console));
        this.formatter = formatter ?? throw new ArgumentNullException(nameof(formatter));
        this.help = help ?? throw new ArgumentNullException(nameof(help));
    }

    /// <inheritdoc />
    public async ValueTask<CommandExitCode> RunAsync(
        IReadOnlyList<string> tokens,
        CancellationToken cancellationToken)
    {
        CommandInvocation? invocation = null;
        try
        {
            if (tokens.Count == 0 ||
                tokens.Count == 1 &&
                string.Equals(tokens[0], "--help", StringComparison.Ordinal))
            {
                await console.WriteStandardOutputAsync(
                    help.RenderTopLevel(tokens.Count == 0),
                    cancellationToken).ConfigureAwait(false);
                return CommandExitCode.Success;
            }

            if (string.Equals(tokens[^1], "--help", StringComparison.Ordinal))
            {
                await console.WriteStandardOutputAsync(
                    help.RenderCommandPath(tokens.Take(tokens.Count - 1).ToArray()),
                    cancellationToken).ConfigureAwait(false);
                return CommandExitCode.Success;
            }

            invocation = parser.Parse(tokens);
            var operation = operations.Resolve(invocation.Descriptor.Key);
            var result = await operation.ExecuteAsync(
                invocation,
                cancellationToken).ConfigureAwait(false);
            if (!result.StandardOutput.IsEmpty)
            {
                await console.WriteStandardOutputAsync(
                    result.StandardOutput,
                    cancellationToken).ConfigureAwait(false);
            }

            await WriteDiagnosticsAsync(
                invocation,
                result.ExitCode,
                result.Diagnostics,
                cancellationToken).ConfigureAwait(false);
            return result.ExitCode;
        }
        catch (CommandInvocationException exception)
        {
            return await WriteFailureAsync(
                invocation,
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.InvalidInvocation,
                exception.Message,
                exception.Path,
                cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception)
            when (exception is IOException or UnauthorizedAccessException)
        {
            return await WriteFailureAsync(
                invocation,
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.InvalidInput,
                exception.Message,
                "/input",
                cancellationToken).ConfigureAwait(false);
        }
        catch (ProgramKitJsonException exception)
        {
            return await WriteFailureAsync(
                invocation,
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.InvalidInput,
                exception.Message,
                PrefixPath("/input", exception.Diagnostic.Path),
                cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception)
            when (exception is JsonException or InvalidDataException or
                ArgumentException)
        {
            return await WriteFailureAsync(
                invocation,
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.InvalidInput,
                exception.Message,
                "/input",
                cancellationToken).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            return await WriteFailureAsync(
                invocation,
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.InvalidInput,
                "The command operation was cancelled.",
                "/command",
                CancellationToken.None).ConfigureAwait(false);
        }
        catch (Exception)
        {
            return await WriteFailureAsync(
                invocation,
                CommandExitCode.InternalFailure,
                CommandDiagnosticIds.InternalFailure,
                "The command failed at an unexpected internal boundary.",
                "/command",
                CancellationToken.None).ConfigureAwait(false);
        }
    }

    private static string PrefixPath(string prefix, string path) =>
        string.IsNullOrEmpty(path)
            ? prefix
            : string.Concat(prefix, path);

    private async ValueTask<CommandExitCode> WriteFailureAsync(
        CommandInvocation? invocation,
        CommandExitCode exitCode,
        string diagnosticId,
        string message,
        string path,
        CancellationToken cancellationToken)
    {
        await WriteDiagnosticsAsync(
            invocation,
            exitCode,
            [
                new CommandDiagnostic(
                    diagnosticId,
                    "error",
                    message,
                    path),
            ],
            cancellationToken).ConfigureAwait(false);
        return exitCode;
    }

    private async ValueTask WriteDiagnosticsAsync(
        CommandInvocation? invocation,
        CommandExitCode exitCode,
        System.Collections.Immutable.ImmutableArray<CommandDiagnostic> diagnostics,
        CancellationToken cancellationToken)
    {
        if (diagnostics.IsDefaultOrEmpty)
        {
            return;
        }

        var representation = invocation?.OptionalOption("diagnostics") ?? "text";
        var content = formatter.Format(representation, exitCode, diagnostics);
        await console.WriteStandardErrorAsync(content, cancellationToken)
            .ConfigureAwait(false);
    }
}
