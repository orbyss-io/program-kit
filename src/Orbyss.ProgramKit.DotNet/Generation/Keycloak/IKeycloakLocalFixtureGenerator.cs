namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>
/// Generates a disposable provider fixture without resolving secrets or
/// starting Aspire, Keycloak, a browser, or another external resource.
/// </summary>
public interface IKeycloakLocalFixtureGenerator
{
    /// <summary>Validates and renders one complete local-test fixture.</summary>
    KeycloakLocalFixtureGenerationResult Generate(
        KeycloakLocalFixtureDefinition definition);
}
