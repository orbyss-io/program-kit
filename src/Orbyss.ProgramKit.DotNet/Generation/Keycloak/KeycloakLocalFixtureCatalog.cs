namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>Exact reviewed provider and integration selection for W100.</summary>
public static class KeycloakLocalFixtureCatalog
{
    /// <summary>Exact preview Aspire hosting integration package version.</summary>
    public const string AspireKeycloakPackageVersion =
        "13.4.6-preview.1.26319.6";

    /// <summary>Exact Aspire hosting integration package archive digest.</summary>
    public const string AspireKeycloakPackageSha256 =
        "bdc92e34c141dc18f9ee0b523a48927650298fd23991137d320e7afc714f58c2";

    /// <summary>Exact Aspire hosting integration assembly digest.</summary>
    public const string AspireKeycloakAssemblySha256 =
        "3ad7f4f243ec894d489ba2b5b286856663a6dfec1f50c10068eae08815e58521";

    /// <summary>Exact selected Keycloak release.</summary>
    public const string KeycloakVersion = "26.7.0";

    /// <summary>Exact selected Keycloak multi-platform image digest.</summary>
    public const string KeycloakImageSha256 =
        "0f198be292568439d700cdbfb893e69a6009bb43a94a06a945b1d3d506c76b13";

    /// <summary>Exact selected Keycloak upstream source revision.</summary>
    public const string KeycloakSourceCommit =
        "6c73e3027811d9c7b22683edd825e839272e9547";

    /// <summary>Exact runtime-only TLS profile used by the fixture.</summary>
    public static KeycloakLocalFixtureTlsProfile TlsProfile { get; } =
        new(
            new ProgramKitIdentifier(
                "pkid:profile:program-kit:keycloak-fixture-tls"),
            new SemanticVersion("1.0.0"),
            "localhost",
            8443,
            "RSA-SHA256",
            3072,
            3072,
            5,
            24,
            8,
            "1.3.6.1.5.5.7.3.1",
            "PROGRAM_KIT_KEYCLOAK_RUNTIME_ROOT",
            "/opt/keycloak/conf/program-kit-server-certificate.pem",
            "/opt/keycloak/conf/program-kit-server-private-key.pem",
            "dotnet-custom-root-trust",
            "chromium-server-spki-list");
}
