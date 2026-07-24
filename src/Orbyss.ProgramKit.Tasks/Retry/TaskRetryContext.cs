using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Retry;

/// <summary>Bounded facts supplied to a selected retry policy.</summary>
public sealed record TaskRetryContext(
    ArtifactReference PolicyRevision,
    ArtifactReference DefinitionRevision,
    ArtifactReference InstanceRevision,
    ArtifactReference AttemptRevision,
    int AttemptNumber,
    string FailureCode);
