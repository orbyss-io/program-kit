using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>
/// Question 8: identity, owner, schema, provenance, digest, consumers,
/// compatibility, and migration responsibilities.
/// </summary>
public sealed record GovernanceAnswer(
    ProgramKitIdentifier ArtifactIdentity,
    ProgramKitIdentifier OwnerId,
    ArtifactReference? Schema,
    string ProvenancePolicy,
    string DigestPolicy,
    ImmutableArray<ProgramKitIdentifier> ConsumerIds,
    string CompatibilityPolicy,
    string MigrationPolicy);
