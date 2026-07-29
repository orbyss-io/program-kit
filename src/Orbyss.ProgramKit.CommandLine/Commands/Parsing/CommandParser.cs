using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Commands.Parsing;

/// <summary>Deterministic parser for exact long options and OS-provided tokens.</summary>
public sealed class CommandParser : ICommandParser
{
    private readonly ImmutableArray<CommandDescriptor> descriptors;

    /// <summary>Initializes a parser from an explicit finite descriptor set.</summary>
    public CommandParser(IEnumerable<CommandDescriptor> descriptors)
    {
        ArgumentNullException.ThrowIfNull(descriptors);
        this.descriptors = [.. descriptors];
        ValidateDescriptors(this.descriptors);
    }

    /// <inheritdoc />
    public CommandInvocation Parse(IReadOnlyList<string> tokens)
    {
        ArgumentNullException.ThrowIfNull(tokens);
        var descriptor = ResolveDescriptor(tokens);
        var argumentBuilder = ImmutableArray.CreateBuilder<string>();
        var optionBuilder = ImmutableDictionary.CreateBuilder<string, string>(
            StringComparer.Ordinal);
        var definitions = descriptor.Options.ToDictionary(
            static option => option.Name,
            StringComparer.Ordinal);
        for (var index = descriptor.Path.Length; index < tokens.Count; index++)
        {
            var token = tokens[index];
            if (!token.StartsWith("--", StringComparison.Ordinal))
            {
                argumentBuilder.Add(token);
                continue;
            }

            var separator = token.IndexOf('=', StringComparison.Ordinal);
            var name = separator < 0 ? token[2..] : token[2..separator];
            if (!definitions.TryGetValue(name, out var definition))
            {
                throw new CommandInvocationException(
                    $"Unknown option '--{name}'.",
                    string.Concat("/options/", name));
            }

            if (optionBuilder.ContainsKey(name))
            {
                throw new CommandInvocationException(
                    $"Option '--{name}' may occur only once.",
                    string.Concat("/options/", name));
            }

            string value;
            if (definition.RequiresValue)
            {
                if (separator >= 0)
                {
                    value = token[(separator + 1)..];
                }
                else
                {
                    index++;
                    if (index >= tokens.Count ||
                        tokens[index].StartsWith("--", StringComparison.Ordinal))
                    {
                        throw new CommandInvocationException(
                            $"Option '--{name}' requires one value.",
                            string.Concat("/options/", name));
                    }

                    value = tokens[index];
                }

                if (string.IsNullOrWhiteSpace(value))
                {
                    throw new CommandInvocationException(
                        $"Option '--{name}' requires a non-empty value.",
                        string.Concat("/options/", name));
                }
            }
            else
            {
                if (separator >= 0)
                {
                    throw new CommandInvocationException(
                        $"Flag '--{name}' does not accept a value.",
                        string.Concat("/options/", name));
                }

                value = "true";
            }

            ValidateAllowedValue(definition.AllowedValues, value, name);
            optionBuilder.Add(name, value);
        }

        ValidateArguments(descriptor, argumentBuilder);
        foreach (var required in descriptor.Options.Where(static option => option.Required))
        {
            if (!optionBuilder.ContainsKey(required.Name))
            {
                throw new CommandInvocationException(
                    $"Required option '--{required.Name}' is missing.",
                    string.Concat("/options/", required.Name));
            }
        }

        var invocation = new CommandInvocation(
            descriptor,
            argumentBuilder.ToImmutable(),
            optionBuilder.ToImmutable());
        CommandInvocationValidator.Validate(invocation);
        return invocation;
    }

    private CommandDescriptor ResolveDescriptor(IReadOnlyList<string> tokens)
    {
        var matches = descriptors
            .Where(descriptor =>
                tokens.Count >= descriptor.Path.Length &&
                descriptor.Path
                    .Select((part, index) => string.Equals(
                        part,
                        tokens[index],
                        StringComparison.Ordinal))
                    .All(static matches => matches))
            .OrderByDescending(static descriptor => descriptor.Path.Length)
            .ToArray();
        if (matches.Length == 0)
        {
            throw new CommandInvocationException(
                "An exact Program Kit command path is required.",
                "/command");
        }

        return matches[0];
    }

    private static void ValidateArguments(
        CommandDescriptor descriptor,
        ImmutableArray<string>.Builder supplied)
    {
        var required = descriptor.Arguments.Count(static argument => argument.Required);
        var allowsMultiple = descriptor.Arguments.Any(static argument => argument.Multiple);
        var maximum = allowsMultiple ? int.MaxValue : descriptor.Arguments.Length;
        if (supplied.Count < required || supplied.Count > maximum)
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Expected ",
                    Synopsis(descriptor),
                    "; received ",
                    supplied.Count,
                    " positional argument(s)."),
                "/arguments");
        }

        for (var index = 0; index < supplied.Count; index++)
        {
            var definition = descriptor.Arguments[
                Math.Min(index, descriptor.Arguments.Length - 1)];
            ValidateAllowedValue(
                definition.AllowedValues,
                supplied[index],
                definition.Name);
        }
    }

    private static void ValidateAllowedValue(
        IReadOnlySet<string>? allowedValues,
        string value,
        string name)
    {
        if (allowedValues is not null && !allowedValues.Contains(value))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Value '",
                    value,
                    "' is not allowed for '",
                    name,
                    "'. Allowed values: ",
                    string.Join(
                        ", ",
                        allowedValues.Order(StringComparer.Ordinal)),
                    "."),
                string.Concat("/", name));
        }
    }

    private static string Synopsis(CommandDescriptor descriptor)
    {
        var arguments = descriptor.Arguments.Select(
            static argument =>
                argument.Multiple
                    ? string.Concat("<", argument.Name, ">...")
                    : argument.Required
                        ? string.Concat("<", argument.Name, ">")
                        : string.Concat("[", argument.Name, "]"));
        return string.Join(
            " ",
            descriptor.Path
                .Prepend("program-kit")
                .Concat(arguments));
    }

    private static void ValidateDescriptors(
        ImmutableArray<CommandDescriptor> descriptors)
    {
        if (descriptors.IsDefaultOrEmpty)
        {
            throw new ArgumentException(
                "At least one command descriptor is required.",
                nameof(descriptors));
        }

        var keys = new HashSet<string>(StringComparer.Ordinal);
        var paths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var descriptor in descriptors)
        {
            if (descriptor is null ||
                string.IsNullOrWhiteSpace(descriptor.Key) ||
                descriptor.Path.IsDefaultOrEmpty ||
                !keys.Add(descriptor.Key) ||
                !paths.Add(string.Join(" ", descriptor.Path)))
            {
                throw new ArgumentException(
                    "Command keys and paths must be explicit and unique.",
                    nameof(descriptors));
            }
        }
    }
}
