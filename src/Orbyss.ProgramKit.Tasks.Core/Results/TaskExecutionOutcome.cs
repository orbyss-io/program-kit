namespace Orbyss.ProgramKit.Tasks.Core.Results;

/// <summary>
/// Immutable immediate-execution outcome; rejected work has no instance.
/// </summary>
/// <typeparam name="TResponse">The consumer-owned typed response model.</typeparam>
public sealed record TaskExecutionOutcome<TResponse>(
    ArtifactReference RequestRevision,
    TaskExecutionOutcomeKind Kind,
    ArtifactReference? InstanceRevision,
    TaskResponse<TResponse>? Response,
    TaskFailure? Failure,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics)
    where TResponse : notnull;
