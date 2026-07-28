using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Offline generated-host integrity verification transport.</summary>
public sealed class DotNetVerifyHostCommandOperation : ICommandOperation
{
    private readonly IGeneratedOutputIntegrityVerifier verifier;

    /// <summary>Initializes the transport with host-neutral verification behavior.</summary>
    public DotNetVerifyHostCommandOperation(
        IGeneratedOutputIntegrityVerifier verifier)
    {
        this.verifier = verifier ??
            throw new ArgumentNullException(nameof(verifier));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.verify-host";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            var result = await verifier.VerifyAsync(
                invocation.RequiredOption("root"),
                cancellationToken).ConfigureAwait(false);
            return result.IsValid
                ? CommandOperationResult.Success()
                : new CommandOperationResult(
                    CommandExitCode.ConformanceFailure,
                    default,
                    result.Issues
                        .Select(static issue =>
                            new CommandDiagnostic(
                                DiagnosticId(issue.Kind),
                                "error",
                                issue.Message,
                                issue.Path))
                        .ToImmutableArray());
        }
        catch (Exception exception) when (
            exception is ArgumentException or
            InvalidDataException or
            NotSupportedException or
            PathTooLongException)
        {
            return new CommandOperationResult(
                CommandExitCode.UsageOrInputFailure,
                default,
                [
                    new CommandDiagnostic(
                        "PKINT007",
                        "error",
                        "The generated-host root is invalid.",
                        "/root"),
                ]);
        }
    }

    private static string DiagnosticId(
        GeneratedOutputIntegrityIssueKind kind) =>
        kind switch
        {
            GeneratedOutputIntegrityIssueKind.Missing => "PKINT001",
            GeneratedOutputIntegrityIssueKind.Modified => "PKINT002",
            GeneratedOutputIntegrityIssueKind.Unexpected => "PKINT003",
            GeneratedOutputIntegrityIssueKind.Unsafe => "PKINT004",
            GeneratedOutputIntegrityIssueKind.Malformed => "PKINT005",
            GeneratedOutputIntegrityIssueKind.Unsealed => "PKINT006",
            _ => throw new ArgumentOutOfRangeException(nameof(kind)),
        };
}
