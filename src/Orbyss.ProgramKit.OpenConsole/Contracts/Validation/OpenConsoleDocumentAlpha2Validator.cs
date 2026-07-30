using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.OpenConsole.Contracts.Validation;

/// <summary>
/// Deterministic semantic validator for the current alpha.2 Open Console
/// contract. The immutable 1.0.0 validator retains its original behavior.
/// </summary>
public sealed class OpenConsoleDocumentAlpha2Validator :
    IProgramKitSemanticValidator<OpenConsoleDocumentAlpha2>
{
    private const string Schema =
        "pkid:schema:program-kit:open-console@0.1.0-alpha.2";
    private static readonly SemanticVersion Version = new("0.1.0-alpha.2");
    private readonly IProgramKitSemanticValidator<OpenConsoleDocument>
        version1Validator;

    /// <summary>Initializes alpha.2 validation over the immutable v1 rules.</summary>
    public OpenConsoleDocumentAlpha2Validator(
        IProgramKitSemanticValidator<OpenConsoleDocument> version1Validator)
    {
        this.version1Validator = version1Validator ??
            throw new ArgumentNullException(nameof(version1Validator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OpenConsoleDocumentAlpha2 document)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (document is null)
        {
            Error(diagnostics, "An Open Console alpha.2 document is required.", "");
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (!string.Equals(document.Schema, Schema, StringComparison.Ordinal) ||
            document.DocumentVersion != Version)
        {
            Error(
                diagnostics,
                "Open Console must select the exact 0.1.0-alpha.2 schema and document version.",
                "");
        }

        var roles = new[]
        {
            document.HostExitCodeRoles.InvalidInvocation,
            document.HostExitCodeRoles.Cancellation,
            document.HostExitCodeRoles.InternalFailure,
        };
        if (roles.Any(code => code <= 0 || code == document.Help.ExitCode) ||
            roles.Distinct().Count() != roles.Length)
        {
            Error(
                diagnostics,
                "Host exit-code roles must be distinct positive reservations and must not equal the help exit code.",
                "/hostExitCodeRoles");
        }

        if (document.Commands.IsDefaultOrEmpty)
        {
            Error(diagnostics, "At least one command is required.", "/commands");
            return ProgramKitValidationResult.From(diagnostics);
        }

        var operationKeys = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < document.Commands.Length; index++)
        {
            var command = document.Commands[index];
            var path = string.Concat("/commands/", index);
            if (!operationKeys.Add(Exact(command.OperationRevision)))
            {
                Error(
                    diagnostics,
                    "Command operation revisions must be unique.",
                    string.Concat(path, "/operationRevision"));
            }

            ValidateExitMap(document, command, path, diagnostics);
            ValidateSchemaSets(command, path, diagnostics);
            ValidateStreams(command, path, diagnostics);
        }

        var provenance = document.Provenance.OperationRevisions.IsDefault
            ? []
            : document.Provenance.OperationRevisions.Select(Exact)
                .ToHashSet(StringComparer.Ordinal);
        if (!operationKeys.SetEquals(provenance))
        {
            Error(
                diagnostics,
                "Console provenance must bind exactly the projected operations.",
                "/provenance/operationRevisions");
        }

        var legacy = document.ToVersion1();
        var legacyResult = version1Validator.Validate(legacy);
        diagnostics.AddRange(legacyResult.Diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateExitMap(
        OpenConsoleDocumentAlpha2 document,
        OpenConsoleCommandAlpha2 command,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var required = new[]
        {
            0,
            document.HostExitCodeRoles.InvalidInvocation,
            document.HostExitCodeRoles.Cancellation,
            document.HostExitCodeRoles.InternalFailure,
        };
        var codes = command.ExitCodes.IsDefault
            ? []
            : command.ExitCodes.Select(static exit => exit.Code).ToArray();
        if (codes.Length == 0 ||
            codes.Distinct().Count() != codes.Length ||
            required.Any(code => !codes.Contains(code)))
        {
            Error(
                diagnostics,
                "Each command exit map must be exhaustive, unique, and include success plus every host exit-code role.",
                string.Concat(path, "/exitCodes"));
        }
    }

    private static void ValidateSchemaSets(
        OpenConsoleCommandAlpha2 command,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        RequireUniqueInitialized(
            command.RequestSchemaRevisions,
            string.Concat(path, "/requestSchemaRevisions"),
            diagnostics);
        RequireUniqueInitialized(
            command.ResultSchemaRevisions,
            string.Concat(path, "/resultSchemaRevisions"),
            diagnostics);
        RequireUniqueInitialized(
            command.DiagnosticSchemaRevisions,
            string.Concat(path, "/diagnosticSchemaRevisions"),
            diagnostics);

        var mechanicalRequests = command.Arguments
            .Select(static argument => argument.ValueSchemaRevision)
            .Concat(command.Options
                .Where(static option => option.ValueSchemaRevision is not null)
                .Select(static option => option.ValueSchemaRevision!))
            .Concat(command.StandardInput is null
                ? []
                : [command.StandardInput.SchemaRevision]);
        var mechanicalDiagnostics = command.ExitCodes
            .SelectMany(static exit => exit.DiagnosticSchemaRevisions)
            .Concat(command.StandardError is null
                ? []
                : [command.StandardError.SchemaRevision]);
        if (!ExactSet(command.RequestSchemaRevisions, mechanicalRequests))
        {
            Error(
                diagnostics,
                "The explicit request schema set must exactly match argument, option, and stdin projections.",
                string.Concat(path, "/requestSchemaRevisions"));
        }

        if (!ExactSet(command.DiagnosticSchemaRevisions, mechanicalDiagnostics))
        {
            Error(
                diagnostics,
                "The explicit diagnostic schema set must exactly match exit and stderr projections.",
                string.Concat(path, "/diagnosticSchemaRevisions"));
        }

        if (command.StandardOutput is not null &&
            !command.ResultSchemaRevisions.Contains(
                command.StandardOutput.SchemaRevision))
        {
            Error(
                diagnostics,
                "The stdout schema must be declared by the explicit result schema set.",
                string.Concat(path, "/standardOutput/schemaRevision"));
        }
    }

    private static void ValidateStreams(
        OpenConsoleCommandAlpha2 command,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var streams = new[]
        {
            (Name: "standardInput", Value: command.StandardInput),
            (Name: "standardOutput", Value: command.StandardOutput),
            (Name: "standardError", Value: command.StandardError),
        };
        foreach (var stream in streams)
        {
            if (stream.Value is not null && stream.Value.SchemaRevision is null)
            {
                Error(
                    diagnostics,
                    "Every present stream requires a non-null exact schema revision.",
                    string.Concat(path, "/", stream.Name, "/schemaRevision"));
            }
        }
    }

    private static void RequireUniqueInitialized(
        ImmutableArray<ArtifactReference> references,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (references.IsDefault ||
            references.Select(Exact).Distinct(StringComparer.Ordinal).Count() !=
            references.Length)
        {
            Error(
                diagnostics,
                "Schema revision sets must be initialized and contain unique exact revisions.",
                path);
        }
    }

    private static bool ExactSet(
        ImmutableArray<ArtifactReference> expected,
        IEnumerable<ArtifactReference> actual) =>
        !expected.IsDefault &&
        expected.Select(Exact).ToHashSet(StringComparer.Ordinal)
            .SetEquals(actual.Select(Exact));

    private static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    private static void Error(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string message,
        string path) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                OpenConsoleDiagnosticIds.InvalidDocument,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));
}
