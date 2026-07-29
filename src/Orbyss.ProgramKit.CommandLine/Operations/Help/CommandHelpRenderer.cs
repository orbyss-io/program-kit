using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;

namespace Orbyss.ProgramKit.CommandLine.Operations.Help;

/// <summary>Descriptor-backed help with no second prose command catalog.</summary>
public sealed class CommandHelpRenderer : ICommandHelpRenderer
{
    private static readonly UTF8Encoding Utf8 = new(false);
    private readonly CommandDescriptor[] descriptors;

    /// <summary>Initializes help from the exact parser descriptor set.</summary>
    public CommandHelpRenderer(IEnumerable<CommandDescriptor> descriptors)
    {
        ArgumentNullException.ThrowIfNull(descriptors);
        this.descriptors = descriptors
            .OrderBy(static item => string.Join(" ", item.Path), StringComparer.Ordinal)
            .ToArray();
        if (this.descriptors.Length == 0)
        {
            throw new ArgumentException(
                "The command help catalog cannot be empty.",
                nameof(descriptors));
        }
    }

    /// <inheritdoc />
    public byte[] RenderTopLevel(bool firstUse)
    {
        StringBuilder output = new();
        output.Append("Program Kit ")
            .Append(ProgramKitProductInfo.Version)
            .AppendLine();
        if (firstUse)
        {
            output.AppendLine(
                "First use: program-kit capabilities initialize --provider <codex|claude> --workspace-root .");
            output.AppendLine(
                "Installation does not initialize capabilities or grant authority.");
        }

        output.AppendLine("Usage: program-kit <command> [arguments] [options]");
        output.AppendLine();
        output.AppendLine("Commands:");
        foreach (var descriptor in descriptors)
        {
            output.Append("  ")
                .Append(string.Join(" ", descriptor.Path))
                .Append("  ")
                .AppendLine(descriptor.Description);
        }

        output.AppendLine();
        output.AppendLine(
            "Use 'program-kit <command-path> --help' for exact arguments, options, allowed values, authority, and an example.");
        return Utf8.GetBytes(output.ToString());
    }

    /// <inheritdoc />
    public byte[] RenderCommandPath(IReadOnlyList<string> path)
    {
        ArgumentNullException.ThrowIfNull(path);
        var matches = descriptors.Where(
                descriptor =>
                    descriptor.Path.SequenceEqual(path, StringComparer.Ordinal))
            .ToArray();
        if (matches.Length != 1)
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Unknown Program Kit command path '",
                    string.Join(" ", path),
                    "'. Use 'program-kit --help' to list exact paths."),
                "/command");
        }

        return RenderDescriptor(matches[0], "text");
    }

    /// <inheritdoc />
    public byte[] RenderDescriptor(CommandDescriptor descriptor, string format)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        return format switch
        {
            "json" => RenderJson(descriptor),
            "text" => RenderText(descriptor),
            _ => throw new CommandInvocationException(
                "Help format must be one of: json, text.",
                "/options/format"),
        };
    }

    private static byte[] RenderText(CommandDescriptor descriptor)
    {
        StringBuilder output = new();
        output.AppendLine(descriptor.Description);
        output.Append("Usage: ")
            .AppendLine(Synopsis(descriptor));
        output.Append("Command key: ")
            .AppendLine(descriptor.Key);
        output.Append("Authority: ")
            .AppendLine(descriptor.Authority);
        if (!descriptor.Arguments.IsDefaultOrEmpty)
        {
            output.AppendLine("Arguments:");
            foreach (var argument in descriptor.Arguments)
            {
                output.Append("  ")
                    .Append(argument.Name)
                    .Append(argument.Required ? " (required)" : " (optional)");
                AppendAllowed(output, argument.AllowedValues);
                output.AppendLine();
            }
        }

        if (!descriptor.Options.IsDefaultOrEmpty)
        {
            output.AppendLine("Options:");
            foreach (var option in descriptor.Options)
            {
                output.Append("  --")
                    .Append(option.Name);
                if (option.RequiresValue)
                {
                    output.Append(" <value>");
                }

                output.Append(option.Required ? " (required)" : " (optional)");
                AppendAllowed(output, option.AllowedValues);
                output.AppendLine();
            }
        }

        output.Append("Example: ")
            .AppendLine(descriptor.Example);
        output.AppendLine(
            "Exit classes: 0 success; 1 conformance failure; 2 usage/input or unavailable operation; 3 internal failure.");
        return Utf8.GetBytes(output.ToString());
    }

    private static byte[] RenderJson(CommandDescriptor descriptor)
    {
        using MemoryStream output = new();
        using (Utf8JsonWriter writer = new(output))
        {
            writer.WriteStartObject();
            writer.WriteString("authority", descriptor.Authority);
            writer.WriteString("description", descriptor.Description);
            writer.WriteString("example", descriptor.Example);
            writer.WriteString("key", descriptor.Key);
            writer.WriteStartArray("path");
            foreach (var part in descriptor.Path)
            {
                writer.WriteStringValue(part);
            }

            writer.WriteEndArray();
            writer.WriteString("usage", Synopsis(descriptor));
            WriteArguments(writer, descriptor);
            WriteOptions(writer, descriptor);
            writer.WriteStartObject("exitClasses");
            writer.WriteNumber("conformanceFailure", 1);
            writer.WriteNumber("internalFailure", 3);
            writer.WriteNumber("success", 0);
            writer.WriteNumber("usageInputOrUnavailable", 2);
            writer.WriteEndObject();
            writer.WriteEndObject();
        }

        return output.ToArray();
    }

    private static void WriteArguments(
        Utf8JsonWriter writer,
        CommandDescriptor descriptor)
    {
        writer.WriteStartArray("arguments");
        foreach (var argument in descriptor.Arguments)
        {
            writer.WriteStartObject();
            WriteAllowed(writer, argument.AllowedValues);
            writer.WriteBoolean("multiple", argument.Multiple);
            writer.WriteString("name", argument.Name);
            writer.WriteBoolean("required", argument.Required);
            writer.WriteEndObject();
        }

        writer.WriteEndArray();
    }

    private static void WriteOptions(
        Utf8JsonWriter writer,
        CommandDescriptor descriptor)
    {
        writer.WriteStartArray("options");
        foreach (var option in descriptor.Options)
        {
            writer.WriteStartObject();
            WriteAllowed(writer, option.AllowedValues);
            writer.WriteString("name", option.Name);
            writer.WriteBoolean("required", option.Required);
            writer.WriteBoolean("requiresValue", option.RequiresValue);
            writer.WriteEndObject();
        }

        writer.WriteEndArray();
    }

    private static void WriteAllowed(
        Utf8JsonWriter writer,
        IReadOnlySet<string>? values)
    {
        writer.WriteStartArray("allowedValues");
        if (values is not null)
        {
            foreach (var value in values.Order(StringComparer.Ordinal))
            {
                writer.WriteStringValue(value);
            }
        }

        writer.WriteEndArray();
    }

    private static string Synopsis(CommandDescriptor descriptor)
    {
        IEnumerable<string> arguments = descriptor.Arguments.Select(
            static argument =>
                argument.Multiple
                    ? string.Concat("<", argument.Name, ">...")
                    : argument.Required
                        ? string.Concat("<", argument.Name, ">")
                        : string.Concat("[", argument.Name, "]"));
        IEnumerable<string> options = descriptor.Options.Select(
            static option =>
            {
                var value = option.RequiresValue
                    ? string.Concat(
                        " <",
                        option.AllowedValues is null
                            ? "value"
                            : string.Join(
                                "|",
                                option.AllowedValues.Order(StringComparer.Ordinal)),
                        ">")
                    : string.Empty;
                var token = string.Concat("--", option.Name, value);
                return option.Required ? token : string.Concat("[", token, "]");
            });
        return string.Join(
            " ",
            descriptor.Path
                .Prepend("program-kit")
                .Concat(arguments)
                .Concat(options));
    }

    private static void AppendAllowed(
        StringBuilder output,
        IReadOnlySet<string>? allowed)
    {
        if (allowed is null)
        {
            return;
        }

        output.Append("; allowed: ")
            .Append(string.Join(", ", allowed.Order(StringComparer.Ordinal)));
    }
}
