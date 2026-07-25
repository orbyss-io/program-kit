namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for an opaque credential object or handle.</summary>
public interface ICredentialHandleSecretLease : ISecretResolutionLease
{
    /// <summary>Gets the provider-owned credential handle.</summary>
    ISecretCredentialHandle Handle { get; }
}
