namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Deterministic exact-input lock for generated Console command dispatch.</summary>
public sealed record DotNetConsoleCommandDispatchLockDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("hostRevision")] ArtifactReference HostRevision,
    [property: JsonPropertyName("shellRevision")] ArtifactReference ShellRevision,
    [property: JsonPropertyName("openConsoleDocumentRevision")] ArtifactReference OpenConsoleDocumentRevision,
    [property: JsonPropertyName("hostGeneratorRevision")] ArtifactReference HostGeneratorRevision,
    [property: JsonPropertyName("dispatcherContractRevision")] ArtifactReference DispatcherContractRevision);
