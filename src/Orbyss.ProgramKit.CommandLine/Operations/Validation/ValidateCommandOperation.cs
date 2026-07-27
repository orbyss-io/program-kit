using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Validation;

/// <summary>Validates explicitly supplied artifacts against exact package-owned schemas.</summary>
public sealed class ValidateCommandOperation : ICommandOperation
{
    private readonly ICommandFileSystem fileSystem;
    private readonly ICommandSchemaSelector schemaSelector;
    private readonly IWorkbenchSchemaValidator validator;

    /// <summary>Initializes validation over explicit file, schema, and Workbench behavior.</summary>
    public ValidateCommandOperation(
        ICommandFileSystem fileSystem,
        ICommandSchemaSelector schemaSelector,
        IWorkbenchSchemaValidator validator)
    {
        this.fileSystem = fileSystem ?? throw new ArgumentNullException(nameof(fileSystem));
        this.schemaSelector = schemaSelector ??
            throw new ArgumentNullException(nameof(schemaSelector));
        this.validator = validator ?? throw new ArgumentNullException(nameof(validator));
    }

    /// <inheritdoc />
    public string CommandKey => "validate";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        if (invocation.Options.ContainsKey("manifest"))
        {
            return new CommandOperationResult(
                CommandExitCode.UsageOrInputFailure,
                default,
                [
                    new CommandDiagnostic(
                        CommandDiagnosticIds.OperationUnavailable,
                        "error",
                        "Artifact-manifest validation requires the PK-W060 workspace artifact model.",
                        "/options/manifest"),
                ]);
        }

        var diagnostics = ImmutableArray.CreateBuilder<CommandDiagnostic>();
        foreach (var artifact in invocation.Arguments)
        {
            var content = await fileSystem.ReadAllBytesAsync(
                artifact,
                cancellationToken).ConfigureAwait(false);
            var module = schemaSelector.Resolve(content, out var revision);
            var validation = validator.Validate(
                content,
                module,
                revision,
                JsonSerializationLimits.Default);
            diagnostics.AddRange(
                validation.Diagnostics.Select(diagnostic =>
                    new CommandDiagnostic(
                        diagnostic.Id,
                        diagnostic.Severity.ToString().ToLowerInvariant(),
                        diagnostic.Message,
                        string.Concat(artifact, diagnostic.Path))));
        }

        return diagnostics.Count == 0
            ? CommandOperationResult.Success()
            : new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                diagnostics.ToImmutable());
    }
}
