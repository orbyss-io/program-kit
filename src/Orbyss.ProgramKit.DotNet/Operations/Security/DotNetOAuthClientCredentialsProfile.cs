namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact OAuth 2.0 client-credentials service-client profile.</summary>
public sealed record DotNetOAuthClientCredentialsProfile(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("clientName")] string ClientName,
    [property: JsonPropertyName("metadataAddress")] Uri MetadataAddress,
    [property: JsonPropertyName("tokenEndpoint")] Uri TokenEndpoint,
    [property: JsonPropertyName("clientId")] string ClientId,
    [property: JsonPropertyName("authentication")] DotNetOAuthClientAuthentication Authentication,
    [property: JsonPropertyName("resource")] Uri Resource,
    [property: JsonPropertyName("audience")] string Audience,
    [property: JsonPropertyName("scopes")] ImmutableArray<string> Scopes,
    [property: JsonPropertyName("expectedIssuedTokenType")] DotNetOAuthTokenType ExpectedIssuedTokenType,
    [property: JsonPropertyName("requestedLifetimeSeconds")] int RequestedLifetimeSeconds,
    [property: JsonPropertyName("requestTimeoutSeconds")] int RequestTimeoutSeconds,
    [property: JsonPropertyName("cache")] DotNetOAuthCachePolicy Cache,
    [property: JsonPropertyName("cancellationRequired")] bool CancellationRequired,
    [property: JsonPropertyName("failClosedOnOutage")] bool FailClosedOnOutage,
    [property: JsonPropertyName("redactTokenMaterial")] bool RedactTokenMaterial,
    [property: JsonPropertyName("automaticRetry")] bool AutomaticRetry,
    [property: JsonPropertyName("retrieveAmbientCurrentUserToken")] bool RetrieveAmbientCurrentUserToken);
