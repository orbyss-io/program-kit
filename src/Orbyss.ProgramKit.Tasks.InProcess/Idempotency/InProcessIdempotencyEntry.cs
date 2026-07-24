using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.InProcess.Idempotency;

internal sealed record InProcessIdempotencyEntry(
    ArtifactReference InstanceRevision,
    bool Completed,
    DateTimeOffset ExpiresAt);
