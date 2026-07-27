namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Finite refresh and rotation signals a resolver can prove.</summary>
public enum SecretRotationCapability
{
    /// <summary>Rotation is not supported.</summary>
    Unsupported,
    /// <summary>Expiry metadata provides the only refresh boundary.</summary>
    LeaseExpiry,
    /// <summary>The provider produces metadata-only change signals.</summary>
    ChangeSignal,
    /// <summary>Both expiry boundaries and metadata-only change signals are supported.</summary>
    LeaseExpiryAndChangeSignal,
}
