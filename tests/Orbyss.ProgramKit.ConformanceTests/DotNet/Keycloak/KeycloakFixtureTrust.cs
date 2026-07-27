namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

internal sealed record KeycloakFixtureTrust(
    string AuthorityCertificatePath,
    string ChromiumSpkiList);
