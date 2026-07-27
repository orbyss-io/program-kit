namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

/// <summary>
/// Bounded classification for the one reviewed Windows pre-resource DCP
/// fingerprint. It performs no discovery, remediation, or environment change.
/// </summary>
internal static class KeycloakIntegrationEnvironmentClassifier
{
    internal const string WindowsDcpPreResourceFingerprint =
        "sha256:5312155b739bcb05f204f1b2bd71d724f5c24dc941ebfa7efd932aba2bd90912";

    internal static bool IsReviewedWindowsPreResourceBlocker(
        KeycloakIntegrationFailure failure) =>
        failure.OperatingSystem == "windows" &&
        failure.Phase == "dcp-control-plane-startup" &&
        failure.ResourceCreated is false &&
        failure.Fingerprint == WindowsDcpPreResourceFingerprint;
}
