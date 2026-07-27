using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>
/// Classified references for values supplied only when the disposable fixture
/// is explicitly started. No referenced value is a generator input.
/// </summary>
public sealed record KeycloakLocalFixtureSecretReferences(
    SecretReferenceDescriptor AdminPassword,
    SecretReferenceDescriptor TestPrincipalPassword,
    SecretReferenceDescriptor ConfidentialClientSecret,
    SecretReferenceDescriptor ServiceClientSecret,
    SecretReferenceDescriptor TokenExchangeClientSecret);
