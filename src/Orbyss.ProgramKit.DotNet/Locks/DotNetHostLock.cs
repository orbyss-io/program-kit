using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Targeting;

namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Complete deterministic generation lock for one selected host.</summary>
public sealed record DotNetHostLock(
    [property: JsonPropertyName("hostIdentity")] ProgramKitIdentifier HostIdentity,
    [property: JsonPropertyName("hostVersion")] SemanticVersion HostVersion,
    [property: JsonPropertyName("kind")] DotNetHostKind Kind,
    [property: JsonPropertyName("target")] DotNetTargetLock Target,
    [property: JsonPropertyName("cShellsAbiVersion")] SemanticVersion CShellsAbiVersion,
    [property: JsonPropertyName("featureActivationIdentities")] ImmutableArray<ProgramKitIdentifier> FeatureActivationIdentities,
    [property: JsonPropertyName("contractRevisions")] ImmutableArray<ArtifactReference> ContractRevisions,
    [property: JsonPropertyName("schemaRevisions")] ImmutableArray<ArtifactReference> SchemaRevisions,
    [property: JsonPropertyName("generatorRevisions")] ImmutableArray<ArtifactReference> GeneratorRevisions,
    [property: JsonPropertyName("serializationRevisions")] ImmutableArray<ArtifactReference> SerializationRevisions,
    [property: JsonPropertyName("inputVersionMapRevision")] ArtifactReference InputVersionMapRevision,
    [property: JsonPropertyName("inputVersionSelectionRevision")] ArtifactReference InputVersionSelectionRevision,
    [property: JsonPropertyName("packages")] ImmutableArray<DotNetPackageLock> Packages,
    [property: JsonPropertyName("packageLockDigest")] Sha256Digest PackageLockDigest);
