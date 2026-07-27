namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Outcome of one consumer-owned lifecycle reaction.</summary>
public enum SecretReactionStatus
{
    /// <summary>The reaction has not completed.</summary>
    Pending,
    /// <summary>The declared reaction completed successfully.</summary>
    Succeeded,
    /// <summary>The declared reaction ran and failed.</summary>
    Failed,
    /// <summary>The bounded reaction queue rejected the work.</summary>
    Rejected,
}
