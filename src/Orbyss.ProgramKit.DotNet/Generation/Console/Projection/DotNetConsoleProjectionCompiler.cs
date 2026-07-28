using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed class DotNetConsoleProjectionCompiler :
    IDotNetConsoleProjectionCompiler
{
    private static readonly Dictionary<string, string> ElementTypes =
        new(StringComparer.Ordinal)
        {
            ["string"] = "global::System.String",
            ["boolean"] = "global::System.Boolean",
            ["int32"] = "global::System.Int32",
            ["int64"] = "global::System.Int64",
            ["decimal"] = "global::System.Decimal",
            ["guid"] = "global::System.Guid",
            ["date-time"] = "global::System.DateTimeOffset",
        };

    public DotNetConsoleProjectionResult Compile(
        OpenConsoleDocument document,
        DotNetConsoleBindingDocument binding)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(binding);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        var commands = ImmutableArray.CreateBuilder<DotNetConsoleCommandProjection>();
        var bindingByOperation = binding.Operations.ToDictionary(
            static operation => Exact(operation.OperationRevision),
            StringComparer.Ordinal);
        foreach (var command in document.Commands.OrderBy(
                     static item => string.Join(" ", item.Path),
                     StringComparer.Ordinal))
        {
            if (!bindingByOperation.TryGetValue(
                    Exact(command.OperationRevision),
                    out var operation))
            {
                Error(
                    diagnostics,
                    "The Console projection requires one exact operation binding.",
                    "/commands");
                continue;
            }

            var values = CompileValues(
                document.GlobalOptions,
                command,
                operation,
                diagnostics);
            commands.Add(
                new DotNetConsoleCommandProjection(
                    command.Path,
                    command.Aliases,
                    command.Summary,
                    operation.GeneratedSymbol,
                    string.Concat(operation.GeneratedSymbol, "Settings"),
                    string.Concat(operation.GeneratedSymbol, "Command"),
                    string.Concat(operation.GeneratedSymbol, "RequestFactory"),
                    operation.RequestType,
                    operation.HandlerType,
                    operation.ValidatorType,
                    values));
        }

        if (diagnostics.Count > 0)
        {
            return new DotNetConsoleProjectionResult(
                null,
                diagnostics.ToImmutable());
        }

        var commandArray = commands.ToImmutable();
        var trie = CompileTrie(commandArray, diagnostics);
        if (diagnostics.Count > 0)
        {
            return new DotNetConsoleProjectionResult(
                null,
                diagnostics.ToImmutable());
        }

        var assemblyName = string.Concat(document.Info.Name, ".Cli.Host");
        if (!IsSafeAssemblyName(assemblyName))
        {
            Error(
                diagnostics,
                "Open Console info.name cannot form a safe generated assembly name.",
                "/info/name");
            return new DotNetConsoleProjectionResult(
                null,
                diagnostics.ToImmutable());
        }

        return new DotNetConsoleProjectionResult(
            new DotNetConsoleHostProjection(
                document.Info.Name,
                document.Info.Version.Value,
                assemblyName,
                binding.ConsumerProject.RelativeProjectPath,
                binding.FeatureType,
                binding.ValidationResultType,
                commandArray,
                trie),
            diagnostics.ToImmutable());
    }

    private static ImmutableArray<DotNetConsoleValueProjection> CompileValues(
        ImmutableArray<OpenConsoleOption> globalOptions,
        OpenConsoleCommand command,
        DotNetConsoleOperationBinding operation,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var values = ImmutableArray.CreateBuilder<DotNetConsoleValueProjection>();
        foreach (var parameter in operation.ConstructorParameters.OrderBy(
                     static item => item.Position))
        {
            if (parameter.Source.Kind == DotNetConsoleBindingSourceKind.Argument)
            {
                var argument = command.Arguments.Single(item =>
                    item.Name == parameter.Source.Name);
                AddValue(
                    values,
                    parameter,
                    argument.ValueType,
                    argument.Occurrence,
                    argument.Required,
                    false,
                    argument.Position,
                    string.Concat(
                        argument.Required ? "<" : "[",
                        argument.Name,
                        argument.Required ? ">" : "]"),
                    argument.Summary,
                    diagnostics);
                continue;
            }

            var option = globalOptions
                .Concat(command.Options)
                .Single(item => item.LongName == parameter.Source.Name);
            if (option.Kind == ConsoleOptionKind.Value &&
                option.ValueArity is not { Minimum: 1, Maximum: 1 })
            {
                Error(
                    diagnostics,
                    "Spectre.Console.Cli 0.55.0 projection supports exactly one value token per value-option occurrence.",
                    "/commands/options/valueArity");
                continue;
            }

            AddValue(
                values,
                parameter,
                option.ValueType,
                option.Occurrence,
                option.Required,
                option.Kind == ConsoleOptionKind.Flag,
                -1,
                OptionTemplate(option),
                option.Summary,
                diagnostics);
        }

        return values.ToImmutable();
    }

    private static void AddValue(
        ImmutableArray<DotNetConsoleValueProjection>.Builder values,
        DotNetConsoleConstructorParameter parameter,
        string logicalType,
        ConsoleOccurrence occurrence,
        bool required,
        bool flag,
        int argumentPosition,
        string attributeTemplate,
        string summary,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!ElementTypes.TryGetValue(logicalType, out var elementType))
        {
            Error(
                diagnostics,
                "The logical value type has no pinned Spectre projection.",
                "/commands");
            return;
        }

        var repeated = occurrence.Maximum > 1;
        var propertyType = repeated
            ? string.Concat(elementType, "[]?")
            : flag
                ? elementType
                : string.Concat(elementType, "?");
        values.Add(
            new DotNetConsoleValueProjection(
                parameter.Position,
                parameter.Name,
                parameter.Source.Kind,
                parameter.Source.Name,
                string.Concat("Value", parameter.Position),
                propertyType,
                elementType,
                attributeTemplate,
                summary,
                argumentPosition,
                required,
                repeated,
                flag,
                parameter.ClrType,
                parameter.DefaultDisposition));
    }

    private static string OptionTemplate(OpenConsoleOption option)
    {
        var names = ImmutableArray.CreateBuilder<string>();
        names.Add(string.Concat("--", option.LongName));
        if (option.ShortName is not null)
        {
            names.Add(string.Concat("-", option.ShortName));
        }

        names.AddRange(option.Aliases.Order(StringComparer.Ordinal));
        var template = string.Join(
            "|",
            names.Distinct(StringComparer.Ordinal));
        return option.Kind == ConsoleOptionKind.Flag
            ? template
            : string.Concat(
                template,
                " <",
                option.LongName.ToUpperInvariant(),
                ">");
    }

    private static ImmutableArray<DotNetConsoleCommandTrieNode> CompileTrie(
        ImmutableArray<DotNetConsoleCommandProjection> commands,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        DotNetConsoleMutableTrieNode root = new(string.Empty);
        foreach (var command in commands)
        {
            AddPath(root, command.Path, command, diagnostics);
            foreach (var alias in command.Aliases)
            {
                AddPath(root, alias, command, diagnostics);
            }
        }

        return root.Children.Values
            .OrderBy(static node => node.Token, StringComparer.Ordinal)
            .Select(Freeze)
            .ToImmutableArray();
    }

    private static void AddPath(
        DotNetConsoleMutableTrieNode root,
        ImmutableArray<string> path,
        DotNetConsoleCommandProjection command,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var current = root;
        foreach (var token in path)
        {
            if (!current.Children.TryGetValue(token, out var child))
            {
                child = new DotNetConsoleMutableTrieNode(token);
                current.Children.Add(token, child);
            }

            current = child;
        }

        if (current.Command is not null)
        {
            Error(
                diagnostics,
                "A canonical command path or alias collides in the Spectre command trie.",
                "/commands/path");
            return;
        }

        current.Command = command;
    }

    private static DotNetConsoleCommandTrieNode Freeze(
        DotNetConsoleMutableTrieNode node) =>
        new(
            node.Token,
            node.Command,
            node.Children.Values
                .OrderBy(static child => child.Token, StringComparer.Ordinal)
                .Select(Freeze)
                .ToImmutableArray());

    private static bool IsSafeAssemblyName(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        value.Length <= 256 &&
        value.All(static character =>
            char.IsAsciiLetterOrDigit(character) ||
            character is '.' or '-' or '_');

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
                DotNetDiagnosticIds.ConsoleProjectionFailed,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));
}
