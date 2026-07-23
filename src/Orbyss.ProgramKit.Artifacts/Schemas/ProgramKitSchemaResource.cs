using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Schemas;

/// <summary>Describes one exact JSON Schema resource without imposing a schema-engine dependency.</summary>
/// <param name="SchemaReference">The exact schema identity, version, and source-byte digest.</param>
/// <param name="CanonicalUri">The canonical JSON Schema URI.</param>
/// <param name="ResourceName">The module-owned resource name.</param>
/// <param name="MediaType">The resource media type.</param>
/// <param name="OwnerId">The semantic owner of the raw schema contract.</param>
/// <param name="Status">The truthful implementation status of the schema.</param>
/// <param name="Consumers">Explicit consumers of the schema contract.</param>
/// <param name="Provenance">Producer and exact approved source inputs.</param>
/// <param name="Compatibility">Compatibility policy, ranges, dimensions, and migrations.</param>
/// <remarks>
/// <see cref="ArtifactReference.Digest"/> binds the raw schema source bytes.
/// It is not a claim that a canonical artifact envelope has been constructed;
/// canonical-envelope integrity remains W015 work.
/// </remarks>
public sealed record ProgramKitSchemaResource(
    ArtifactReference SchemaReference,
    Uri CanonicalUri,
    string ResourceName,
    string MediaType,
    ProgramKitIdentifier OwnerId,
    ArtifactStatus Status,
    ImmutableArray<ProgramKitIdentifier> Consumers,
    ArtifactProvenance Provenance,
    ArtifactCompatibility Compatibility);
