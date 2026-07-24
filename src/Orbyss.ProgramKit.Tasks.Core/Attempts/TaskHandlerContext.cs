namespace Orbyss.ProgramKit.Tasks.Core.Attempts;

/// <summary>Exact execution context supplied to one consumer-owned handler.</summary>
public sealed record TaskHandlerContext(
    ArtifactReference DefinitionRevision,
    ArtifactReference InstanceRevision,
    ArtifactReference AttemptRevision,
    ArtifactReference ActivationBindingRevision,
    ArtifactReference RequestContract,
    ArtifactReference ResponseContract,
    ArtifactReference FailureContract);
