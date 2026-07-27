namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for a workload or managed-identity capability.</summary>
public interface IWorkloadIdentitySecretLease : ISecretResolutionLease
{
    /// <summary>Gets the provider-owned material-free capability.</summary>
    IWorkloadIdentityCapability Capability { get; }
}
