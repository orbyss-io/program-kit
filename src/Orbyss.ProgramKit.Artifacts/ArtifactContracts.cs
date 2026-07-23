using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts;

/// <summary>The implementation maturity of an artifact, independent of review or approval state.</summary>
public enum ArtifactStatus
{
    /// <summary>The claimed behavior is implemented.</summary>
    Implemented,

    /// <summary>Only a deliberate scaffold exists.</summary>
    Scaffolded,

    /// <summary>Implementation is deliberately postponed.</summary>
    Deferred,

    /// <summary>The artifact records a possible future outcome.</summary>
    Aspirational,
}

/// <summary>A dimension on which compatibility is classified independently.</summary>
public enum CompatibilityDimension
{
    /// <summary>Domain or application behavior.</summary>
    SemanticBehavior,

    /// <summary>Ability to read existing wire representations.</summary>
    WireRead,

    /// <summary>Wire representations emitted by the writer.</summary>
    WireWrite,

    /// <summary>Source-level API compatibility.</summary>
    SourceApi,

    /// <summary>Binary ABI compatibility.</summary>
    BinaryAbi,

    /// <summary>Configuration compatibility.</summary>
    Configuration,

    /// <summary>Persisted artifact or data compatibility.</summary>
    PersistedArtifacts,

    /// <summary>Generated input or output compatibility.</summary>
    GeneratedArtifacts,

    /// <summary>Command-line surface compatibility.</summary>
    CommandLine,

    /// <summary>Host composition and activation compatibility.</summary>
    HostComposition,
}

/// <summary>A compatibility classification that fails closed when unknown.</summary>
public enum CompatibilityClassification
{
    /// <summary>No semantic or behavioral meaning changed.</summary>
    Editorial,

    /// <summary>The change is backward-compatible and additive.</summary>
    CompatibleAdditive,

    /// <summary>Compatibility depends on explicit conditions.</summary>
    ConditionallyCompatible,

    /// <summary>The change is incompatible.</summary>
    Breaking,

    /// <summary>Compatibility has not been established and must fail closed.</summary>
    Unknown,
}

/// <summary>An exact immutable reference to one semantic revision.</summary>
/// <param name="Identity">The stable semantic identity.</param>
/// <param name="Version">The independent semantic version.</param>
/// <param name="Digest">The digest of the exact referenced bytes.</param>
public sealed record ArtifactReference(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest);

/// <summary>An exact immutable reference constrained to a profile identity.</summary>
/// <param name="Identity">The profile identity.</param>
/// <param name="Version">The independent profile version.</param>
/// <param name="Digest">The digest of the exact profile bytes.</param>
public sealed record ProfileReference(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest Digest);

/// <summary>Identifies the schema contract governing an envelope.</summary>
/// <param name="SchemaId">The schema PKID.</param>
/// <param name="SchemaVersion">The full schema SemVer version.</param>
public sealed record ArtifactContract(
    ProgramKitIdentifier SchemaId,
    SemanticVersion SchemaVersion);

/// <summary>Identifies and classifies the enveloped artifact.</summary>
/// <param name="Id">The stable artifact identity.</param>
/// <param name="Kind">The canonical kebab-case artifact kind.</param>
/// <param name="Version">The artifact's independent version.</param>
/// <param name="OwnerId">The stable owner identity.</param>
/// <param name="Status">The truthful implementation status.</param>
/// <param name="Consumers">Explicit known consumers.</param>
public sealed record ArtifactIdentity(
    ProgramKitIdentifier Id,
    string Kind,
    SemanticVersion Version,
    ProgramKitIdentifier OwnerId,
    ArtifactStatus Status,
    ImmutableArray<ProgramKitIdentifier> Consumers);

/// <summary>Classifies one compatibility dimension.</summary>
/// <param name="Dimension">The independent compatibility dimension.</param>
/// <param name="Classification">The compatibility classification.</param>
/// <param name="Conditions">Explicit conditions for a conditional classification.</param>
public sealed record CompatibilityClaim(
    CompatibilityDimension Dimension,
    CompatibilityClassification Classification,
    ImmutableArray<string> Conditions);

/// <summary>Declares compatibility ranges, dimensions, and migration references.</summary>
/// <param name="Policy">The identity of the applied compatibility policy.</param>
/// <param name="Dimensions">Exactly one claim per classified dimension.</param>
/// <param name="ReaderRange">Versions whose representations can be read.</param>
/// <param name="WriterRange">Versions whose representations may be written.</param>
/// <param name="MigrationReferences">Explicit migration definitions.</param>
public sealed record ArtifactCompatibility(
    ProgramKitIdentifier Policy,
    ImmutableArray<CompatibilityClaim> Dimensions,
    SemanticVersionRange ReaderRange,
    SemanticVersionRange WriterRange,
    ImmutableArray<ArtifactReference> MigrationReferences);

/// <summary>Records supplied provenance without inventing ambient values.</summary>
/// <param name="SourceInputs">Exact source revisions in stable order.</param>
/// <param name="Producer">The producer identity.</param>
/// <param name="CorrelationId">A caller-supplied correlation identifier.</param>
public sealed record ArtifactProvenance(
    ImmutableArray<ArtifactReference> SourceInputs,
    ProgramKitIdentifier Producer,
    string CorrelationId);

/// <summary>Binds the exact serialization and canonicalization profiles.</summary>
/// <param name="SerializationProfileRef">The exact serialization profile.</param>
/// <param name="CanonicalizationProfileRef">The exact canonicalization profile.</param>
/// <param name="CanonicalMediaType">The canonical media type.</param>
public sealed record ArtifactRepresentation(
    ProfileReference SerializationProfileRef,
    ProfileReference CanonicalizationProfileRef,
    string CanonicalMediaType);

/// <summary>Records the digest of canonical envelope bytes.</summary>
/// <param name="Algorithm">The lowercase digest algorithm name.</param>
/// <param name="Digest">The digest calculated with the digest field omitted.</param>
public sealed record ArtifactIntegrity(
    string Algorithm,
    Sha256Digest Digest);

/// <summary>The universal immutable envelope for a durable Program Kit artifact.</summary>
/// <typeparam name="TDocument">The immutable typed document view.</typeparam>
/// <param name="Contract">The governing schema contract.</param>
/// <param name="Artifact">Artifact identity and status.</param>
/// <param name="Compatibility">Compatibility claims and migration references.</param>
/// <param name="Provenance">Exact supplied provenance.</param>
/// <param name="Representation">Exact representation profiles.</param>
/// <param name="Integrity">Canonical-byte integrity metadata.</param>
/// <param name="Document">The typed document.</param>
public sealed record ArtifactEnvelope<TDocument>(
    ArtifactContract Contract,
    ArtifactIdentity Artifact,
    ArtifactCompatibility Compatibility,
    ArtifactProvenance Provenance,
    ArtifactRepresentation Representation,
    ArtifactIntegrity Integrity,
    TDocument Document);
