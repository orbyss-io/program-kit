namespace Orbyss.ProgramKit.Tasks.Core.Dispatching;

/// <summary>
/// Result returned after background acceptance; rejected work has no instance.
/// </summary>
public sealed record TaskDispatchResult(
    ArtifactReference RequestRevision,
    TaskDispatchDisposition Disposition,
    ArtifactReference? InstanceRevision,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics);
