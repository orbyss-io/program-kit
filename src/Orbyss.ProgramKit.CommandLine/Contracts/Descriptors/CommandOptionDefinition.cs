namespace Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;

/// <summary>One exact long-form command option.</summary>
public sealed record CommandOptionDefinition(
    string Name,
    bool RequiresValue,
    bool Required,
    IReadOnlySet<string>? AllowedValues = null);
