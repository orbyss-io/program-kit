namespace Application.Core;

/// <summary>Preserves the exact authenticated issuer and subject without provider-specific roles.</summary>
public sealed record OwnedActor(string Issuer, string Subject);
