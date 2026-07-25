namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for an assertion-producing service.</summary>
public interface IAssertionServiceSecretLease : ISecretResolutionLease
{
    /// <summary>Gets the provider-owned assertion service.</summary>
    ISecretAssertionService Service { get; }
}
