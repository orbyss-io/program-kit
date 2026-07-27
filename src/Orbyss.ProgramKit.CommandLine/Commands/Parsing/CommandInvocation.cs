using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;

namespace Orbyss.ProgramKit.CommandLine.Commands.Parsing;

/// <summary>One fully parsed invocation of an exact command descriptor.</summary>
public sealed record CommandInvocation(
    CommandDescriptor Descriptor,
    ImmutableArray<string> Arguments,
    ImmutableDictionary<string, string> Options)
{
    /// <summary>Gets one required option value.</summary>
    public string RequiredOption(string name) =>
        Options.TryGetValue(name, out var value)
            ? value
            : throw new InvalidOperationException(
                $"The parsed invocation has no required '--{name}' option.");

    /// <summary>Gets one optional option value.</summary>
    public string? OptionalOption(string name) =>
        Options.GetValueOrDefault(name);
}
