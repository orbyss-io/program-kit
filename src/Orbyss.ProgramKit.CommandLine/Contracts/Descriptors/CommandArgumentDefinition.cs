namespace Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;

/// <summary>One ordered positional command argument.</summary>
public sealed record CommandArgumentDefinition(
    string Name,
    bool Required,
    bool Multiple,
    IReadOnlySet<string>? AllowedValues = null);
