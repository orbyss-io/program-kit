using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Planning.Approvals;

namespace Orbyss.ProgramKit.Development.Receipts;

/// <summary>
/// Provides evidence of a development-capability invocation without granting implementation,
/// approval, release, or any other authority.
/// </summary>
public sealed record DevelopmentReceipt(
    ArtifactReference Capability,
    ArtifactReference RequestOrIntent,
    ImmutableArray<ArtifactReference> ConsumedArtifacts,
    DevelopmentResult Result,
    ProgramKitIdentifier ProducerId,
    PrincipalReference Principal,
    string CorrelationId,
    DateTimeOffset SuppliedAt);
