using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Idempotency;

/// <summary>Outcome of one process-local idempotency claim.</summary>
public sealed record TaskIdempotencyResult(
    TaskIdempotencyDisposition Disposition,
    ArtifactReference? ExistingInstanceRevision);
