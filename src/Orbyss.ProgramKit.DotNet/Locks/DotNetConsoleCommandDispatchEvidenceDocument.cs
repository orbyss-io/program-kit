namespace Orbyss.ProgramKit.DotNet.Locks;

/// <summary>Deterministic generated evidence for the Console command-dispatch seam.</summary>
public sealed record DotNetConsoleCommandDispatchEvidenceDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("dispatchLockRevision")] ArtifactReference DispatchLockRevision,
    [property: JsonPropertyName("dispatcherContractPath")] string DispatcherContractPath,
    [property: JsonPropertyName("registrationMethod")] string RegistrationMethod,
    [property: JsonPropertyName("requiredDispatcherResolution")] bool RequiredDispatcherResolution,
    [property: JsonPropertyName("resolutionBeforeHostStart")] bool ResolutionBeforeHostStart,
    [property: JsonPropertyName("lifecycleOrder")] ImmutableArray<string> LifecycleOrder,
    [property: JsonPropertyName("parserPath")] string ParserPath,
    [property: JsonPropertyName("parserDigest")] Sha256Digest ParserDigest,
    [property: JsonPropertyName("parseResultPath")] string ParseResultPath,
    [property: JsonPropertyName("parseResultDigest")] Sha256Digest ParseResultDigest,
    [property: JsonPropertyName("exitCodePolicy")] string ExitCodePolicy);
