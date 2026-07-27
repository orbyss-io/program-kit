namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Material-free resolution and lifecycle status.</summary>
public enum SecretResolutionStatus
{
    /// <summary>No status was supplied.</summary>
    Unspecified,
    /// <summary>The selected capability is available.</summary>
    Available,
    /// <summary>Resolution was denied.</summary>
    Denied,
    /// <summary>The provider is unavailable.</summary>
    ProviderUnavailable,
    /// <summary>The capability expired.</summary>
    Expired,
    /// <summary>The capability was revoked.</summary>
    Revoked,
    /// <summary>Resolution failed without a more specific safe status.</summary>
    Failed,
}
