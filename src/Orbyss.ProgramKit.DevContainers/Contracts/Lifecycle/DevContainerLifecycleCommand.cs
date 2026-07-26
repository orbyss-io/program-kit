namespace Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;

/// <summary>
/// One exact lifecycle command. Exactly one shell string or exec-form argument
/// array must be supplied; Program Kit never interprets or executes it.
/// </summary>
public sealed record DevContainerLifecycleCommand(
    DevContainerLifecycleStage Stage,
    string? ShellCommand,
    ImmutableArray<string> Arguments);
