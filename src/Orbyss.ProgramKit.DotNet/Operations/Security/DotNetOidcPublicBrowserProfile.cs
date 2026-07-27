namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact public-browser OIDC authorization-code-with-PKCE profile.</summary>
public sealed record DotNetOidcPublicBrowserProfile(
    [property: JsonPropertyName("profileRevision")] ArtifactReference ProfileRevision,
    [property: JsonPropertyName("targetAdapter")] DotNetPublicBrowserTargetAdapter TargetAdapter,
    [property: JsonPropertyName("authority")] Uri Authority,
    [property: JsonPropertyName("metadataAddress")] Uri MetadataAddress,
    [property: JsonPropertyName("clientId")] string ClientId,
    [property: JsonPropertyName("redirectUri")] Uri RedirectUri,
    [property: JsonPropertyName("postLogoutRedirectUri")] Uri PostLogoutRedirectUri,
    [property: JsonPropertyName("browserOrigin")] Uri BrowserOrigin,
    [property: JsonPropertyName("apiResource")] Uri ApiResource,
    [property: JsonPropertyName("corsPolicyName")] string CorsPolicyName,
    [property: JsonPropertyName("corsAllowedOrigins")] ImmutableArray<Uri> CorsAllowedOrigins,
    [property: JsonPropertyName("corsAllowedMethods")] ImmutableArray<string> CorsAllowedMethods,
    [property: JsonPropertyName("scopes")] ImmutableArray<string> Scopes,
    [property: JsonPropertyName("tokenStorage")] DotNetPublicBrowserTokenStorage TokenStorage,
    [property: JsonPropertyName("refreshDisposition")] DotNetPublicBrowserRefreshDisposition RefreshDisposition,
    [property: JsonPropertyName("threatModelAcceptanceRevision")] ArtifactReference ThreatModelAcceptanceRevision,
    [property: JsonPropertyName("humanAcceptedBrowserHeldTokens")] bool HumanAcceptedBrowserHeldTokens,
    [property: JsonPropertyName("confidentialBffPreferredForSensitiveApplications")] bool ConfidentialBffPreferredForSensitiveApplications,
    [property: JsonPropertyName("requireHttps")] bool RequireHttps,
    [property: JsonPropertyName("usePkce")] bool UsePkce,
    [property: JsonPropertyName("requireState")] bool RequireState,
    [property: JsonPropertyName("requireNonce")] bool RequireNonce,
    [property: JsonPropertyName("clientSecretAbsent")] bool ClientSecretAbsent,
    [property: JsonPropertyName("logoutEnabled")] bool LogoutEnabled,
    [property: JsonPropertyName("verification")] DotNetPublicBrowserVerification Verification);
