namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for a mounted-file handle.</summary>
public interface IMountedFileSecretLease : ISecretResolutionLease
{
    /// <summary>Gets the opaque mounted-file handle.</summary>
    ISecretMountedFileHandle Handle { get; }
}
