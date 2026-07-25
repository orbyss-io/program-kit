namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Explicit consumer-owned reaction to secret lifecycle change.</summary>
public enum SecretConsumerReaction
{
    /// <summary>Replace the capability in place.</summary>
    HotReplacement,
    /// <summary>Recreate the dependent client.</summary>
    ClientRecreation,
    /// <summary>Reconnect the dependent client or transport.</summary>
    Reconnect,
    /// <summary>Recycle the dependent resource.</summary>
    ResourceRecycle,
    /// <summary>Request an orderly host restart.</summary>
    HostRestartRequest,
    /// <summary>Require explicit manual handling.</summary>
    Manual,
    /// <summary>The consumer cannot react to rotation.</summary>
    Unsupported,
}
