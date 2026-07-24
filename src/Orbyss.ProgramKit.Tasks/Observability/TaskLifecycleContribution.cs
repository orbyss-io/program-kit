using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Modularity.Contributions;

namespace Orbyss.ProgramKit.Tasks.Observability;

/// <summary>Optional post-transition task lifecycle observation.</summary>
public sealed record TaskLifecycleContribution(
    TaskLifecycleKind Kind,
    ArtifactReference DefinitionRevision,
    ArtifactReference InstanceRevision,
    ArtifactReference? AttemptRevision,
    DateTimeOffset ObservedAt) : IDomainContribution;
