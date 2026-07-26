namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact confidential server-side OIDC authorization-code-with-PKCE profile.</summary>
public sealed record DotNetOidcConfidentialInteractiveProfile(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("scheme")] string Scheme,
    [property: JsonPropertyName("cookieScheme")] string CookieScheme,
    [property: JsonPropertyName("authority")] Uri Authority,
    [property: JsonPropertyName("metadataAddress")] Uri MetadataAddress,
    [property: JsonPropertyName("clientId")] string ClientId,
    [property: JsonPropertyName("clientAuthentication")] DotNetOidcClientAuthentication ClientAuthentication,
    [property: JsonPropertyName("callbackPath")] string CallbackPath,
    [property: JsonPropertyName("signedOutCallbackPath")] string SignedOutCallbackPath,
    [property: JsonPropertyName("remoteSignOutPath")] string RemoteSignOutPath,
    [property: JsonPropertyName("scopes")] ImmutableArray<string> Scopes,
    [property: JsonPropertyName("allowedIdTokenAlgorithms")] ImmutableArray<string> AllowedIdTokenAlgorithms,
    [property: JsonPropertyName("pushedAuthorization")] DotNetOidcPushedAuthorizationBehavior PushedAuthorization,
    [property: JsonPropertyName("claimMapping")] DotNetTransportClaimMapping ClaimMapping,
    [property: JsonPropertyName("cookie")] DotNetCookieSecurityProfile Cookie,
    [property: JsonPropertyName("correlationCookie")] DotNetCookieSecurityProfile CorrelationCookie,
    [property: JsonPropertyName("nonceCookie")] DotNetCookieSecurityProfile NonceCookie,
    [property: JsonPropertyName("remoteAuthenticationTimeoutSeconds")] int RemoteAuthenticationTimeoutSeconds,
    [property: JsonPropertyName("requireHttpsMetadata")] bool RequireHttpsMetadata,
    [property: JsonPropertyName("usePkce")] bool UsePkce,
    [property: JsonPropertyName("requireNonce")] bool RequireNonce,
    [property: JsonPropertyName("requireState")] bool RequireState,
    [property: JsonPropertyName("saveTokens")] bool SaveTokens,
    [property: JsonPropertyName("getClaimsFromUserInfoEndpoint")] bool GetClaimsFromUserInfoEndpoint);
