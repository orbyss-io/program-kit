namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Material-free work item queued for one consumer-owned reaction.</summary>
public sealed record SecretReactionRequest(
    SecretChangeSignal Signal,
    SecretConsumerReaction Reaction);
