using ProgramKit.Authentication;

namespace ProgramKit.Authentication.SpaPkce;

/// <summary>Identifies the direct SPA-PKCE authentication profile.</summary>
internal sealed class SpaPkceProfileMarker : IProgramKitAuthenticationProfile
{
    /// <inheritdoc />
    public string Name => "spa-pkce-v1";
}
