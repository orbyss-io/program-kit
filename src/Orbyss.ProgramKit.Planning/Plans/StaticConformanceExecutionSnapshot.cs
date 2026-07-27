using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// Exact observed activation evidence used only to classify currently
/// admissible work. It grants no authority and performs no execution.
/// </summary>
public sealed record StaticConformanceExecutionSnapshot(
    ArtifactReference SelectionLock,
    ArtifactReference ActivationEvidence,
    ImmutableArray<ArtifactReference> ActivationMatrices,
    ImmutableArray<ArtifactReference> VerificationProfiles);
