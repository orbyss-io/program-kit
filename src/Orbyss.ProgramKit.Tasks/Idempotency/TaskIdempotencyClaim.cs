using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Idempotency;

/// <summary>One exact process-local idempotency claim request.</summary>
public sealed record TaskIdempotencyClaim(
    ArtifactReference PolicyRevision,
    ArtifactReference DefinitionRevision,
    string Key);
