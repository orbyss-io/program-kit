namespace Orbyss.ProgramKit.Tasks.Core.Cancellation;

/// <summary>
/// Cancellation-request result; requested cancellation is not terminal
/// cancellation.
/// </summary>
public sealed record TaskCancellationResult(
    ArtifactReference CancellationRequestRevision,
    ArtifactReference InstanceRevision,
    TaskCancellationDisposition Disposition,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics);
