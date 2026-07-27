using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.CommandLine.Operations.CSharpBuildGates;

/// <summary>
/// Thin command transport over five registered Workbench gate operations.
/// </summary>
public sealed class CSharpGateCommandService : ICSharpGateCommandService
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly ICSharpBuildGateOperationService operations;

    /// <summary>Initializes the exact file, serialization, and operation edges.</summary>
    public CSharpGateCommandService(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer,
        ICSharpBuildGateOperationService operations)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.operations = operations ??
            throw new ArgumentNullException(nameof(operations));
    }

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        string commandKey,
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(commandKey);
        ArgumentNullException.ThrowIfNull(invocation);
        return commandKey switch
        {
            "csharp-gate.validate-definition" =>
                await ValidateAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.render-definition" =>
                await RenderAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.scaffold" =>
                await ScaffoldAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.bind" =>
                await BindAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.verify" =>
                await VerifyAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            _ => throw new InvalidOperationException(
                "The C# gate command is outside the finite catalog."),
        };
    }

    private async ValueTask<CommandOperationResult> ValidateAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var definition = await ReadAsync<CSharpBuildGateDefinitionDocument>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var validation = operations.ValidateDefinition(definition);
        return validation.IsValid
            ? CommandOperationResult.Success()
            : new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                validation.Diagnostics
                    .Select(diagnostic => new CommandDiagnostic(
                        diagnostic.Id,
                        diagnostic.Severity.ToString().ToLowerInvariant(),
                        diagnostic.Message,
                        diagnostic.Path))
                    .ToImmutableArray());
    }

    private async ValueTask<CommandOperationResult> RenderAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var definition = await ReadAsync<CSharpBuildGateDefinitionDocument>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        var rendered = operations.RenderDefinition(definition);
        await fileSystem.WriteAllBytesAsync(
            output,
            Encoding.UTF8.GetBytes(rendered),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }

    private async ValueTask<CommandOperationResult> ScaffoldAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var request = await ReadAsync<ConsumerAnalyzerScaffoldRequest>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        _ = await operations.ScaffoldAsync(
            request,
            invocation.RequiredOption("output"),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }

    private async ValueTask<CommandOperationResult> BindAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var request = await ReadAsync<CSharpGateBindRequest>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        var selectionLock = operations.Bind(request);
        var canonical = serializer.Write(
            selectionLock,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        await fileSystem.WriteAllBytesAsync(
            output,
            canonical.ToArray(),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }

    private async ValueTask<CommandOperationResult> VerifyAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var request = await ReadAsync<CSharpGateVerificationRequest>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        var result = await operations.VerifyAsync(
            request with { EvidenceOutputPath = output },
            cancellationToken).ConfigureAwait(false);
        return result.Succeeded
            ? CommandOperationResult.Success()
            : new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                [
                    new CommandDiagnostic(
                        "PKCG070",
                        "error",
                        string.Concat(
                            "C# gate verification failed at ",
                            result.FailureLayer?.ToString() ?? "unknown",
                            "."),
                        "/verification"),
                ]);
    }

    private async ValueTask<T> ReadAsync<T>(
        string path,
        CancellationToken cancellationToken)
    {
        var bytes = await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
        return serializer.Read<T>(
            bytes,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
    }

    private void RequireNewOutput(string path)
    {
        if (fileSystem.FileExists(path) || fileSystem.DirectoryExists(path))
        {
            throw new IOException(
                "The exact operation output already exists.");
        }
    }
}
