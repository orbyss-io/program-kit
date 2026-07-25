namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for configuration-shaped byte material.</summary>
public interface IConfigurationBytesSecretLease : ISecretResolutionLease
{
    /// <summary>Gets protected bytes for immediate bounded consumption.</summary>
    ReadOnlyMemory<byte> Value { get; }
}
