using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.OpenConsole.Contracts.Validation;

/// <summary>Deterministic semantic validator for Open Console 1.0.</summary>
public sealed class OpenConsoleDocumentValidator :
    IProgramKitSemanticValidator<OpenConsoleDocument>
{
    private static readonly HashSet<string> ValueTypes =
        new(
            ["string", "boolean", "int32", "int64", "decimal", "guid", "date-time"],
            StringComparer.Ordinal);

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OpenConsoleDocument document)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (document is null)
        {
            Error(diagnostics, "An Open Console document is required.", string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (document.Schema != "pkid:schema:program-kit:open-console@1.0.0" ||
            document.DocumentVersion.Value != "1.0.0" ||
            !document.Parsing.ConsumesOperatingSystemTokenArray ||
            document.Parsing.OptionTerminator != "--" ||
            !document.Parsing.SupportsLongEqualsSyntax ||
            !document.Parsing.CaseSensitive ||
            document.Parsing.ConversionCulture != "invariant")
        {
            Error(
                diagnostics,
                "Open Console must select the exact 1.0.0 schema and frozen token-array parsing conventions.",
                string.Empty);
        }

        if (document.Commands.IsDefaultOrEmpty ||
            document.GlobalOptions.IsDefault ||
            !IsToken(document.Help.LongOption) ||
            document.Help.ShortOption.Length != 1 ||
            !IsToken(document.Completion.LongOption) ||
            document.Help.ExitCode < 0)
        {
            Error(
                diagnostics,
                "Open Console commands, global options, help, and completion must be explicit and valid.",
                "/commands");
            return ProgramKitValidationResult.From(diagnostics);
        }

        var commandPaths = new HashSet<string>(StringComparer.Ordinal);
        var operationKeys = new HashSet<string>(StringComparer.Ordinal);
        foreach (var command in document.Commands)
        {
            var path = string.Join(" ", command.Path);
            if (command.Path.IsDefaultOrEmpty ||
                command.Path.Any(static token => !IsToken(token)) ||
                !commandPaths.Add(path) ||
                !operationKeys.Add(Exact(command.OperationRevision)))
            {
                Error(
                    diagnostics,
                    "Command paths and operation revisions must be non-empty and unique.",
                    "/commands");
            }

            if (command.Aliases.IsDefault)
            {
                Error(
                    diagnostics,
                    "Command aliases must be initialized token arrays.",
                    "/commands/aliases");
            }
            else
            {
                foreach (var alias in command.Aliases)
                {
                    var aliasPath = string.Join(" ", alias);
                    if (alias.IsDefaultOrEmpty ||
                        alias.Any(static token => !IsToken(token)) ||
                        !commandPaths.Add(aliasPath))
                    {
                        Error(
                            diagnostics,
                            "Command aliases must be unique non-empty token arrays.",
                            "/commands/aliases");
                    }
                }
            }

            ValidateArguments(command.Arguments, diagnostics);
            ValidateOptions(document.GlobalOptions, command.Options, diagnostics);
            if (command.ExitCodes.IsDefaultOrEmpty ||
                !command.ExitCodes.Any(static exit => exit.Code == 0) ||
                !command.ExitCodes.Any(static exit => exit.Code == 2) ||
                command.ExitCodes.Select(static exit => exit.Code).Distinct().Count() !=
                command.ExitCodes.Length)
            {
                Error(
                    diagnostics,
                    "Each command requires an exhaustive unique exit map including success code 0 and invalid-invocation code 2.",
                    "/commands/exitCodes");
            }
        }

        var provenance = document.Provenance.OperationRevisions.IsDefault
            ? []
            : document.Provenance.OperationRevisions
                .Select(Exact)
                .ToHashSet(StringComparer.Ordinal);
        if (!operationKeys.SetEquals(provenance))
        {
            Error(
                diagnostics,
                "Console provenance must bind exactly the projected operations.",
                "/provenance/operationRevisions");
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateArguments(
        ImmutableArray<OpenConsoleArgument> arguments,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (arguments.IsDefault)
        {
            Error(
                diagnostics,
                "Command arguments must be initialized.",
                "/commands/arguments");
            return;
        }

        for (var index = 0; index < arguments.Length; index++)
        {
            var argument = arguments[index];
            if (argument.Position != index ||
                !IsToken(argument.Name) ||
                !ValueTypes.Contains(argument.ValueType) ||
                argument.ValueArity is not { Minimum: 1, Maximum: 1 } ||
                !ValidRange(
                    argument.Occurrence.Minimum,
                    argument.Occurrence.Maximum) ||
                argument.Required != (argument.Occurrence.Minimum > 0) ||
                (argument.DefaultValue is not null &&
                 !HasValidValue(argument.ValueType, argument.DefaultValue)))
            {
                Error(
                    diagnostics,
                    "Arguments require contiguous positions, token names, known types, one token per occurrence, valid occurrence, typed defaults, and consistent required state.",
                    "/commands/arguments");
            }
        }
    }

    private static void ValidateOptions(
        ImmutableArray<OpenConsoleOption> globalOptions,
        ImmutableArray<OpenConsoleOption> commandOptions,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (commandOptions.IsDefault)
        {
            Error(
                diagnostics,
                "Command options must be initialized.",
                "/commands/options");
            return;
        }

        var names = new HashSet<string>(StringComparer.Ordinal);
        var options = globalOptions.Concat(commandOptions).ToArray();
        foreach (var option in options)
        {
            var valid = IsToken(option.LongName) &&
                        ValueTypes.Contains(option.ValueType) &&
                        ValidRange(
                            option.ValueArity.Minimum,
                            option.ValueArity.Maximum) &&
                        ValidRange(
                            option.Occurrence.Minimum,
                            option.Occurrence.Maximum) &&
                        option.Occurrence.Maximum > 0 &&
                        option.Required == (option.Occurrence.Minimum > 0) &&
                        !option.Aliases.IsDefault &&
                        !option.Conflicts.IsDefault &&
                        !option.Prerequisites.IsDefault &&
                        names.Add(string.Concat("--", option.LongName));
            valid &= option.Kind switch
            {
                ConsoleOptionKind.Flag =>
                    option.ValueType == "boolean" &&
                    option.ValueArity is { Minimum: 0, Maximum: 0 } &&
                    option.DefaultValue is null,
                ConsoleOptionKind.Value =>
                    option.ValueArity.Minimum > 0 &&
                    (option.DefaultValue is null ||
                     HasValidValue(option.ValueType, option.DefaultValue)),
                _ => false,
            };
            if (option.ShortName is not null)
            {
                valid &= option.ShortName.Length == 1 &&
                         names.Add(string.Concat("-", option.ShortName));
            }

            foreach (var alias in option.Aliases)
            {
                valid &= alias.StartsWith('-') && names.Add(alias);
            }

            if (!valid)
            {
                Error(
                    diagnostics,
                    "Options require unique names, known types, and valid arity/occurrence.",
                    "/commands/options");
            }
        }

        var canonicalNames = options
            .Select(static option => option.LongName)
            .ToHashSet(StringComparer.Ordinal);
        foreach (var option in options)
        {
            if (option.Conflicts.Any(name =>
                    name == option.LongName ||
                    !canonicalNames.Contains(name)) ||
                option.Prerequisites.Any(name =>
                    name == option.LongName ||
                    !canonicalNames.Contains(name)) ||
                option.Conflicts.Intersect(
                    option.Prerequisites,
                    StringComparer.Ordinal).Any())
            {
                Error(
                    diagnostics,
                    "Option conflicts and prerequisites must reference distinct canonical options in the same command.",
                    "/commands/options");
            }
        }
    }

    private static bool IsToken(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        char.IsAsciiLetterOrDigit(value[0]) &&
        value.All(static character =>
            char.IsAsciiLetterOrDigit(character) || character == '-');

    private static bool ValidRange(int minimum, int maximum) =>
        minimum >= 0 && maximum >= minimum;

    private static bool HasValidValue(string valueType, string value) =>
        valueType switch
        {
            "string" => true,
            "boolean" => bool.TryParse(value, out _),
            "int32" => int.TryParse(
                value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out _),
            "int64" => long.TryParse(
                value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out _),
            "decimal" => decimal.TryParse(
                value,
                NumberStyles.Number,
                CultureInfo.InvariantCulture,
                out _),
            "guid" => Guid.TryParseExact(value, "D", out _),
            "date-time" => DateTimeOffset.TryParseExact(
                value,
                "O",
                CultureInfo.InvariantCulture,
                DateTimeStyles.None,
                out _),
            _ => false,
        };

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
