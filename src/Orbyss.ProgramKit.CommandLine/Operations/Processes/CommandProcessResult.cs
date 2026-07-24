namespace Orbyss.ProgramKit.CommandLine.Operations.Processes;

/// <summary>Captured result from one contained child-process invocation.</summary>
public sealed record CommandProcessResult(
    int ExitCode,
    string StandardOutput,
    string StandardError);
