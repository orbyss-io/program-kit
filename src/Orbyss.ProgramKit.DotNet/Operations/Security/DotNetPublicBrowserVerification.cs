namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Layered browser verification without durable authentication material.</summary>
public sealed record DotNetPublicBrowserVerification(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("playwrightRevision")] ArtifactReference PlaywrightRevision,
    [property: JsonPropertyName("engines")] ImmutableArray<DotNetBrowserEngine> Engines,
    [property: JsonPropertyName("automatedLocalExecutionHumanStarted")] bool AutomatedLocalExecutionHumanStarted,
    [property: JsonPropertyName("operatorAssistedRealProviderOptIn")] bool OperatorAssistedRealProviderOptIn,
    [property: JsonPropertyName("captureCredentials")] bool CaptureCredentials,
    [property: JsonPropertyName("persistAuthenticationState")] bool PersistAuthenticationState,
    [property: JsonPropertyName("persistTrace")] bool PersistTrace,
    [property: JsonPropertyName("redactedNonAuthoritativeEvidence")] bool RedactedNonAuthoritativeEvidence);
