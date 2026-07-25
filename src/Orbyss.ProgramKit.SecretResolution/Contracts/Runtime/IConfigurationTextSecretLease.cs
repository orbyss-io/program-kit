namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for configuration-shaped character material.</summary>
public interface IConfigurationTextSecretLease : ISecretResolutionLease
{
    /// <summary>Gets protected characters for immediate bounded consumption.</summary>
    ReadOnlyMemory<char> Value { get; }
}
