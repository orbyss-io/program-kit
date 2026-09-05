using ProgramKit.Authentication;

namespace ProgramKit.Authentication.BffCookie;

/// <summary>Identifies the BFF-cookie authentication profile.</summary>
internal sealed class BffCookieProfileMarker : IProgramKitAuthenticationProfile
{
    /// <inheritdoc />
    public string Name => "bff-cookie-v1";
}
