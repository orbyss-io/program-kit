namespace GeneratedPublicBrowser.Operations;

/// <summary>Conformance-only access to the generated-equivalent protocol vectors.</summary>
public static class PublicBrowserProtocolProbe
{
    /// <summary>Creates the RFC 7636 S256 challenge for a verifier.</summary>
    public static string CreateS256Challenge(string verifier) =>
        PublicBrowserProtocolVectors.CreateS256Challenge(verifier);

    /// <summary>Checks the exact callback, issuer, state, and nonce boundaries.</summary>
    public static bool IsSafeAuthorizationResponse(
        Uri callback,
        Uri issuer,
        string expectedState,
        string actualState,
        string expectedNonce,
        string actualNonce) =>
        PublicBrowserProtocolVectors.IsSafeAuthorizationResponse(
            callback,
            issuer,
            expectedState,
            actualState,
            expectedNonce,
            actualNonce);

    /// <summary>Checks the exact post-logout callback.</summary>
    public static bool IsSafeLogoutCallback(Uri callback) =>
        PublicBrowserProtocolVectors.IsSafeLogoutCallback(callback);

    /// <summary>Checks whether a target belongs to the configured API resource.</summary>
    public static bool IsAllowedApiTarget(Uri target) =>
        PublicBrowserProtocolVectors.IsAllowedApiTarget(target);

    /// <summary>Checks the selected bearer access-token type.</summary>
    public static bool IsAccessTokenKind(string tokenType, string? jwtType) =>
        PublicBrowserProtocolVectors.IsAccessTokenKind(tokenType, jwtType);

    /// <summary>Gets whether the selected initial adapter expects refresh tokens.</summary>
    public static bool RefreshTokenExpected =>
        PublicBrowserProtocolVectors.RefreshTokenExpected;
}
