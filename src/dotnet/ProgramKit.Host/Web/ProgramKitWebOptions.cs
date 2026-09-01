namespace ProgramKit.Host.Web;

/// <summary>Defines the validated runtime settings shared by the secure web profiles.</summary>
internal sealed class ProgramKitWebOptions
{
    /// <summary>Gets the configuration section containing secure web settings.</summary>
    public const string SectionName = "ProgramKit:Web";

    /// <summary>Gets or sets the selected secure web boundary profile.</summary>
    public ProgramKitWebProfile Profile { get; set; }

    /// <summary>Gets or sets the OIDC issuer authority.</summary>
    public string Authority { get; set; } = string.Empty;

    /// <summary>Gets or sets the registered OAuth client identifier.</summary>
    public string ClientId { get; set; } = string.Empty;

    /// <summary>Gets or sets the confidential BFF client secret.</summary>
    public string ClientSecret { get; set; } = string.Empty;

    /// <summary>Gets or sets the protected API audience.</summary>
    public string Audience { get; set; } = string.Empty;

    /// <summary>Gets or sets the scopes requested during interactive authentication.</summary>
    public string[] Scopes { get; set; } = ["openid", "profile", "offline_access", "program-kit-api"];

    /// <summary>Gets or sets the provider claim containing normalized application roles.</summary>
    public string RoleClaim { get; set; } = "roles";

    /// <summary>Gets or sets the exact origins permitted by the direct SPA profile.</summary>
    public string[] AllowedOrigins { get; set; } = [];

    /// <summary>Gets or sets the local OIDC authorization callback path.</summary>
    public string CallbackPath { get; set; } = "/signin-oidc";

    /// <summary>Gets or sets the local callback path used after provider logout.</summary>
    public string SignedOutCallbackPath { get; set; } = "/signout-callback-oidc";

    /// <summary>Gets or sets the path receiving provider-initiated logout notifications.</summary>
    public string RemoteSignOutPath { get; set; } = "/signout-oidc";

    /// <summary>Gets or sets the interactive access-denied path.</summary>
    public string AccessDeniedPath { get; set; } = "/bff/access-denied";

    /// <summary>Gets or sets the host-only encrypted session cookie name.</summary>
    public string CookieName { get; set; } = "__Host-program-kit-session";

    /// <summary>Gets or sets the discovery and JWKS readiness budget in seconds.</summary>
    public int DiscoveryTimeoutSeconds { get; set; } = 3;

    /// <summary>Gets or sets the maximum duration of an interactive remote authentication operation.</summary>
    public int RemoteAuthenticationTimeoutSeconds { get; set; } = 10;

    /// <summary>Gets or sets the sliding server session idle lifetime in minutes.</summary>
    public int SessionIdleMinutes { get; set; } = 30;

    /// <summary>Gets or sets the non-extendable server session lifetime in minutes.</summary>
    public int SessionAbsoluteMinutes { get; set; } = 480;

    /// <summary>Gets or sets whether loopback/container HTTP is accepted during local development.</summary>
    public bool AllowHttpForLocalDevelopment { get; set; }

    /// <summary>Gets or sets the deterministic application fallback locale.</summary>
    public string DefaultLocale { get; set; } = "en";

    /// <summary>Gets or sets the application locales accepted by request localization.</summary>
    public string[] SupportedLocales { get; set; } = ["en"];
}
