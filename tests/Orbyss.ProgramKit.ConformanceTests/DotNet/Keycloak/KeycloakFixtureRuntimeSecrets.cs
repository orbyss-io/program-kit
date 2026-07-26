using System.Collections.Immutable;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

internal sealed record KeycloakFixtureRuntimeSecrets(
    string AdminPassword,
    string TestPrincipalPassword,
    string ConfidentialClientSecret,
    string ServiceClientSecret,
    string TokenExchangeClientSecret)
{
    internal ImmutableArray<string> All =>
    [
        AdminPassword,
        TestPrincipalPassword,
        ConfidentialClientSecret,
        ServiceClientSecret,
        TokenExchangeClientSecret,
    ];
}
