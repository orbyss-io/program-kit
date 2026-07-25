using System.Security.Cryptography.X509Certificates;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Lease for a certificate capability.</summary>
public interface ICertificateSecretLease : ISecretResolutionLease
{
    /// <summary>Gets the certificate owned by this lease.</summary>
    X509Certificate2 Certificate { get; }
}
