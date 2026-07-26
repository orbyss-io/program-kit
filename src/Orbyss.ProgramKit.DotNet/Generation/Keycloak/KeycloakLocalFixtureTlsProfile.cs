namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>
/// Exact runtime-only TLS profile for the disposable Keycloak fixture.
/// The profile contains no certificate, key, random value, or runtime path.
/// </summary>
public sealed record KeycloakLocalFixtureTlsProfile(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    string ServerHostName,
    int ProviderHttpsTargetPort,
    string CertificateAlgorithm,
    int CertificateAuthorityKeySize,
    int ServerKeySize,
    int NotBeforeSkewMinutes,
    int CertificateAuthorityValidityHours,
    int ServerCertificateValidityHours,
    string ServerExtendedKeyUsageOid,
    string RuntimeRootEnvironmentVariable,
    string ContainerCertificatePath,
    string ContainerPrivateKeyPath,
    string DotNetTrustMode,
    string ChromiumTrustMode);
