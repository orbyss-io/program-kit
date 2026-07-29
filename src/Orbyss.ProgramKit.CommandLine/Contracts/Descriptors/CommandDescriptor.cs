using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;

/// <summary>Frozen grammar for one exact command path.</summary>
public sealed record CommandDescriptor(
    string Key,
    ImmutableArray<string> Path,
    ImmutableArray<CommandArgumentDefinition> Arguments,
    ImmutableArray<CommandOptionDefinition> Options,
    string Description,
    string Authority,
    string Example);
