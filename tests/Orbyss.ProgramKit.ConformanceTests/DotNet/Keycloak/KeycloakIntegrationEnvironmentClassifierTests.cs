namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

using System.Text.Json;
using Orbyss.ProgramKit.ConformanceTests.Infrastructure;

[TestClass]
public sealed class KeycloakIntegrationEnvironmentClassifierTests
{
    [TestMethod]
    public void OnlyExactReviewedWindowsPreResourceFingerprintIsBlocked()
    {
        var reviewed = new KeycloakIntegrationFailure(
            "windows",
            "dcp-control-plane-startup",
            false,
            KeycloakIntegrationEnvironmentClassifier
                .WindowsDcpPreResourceFingerprint);

        Assert.IsTrue(
            KeycloakIntegrationEnvironmentClassifier
                .IsReviewedWindowsPreResourceBlocker(reviewed));
        Assert.IsFalse(
            KeycloakIntegrationEnvironmentClassifier
                .IsReviewedWindowsPreResourceBlocker(
                    reviewed with { OperatingSystem = "linux" }));
        Assert.IsFalse(
            KeycloakIntegrationEnvironmentClassifier
                .IsReviewedWindowsPreResourceBlocker(
                    reviewed with { ResourceCreated = true }));
        Assert.IsFalse(
            KeycloakIntegrationEnvironmentClassifier
                .IsReviewedWindowsPreResourceBlocker(
                    reviewed with
                    {
                        Fingerprint =
                            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
                    }));
    }

    [TestMethod]
    public void LinuxEnvironmentSelectionPinsExactToolingAndHumanStartedResult()
    {
        var root = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "extensions",
            "host-tooling-keycloak-tls-proof",
            "integration-environment",
            "linux-amd64");
        var dockerfile = File.ReadAllText(
            Path.Combine(root, "Dockerfile"));
        using var selection = JsonDocument.Parse(
            File.ReadAllText(Path.Combine(root, "selection.json")));

        Assert.Contains(
            "10.0.302-noble-amd64@sha256:3dae2f7699441af56216ff64d5c9b6dfce7cd7dc7f4f71d353d29662b10a384f",
            dockerfile);
        Assert.Contains(
            "v1.61.0-noble@sha256:72d804504ac23fcc83c770ca68c88c7e6b3e3462c9ad02f220197b95d46237db",
            dockerfile);
        Assert.Contains(
            "29.6.2-cli@sha256:feb2d49bd65f274b3e4b4620beabe2f4691e5287e496da9fbc9830ed5f780676",
            dockerfile);
        Assert.Contains(
            "/usr/local/libexec/docker/cli-plugins/docker-buildx",
            dockerfile);
        Assert.DoesNotContain("\nRUN ", dockerfile);
        Assert.AreEqual(
            "built-and-executed-passed",
            selection.RootElement.GetProperty("status").GetString());
        Assert.AreEqual(
            "sha256:75ab20d4a5281a6ffe8c42749089c950a51f2a753f0b9f8ccbbede0f51a126ed",
            selection.RootElement.GetProperty("dockerfileSha256").GetString());
        Assert.IsTrue(
            selection.RootElement.GetProperty("execution")
                .GetProperty("humanStarted")
                .GetBoolean());
        Assert.IsFalse(
            selection.RootElement.GetProperty("execution")
                .GetProperty("automaticRun")
                .GetBoolean());
        Assert.AreEqual(
            "sha256:acb4dacf6aeaa49be3be540455725184729a83d3f8ba995ff51ec3e6031726ee",
            selection.RootElement.GetProperty("execution")
                .GetProperty("derivedImageDigest")
                .GetString());
        Assert.AreEqual(
            "passed",
            selection.RootElement.GetProperty("execution")
                .GetProperty("result")
                .GetString());
        Assert.IsTrue(
            selection.RootElement.GetProperty("execution")
                .GetProperty("exactTaskRuntimeRemoved")
                .GetBoolean());
        Assert.AreEqual(
            "bounded-tls-pass-through",
            selection.RootElement.GetProperty("containerRuntime")
                .GetProperty("loopbackBridge")
                .GetString());
    }
}
