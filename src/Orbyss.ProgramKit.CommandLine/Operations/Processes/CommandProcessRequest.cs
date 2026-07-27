using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Processes;

/// <summary>One shell-free child-process invocation with explicit arguments and environment.</summary>
public sealed record CommandProcessRequest(
    string Executable,
    string WorkingDirectory,
    ImmutableArray<string> Arguments,
    ImmutableDictionary<string, string> Environment);
