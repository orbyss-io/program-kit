namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Bounded assertion lease returned by an assertion-producing service.</summary>
public interface ISecretAssertionLease : IAsyncDisposable
{
    /// <summary>Gets protected assertion characters for immediate bounded consumption.</summary>
    ReadOnlyMemory<char> Value { get; }

    /// <summary>Gets the assertion expiry boundary.</summary>
    DateTimeOffset ExpiresAt { get; }
}
