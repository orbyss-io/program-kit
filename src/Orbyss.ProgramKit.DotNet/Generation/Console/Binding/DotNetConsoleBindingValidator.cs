using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Fail-closed validator for the canonical .NET Console binding contract.</summary>
public sealed class DotNetConsoleBindingValidator : IDotNetConsoleBindingValidator
{
    private static readonly HashSet<string> CSharpKeywords =
        new(
            [
                "abstract", "as", "base", "bool", "break", "byte", "case",
                "catch", "char", "checked", "class", "const", "continue",
                "decimal", "default", "delegate", "do", "double", "else",
                "enum", "event", "explicit", "extern", "false", "finally",
                "fixed", "float", "for", "foreach", "goto", "if", "implicit",
                "in", "int", "interface", "internal", "is", "lock", "long",
                "namespace", "new", "null", "object", "operator", "out",
                "override", "params", "private", "protected", "public",
                "readonly", "ref", "return", "sbyte", "sealed", "short",
                "sizeof", "stackalloc", "static", "string", "struct", "switch",
                "this", "throw", "true", "try", "typeof", "uint", "ulong",
                "unchecked", "unsafe", "ushort", "using", "virtual", "void",
                "volatile", "while",
            ],
            StringComparer.Ordinal);

    private static readonly Dictionary<string, string> ScalarTypes =
        new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["string"] = "System.String",
            ["boolean"] = "System.Boolean",
            ["int32"] = "System.Int32",
            ["int64"] = "System.Int64",
            ["decimal"] = "System.Decimal",
            ["guid"] = "System.Guid",
            ["date-time"] = "System.DateTimeOffset",
        };

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        DotNetConsoleBindingDocument binding,
        OpenConsoleDocument openConsole)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (binding is null || openConsole is null)
        {
            Error(
                diagnostics,
                "A .NET Console binding and Open Console document are required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateHeader(binding, diagnostics);
        ValidateProject(binding.ConsumerProject, diagnostics);
        ValidateType(binding.FeatureType, "/featureType", diagnostics);
        ValidateType(
            binding.ValidationResultType,
            "/validationResultType",
            diagnostics);
        ValidateOperations(binding, openConsole, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateHeader(
        DotNetConsoleBindingDocument binding,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (binding.Schema !=
                "pkid:schema:program-kit:dotnet-console-binding@1.0.0" ||
            binding.Version.Value != "1.0.0" ||
            binding.OpenConsoleDocumentRevision is null ||
            binding.ConsumerProject is null ||
            binding.FeatureType is null ||
            binding.ValidationResultType is null ||
            binding.Operations.IsDefaultOrEmpty)
        {
            Error(
                diagnostics,
                "The binding must select the exact 1.0.0 contract and initialize every compiler input.",
                string.Empty);
        }
    }

    private static void ValidateProject(
        DotNetConsoleConsumerProject project,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (project is null ||
            string.IsNullOrWhiteSpace(project.Name) ||
            project.TargetFramework != "net10.0" ||
            string.IsNullOrWhiteSpace(project.ReferenceAssemblyName) ||
            !IsSafeRelativePath(project.RelativeProjectPath, ".csproj") ||
            !IsSafeRelativePath(
                project.RelativeReferenceAssemblyPath,
                ".dll"))
        {
            Error(
                diagnostics,
                "The consumer project must bind one safe relative net10.0 project and one exact reference assembly digest.",
                "/consumerProject");
        }
    }

    private static void ValidateOperations(
        DotNetConsoleBindingDocument binding,
        OpenConsoleDocument openConsole,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (binding.Operations.IsDefault)
        {
            return;
        }

        var commands = openConsole.Commands.IsDefault
            ? new Dictionary<string, OpenConsoleCommand>(StringComparer.Ordinal)
            : openConsole.Commands.ToDictionary(
                static command => Exact(command.OperationRevision),
                StringComparer.Ordinal);
        var operationKeys = new HashSet<string>(StringComparer.Ordinal);
        var generatedSymbols = new HashSet<string>(StringComparer.Ordinal);
        foreach (var operation in binding.Operations)
        {
            if (operation is null ||
                operation.OperationRevision is null)
            {
                Error(
                    diagnostics,
                    "Every operation binding must identify one Open Console operation.",
                    "/operations");
                continue;
            }

            var key = Exact(operation.OperationRevision);
            if (!operationKeys.Add(key) ||
                !commands.TryGetValue(key, out var command))
            {
                Error(
                    diagnostics,
                    "Operation bindings must reconcile one-to-one with Open Console operation revisions.",
                    "/operations/operationRevision");
                continue;
            }

            ValidateOperation(
                operation,
                command,
                openConsole.GlobalOptions,
                generatedSymbols,
                diagnostics);
        }

        if (operationKeys.Count != commands.Count ||
            commands.Keys.Any(key => !operationKeys.Contains(key)))
        {
            Error(
                diagnostics,
                "Every Open Console command requires exactly one .NET operation binding.",
                "/operations");
        }
    }

    private static void ValidateOperation(
        DotNetConsoleOperationBinding operation,
        OpenConsoleCommand command,
        ImmutableArray<OpenConsoleOption> globalOptions,
        HashSet<string> generatedSymbols,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!IsCSharpIdentifier(operation.GeneratedSymbol) ||
            !generatedSymbols.Add(operation.GeneratedSymbol))
        {
            Error(
                diagnostics,
                "Every operation requires one ordinally unique explicit generated C# symbol.",
                "/operations/generatedSymbol");
        }

        ValidateType(operation.RequestType, "/operations/requestType", diagnostics);
        ValidateType(operation.HandlerType, "/operations/handlerType", diagnostics);
        if (operation.ValidatorType is not null)
        {
            ValidateType(
                operation.ValidatorType,
                "/operations/validatorType",
                diagnostics);
        }

        if (SameType(operation.RequestType, operation.HandlerType) ||
            operation.ValidatorType is not null &&
            (SameType(operation.RequestType, operation.ValidatorType) ||
             SameType(operation.HandlerType, operation.ValidatorType)))
        {
            Error(
                diagnostics,
                "Request, handler, and optional validator contracts must name distinct CLR types.",
                "/operations");
        }

        ValidateConstructor(
            operation,
            command,
            globalOptions,
            diagnostics);
    }

    private static void ValidateConstructor(
        DotNetConsoleOperationBinding operation,
        OpenConsoleCommand command,
        ImmutableArray<OpenConsoleOption> globalOptions,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (operation.ConstructorParameters.IsDefault)
        {
            Error(
                diagnostics,
                "Constructor mappings must be initialized, including for parameterless requests.",
                "/operations/constructorParameters");
            return;
        }

        var expected = Sources(command, globalOptions);
        var names = new HashSet<string>(StringComparer.Ordinal);
        var mapped = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < operation.ConstructorParameters.Length; index++)
        {
            var parameter = operation.ConstructorParameters[index];
            if (parameter is null ||
                parameter.Position != index ||
                !IsCSharpIdentifier(parameter.Name) ||
                !names.Add(parameter.Name) ||
                parameter.Source is null ||
                parameter.DefaultDisposition is null)
            {
                Error(
                    diagnostics,
                    "Constructor parameters require contiguous positions, unique C# names, CLR types, sources, and default dispositions.",
                    "/operations/constructorParameters");
                continue;
            }

            ValidateType(
                parameter.ClrType,
                "/operations/constructorParameters/clrType",
                diagnostics);
            var sourceKey = SourceKey(
                parameter.Source.Kind,
                parameter.Source.Name);
            if (!mapped.Add(sourceKey) ||
                !expected.TryGetValue(sourceKey, out var source))
            {
                Error(
                    diagnostics,
                    "Each constructor parameter must select one distinct argument or canonical long option from its command.",
                    "/operations/constructorParameters/source");
                continue;
            }

            ValidateSourceType(parameter.ClrType, source, diagnostics);
            ValidateDefault(parameter.DefaultDisposition, source, diagnostics);
        }

        if (mapped.Count != expected.Count ||
            expected.Keys.Any(key => !mapped.Contains(key)))
        {
            Error(
                diagnostics,
                "Constructor mappings must cover every command argument, global option, and command option exactly once.",
                "/operations/constructorParameters");
        }
    }

    private static Dictionary<string, SourceContract> Sources(
        OpenConsoleCommand command,
        ImmutableArray<OpenConsoleOption> globalOptions)
    {
        Dictionary<string, SourceContract> sources =
            new(StringComparer.Ordinal);
        foreach (var argument in command.Arguments)
        {
            sources.Add(
                SourceKey(
                    DotNetConsoleBindingSourceKind.Argument,
                    argument.Name),
                new SourceContract(
                    argument.ValueType,
                    argument.Occurrence.Maximum,
                    argument.DefaultValue));
        }

        foreach (var option in globalOptions.Concat(command.Options))
        {
            sources.Add(
                SourceKey(
                    DotNetConsoleBindingSourceKind.Option,
                    option.LongName),
                new SourceContract(
                    option.ValueType,
                    option.Occurrence.Maximum,
                    option.DefaultValue));
        }

        return sources;
    }

    private static void ValidateSourceType(
        DotNetConsoleClrTypeDescriptor type,
        SourceContract source,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!ScalarTypes.TryGetValue(source.ValueType, out var scalarName))
        {
            Error(
                diagnostics,
                "The Open Console logical value type is not supported by the .NET binding contract.",
                "/operations/constructorParameters/clrType");
            return;
        }

        var valid = source.MaximumOccurrence <= 1
            ? type.MetadataName == scalarName &&
              type.GenericArguments.IsDefaultOrEmpty
            : type.MetadataName ==
                  "System.Collections.Immutable.ImmutableArray`1" &&
              type.GenericArguments is { IsDefault: false, Length: 1 } &&
              type.GenericArguments[0].MetadataName == scalarName &&
              type.GenericArguments[0].GenericArguments.IsDefaultOrEmpty;
        if (!valid)
        {
            Error(
                diagnostics,
                "CLR constructor types must exactly match the logical scalar or repeated Open Console source type.",
                "/operations/constructorParameters/clrType");
        }
    }

    private static void ValidateDefault(
        DotNetConsoleDefaultDisposition disposition,
        SourceContract source,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var valid = source.DefaultValue is null
            ? disposition.Kind == DotNetConsoleDefaultKind.None &&
              disposition.CanonicalValue is null
            : disposition.Kind == DotNetConsoleDefaultKind.Canonical &&
              disposition.CanonicalValue == source.DefaultValue;
        if (!valid)
        {
            Error(
                diagnostics,
                "Every constructor parameter must explicitly record none or the exact canonical Open Console default.",
                "/operations/constructorParameters/defaultDisposition");
        }
    }

    private static void ValidateType(
        DotNetConsoleClrTypeDescriptor type,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (type is null ||
            !IsMetadataName(type.MetadataName) ||
            type.GenericArguments.IsDefault ||
            !Enum.IsDefined(type.ReferenceNullability))
        {
            Error(
                diagnostics,
                "CLR types require a metadata name, initialized generic arguments, and explicit reference nullability.",
                path);
            return;
        }

        foreach (var argument in type.GenericArguments)
        {
            ValidateType(argument, path, diagnostics);
        }
    }

    private static bool IsSafeRelativePath(string value, string extension)
    {
        if (string.IsNullOrWhiteSpace(value) ||
            value.Contains('\\') ||
            value.StartsWith('/') ||
            value.Contains(':') ||
            !value.EndsWith(extension, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        var segments = value.Split('/');
        return segments.All(static segment =>
            segment.Length > 0 &&
            segment is not "." and not "..");
    }

    private static bool IsCSharpIdentifier(string value) =>
        !string.IsNullOrEmpty(value) &&
        !CSharpKeywords.Contains(value) &&
        (char.IsAsciiLetter(value[0]) || value[0] == '_') &&
        value.Skip(1).All(static character =>
            char.IsAsciiLetterOrDigit(character) || character == '_');

    private static bool IsMetadataName(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        value.Length <= 512 &&
        (char.IsAsciiLetter(value[0]) || value[0] == '_') &&
        value.All(static character =>
            char.IsAsciiLetterOrDigit(character) ||
            character is '.' or '+' or '_' or '`');

    private static bool SameType(
        DotNetConsoleClrTypeDescriptor left,
        DotNetConsoleClrTypeDescriptor right) =>
        left is not null &&
        right is not null &&
        left.MetadataName == right.MetadataName &&
        left.ReferenceNullability == right.ReferenceNullability &&
        left.GenericArguments.SequenceEqual(right.GenericArguments);

    private static string SourceKey(
        DotNetConsoleBindingSourceKind kind,
        string name) =>
        string.Concat(kind.ToString(), ":", name);

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
                DotNetDiagnosticIds.InvalidConsoleBinding,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));

}
