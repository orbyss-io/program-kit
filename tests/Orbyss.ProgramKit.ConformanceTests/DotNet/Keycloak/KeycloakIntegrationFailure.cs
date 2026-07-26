namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

internal sealed record KeycloakIntegrationFailure(
    string OperatingSystem,
    string Phase,
    bool ResourceCreated,
    string Fingerprint);
