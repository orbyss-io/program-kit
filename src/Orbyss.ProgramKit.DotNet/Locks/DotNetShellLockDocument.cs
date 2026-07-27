using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Deterministic lock for one reviewed shell document and its selected hosts.</summary>
public sealed record DotNetShellLockDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("shellRevision")] ArtifactReference ShellRevision,
    [property: JsonPropertyName("inputVersionMapRevision")] ArtifactReference InputVersionMapRevision,
    [property: JsonPropertyName("inputVersionSelectionRevision")] ArtifactReference InputVersionSelectionRevision,
    [property: JsonPropertyName("hostLocks")] ImmutableArray<DotNetHostLock> HostLocks);
