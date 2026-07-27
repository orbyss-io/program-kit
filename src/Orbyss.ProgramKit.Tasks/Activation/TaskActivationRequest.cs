using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Activation;

/// <summary>Exact provider-neutral request for one fresh handler activation.</summary>
public sealed record TaskActivationRequest(
    ProgramKitIdentifier ActivationIdentity,
    ArtifactReference OwningFeatureRevision,
    ArtifactReference HandlerRevision);
