namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Material-free reason for a provider change signal.</summary>
public enum SecretChangeKind
{
    /// <summary>No change kind was supplied.</summary>
    Unspecified,
    /// <summary>A different safe generation is available.</summary>
    GenerationChanged,
    /// <summary>The current capability is approaching expiry.</summary>
    Expiring,
    /// <summary>The current capability expired.</summary>
    Expired,
    /// <summary>The current capability was revoked.</summary>
    Revoked,
    /// <summary>Resolution was denied.</summary>
    Denied,
    /// <summary>The provider became unavailable.</summary>
    ProviderUnavailable,
    /// <summary>Resolution failed without a more specific safe reason.</summary>
    Failed,
}
