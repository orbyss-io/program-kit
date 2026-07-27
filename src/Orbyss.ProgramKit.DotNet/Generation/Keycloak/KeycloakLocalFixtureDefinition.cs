namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>
/// Exact provider-specialized input for one disposable Keycloak/Aspire proof.
/// It owns no production identity, authorization, or provisioning meaning.
/// </summary>
public sealed record KeycloakLocalFixtureDefinition(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    string RealmName,
    Uri Authority,
    Uri MetadataAddress,
    string ApiAudience,
    string ApiScope,
    string PublicClientId,
    Uri PublicRedirectUri,
    Uri PublicPostLogoutRedirectUri,
    Uri PublicBrowserOrigin,
    string ConfidentialClientId,
    Uri ConfidentialRedirectUri,
    string ServiceClientId,
    string TokenExchangeClientId,
    string TestPrincipalName,
    KeycloakLocalFixtureSecretReferences Secrets);
