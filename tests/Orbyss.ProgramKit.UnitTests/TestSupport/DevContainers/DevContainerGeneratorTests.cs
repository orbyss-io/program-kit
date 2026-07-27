using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.DevContainers.Composition;
using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;
using Orbyss.ProgramKit.DevContainers.Contracts.Definitions;
using Orbyss.ProgramKit.DevContainers.Contracts.Diagnostics;
using Orbyss.ProgramKit.DevContainers.Contracts.Features;
using Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;
using Orbyss.ProgramKit.DevContainers.Contracts.Mounts;
using Orbyss.ProgramKit.DevContainers.Contracts.Ports;
using Orbyss.ProgramKit.DevContainers.Contracts.Profiles;
using Orbyss.ProgramKit.DevContainers.Operations.Generation;

namespace Orbyss.ProgramKit.UnitTests.TestSupport.DevContainers;

[TestClass]
public sealed class DevContainerGeneratorTests
{
    /// <summary>Gets the active test context and cancellation token.</summary>
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void SameImageDefinitionProducesIdenticalBytesAndTreeDigest()
    {
        var generator = DevContainerComposition.CreateGenerator();
        var definition = Definition(ImageProfile());

        var first = generator.Generate(definition, TestContext.CancellationToken);
        var second = generator.Generate(definition, TestContext.CancellationToken);

        Assert.AreEqual(first.OutputTreeDigest, second.OutputTreeDigest);
        Assert.AreSequenceEqual(
            first.Files.Select(static file => file.RelativePath).ToArray(),
            second.Files.Select(static file => file.RelativePath).ToArray());
        for (var index = 0; index < first.Files.Length; index++)
        {
            Assert.AreSequenceEqual(
                first.Files[index].Content.ToArray(),
                second.Files[index].Content.ToArray());
        }
    }

    [TestMethod]
    public void DockerfileBytesRemainExactAndComposeExistsOnlyForComposeProfile()
    {
        var generator = DevContainerComposition.CreateGenerator();
        var dockerfile = Opaque(
            ".devcontainer/Dockerfile",
            "FROM example.invalid/base@sha256:" + new string('c', 64) + "\n");
        var direct = generator.Generate(
            Definition(new DevContainerDockerfileProfile(dockerfile, "..")),
            TestContext.CancellationToken);
        var compose = generator.Generate(
            Definition(new DevContainerComposeProfile(
                "workspace",
                "/workspaces/example",
                null,
                dockerfile,
                "..")),
            TestContext.CancellationToken);

        Assert.AreSequenceEqual(
            dockerfile.Content.ToArray(),
            direct.Files.Single(
                static file => file.RelativePath == ".devcontainer/Dockerfile").Content.ToArray());
        Assert.IsFalse(direct.Files.Any(
            static file => file.RelativePath.EndsWith("compose.yaml", StringComparison.Ordinal)));
        Assert.IsTrue(compose.Files.Any(
            static file => file.RelativePath == ".devcontainer/compose.yaml"));
        Assert.Contains(
            "single-primary-development-service",
            Text(compose, ".devcontainer/devcontainer.lock.json"));
    }

    [TestMethod]
    public void FeatureArtifactDigestParticipatesInProvenanceAndTreeDigest()
    {
        var generator = DevContainerComposition.CreateGenerator();
        var definition = Definition(ImageProfile());
        var changed = definition with
        {
            Features =
            [
                definition.Features[0] with
                {
                    ExpectedDigest = Digest(Encoding.UTF8.GetBytes("changed-feature")),
                },
            ],
        };

        var first = generator.Generate(definition, TestContext.CancellationToken);
        var second = generator.Generate(changed, TestContext.CancellationToken);

        Assert.AreNotEqual(first.OutputTreeDigest, second.OutputTreeDigest);
        Assert.AreEqual(
            Text(first, ".devcontainer/devcontainer.json"),
            Text(second, ".devcontainer/devcontainer.json"));
        Assert.AreNotEqual(
            Text(first, ".devcontainer/devcontainer.lock.json"),
            Text(second, ".devcontainer/devcontainer.lock.json"));
    }

    [TestMethod]
    public void UnsafePathAndUnpinnedFeatureFailWithStableDiagnostics()
    {
        var generator = DevContainerComposition.CreateGenerator();
        var definition = Definition(ImageProfile());
        var unsafePath = definition with
        {
            Mounts = [new DevContainerMount(DevContainerMountKind.Bind, "../../host", "/work")],
        };
        var unpinnedFeature = definition with
        {
            Features =
            [
                definition.Features[0] with
                {
                    Reference = "ghcr.io/devcontainers/features/dotnet:latest",
                },
            ],
        };

        var pathException = Assert.ThrowsExactly<DevContainerGenerationException>(
            () => generator.Generate(unsafePath, TestContext.CancellationToken));
        var featureException = Assert.ThrowsExactly<DevContainerGenerationException>(
            () => generator.Generate(
                unpinnedFeature,
                TestContext.CancellationToken));

        Assert.AreEqual(DevContainerDiagnosticIds.UnsafePath, pathException.DiagnosticId);
        Assert.AreEqual(
            DevContainerDiagnosticIds.InvalidFeature,
            featureException.DiagnosticId);
    }

    [TestMethod]
    public void ApparentSecretInOpaqueScriptFailsClosed()
    {
        var generator = DevContainerComposition.CreateGenerator();
        var definition = Definition(ImageProfile());
        var secretScript = Opaque(
            ".devcontainer/scripts/setup.sh",
            "#!/bin/sh\npassword=do-not-store-this\n");
        var unsafeDefinition = definition with { Scripts = [secretScript] };

        var exception = Assert.ThrowsExactly<DevContainerGenerationException>(
            () => generator.Generate(
                unsafeDefinition,
                TestContext.CancellationToken));

        Assert.AreEqual(
            DevContainerDiagnosticIds.UnsafeOpaqueContent,
            exception.DiagnosticId);
    }

    [TestMethod]
    public void CancellationStopsBeforeGeneration()
    {
        var generator = DevContainerComposition.CreateGenerator();
        using CancellationTokenSource cancellation = new();
        cancellation.Cancel();

        Assert.ThrowsExactly<OperationCanceledException>(
            () => generator.Generate(Definition(ImageProfile()), cancellation.Token));
    }

    internal static DevContainerDefinition Definition(DevContainerProfile profile)
    {
        var script = Opaque(
            ".devcontainer/scripts/setup.sh",
            "#!/bin/sh\nset -eu\ndotnet --info\n");
        return new DevContainerDefinition(
            new ProgramKitIdentifier("pkid:dev-container:fixture:example"),
            new SemanticVersion("1.0.0"),
            "Example development container",
            profile,
            [
                new DevContainerFeature(
                    "ghcr.io/devcontainers/features/dotnet:2.7.1",
                    Digest(Encoding.UTF8.GetBytes("feature-artifact")),
                    ImmutableSortedDictionary<string, string>.Empty.Add("version", "10.0.302")),
            ],
            [
                new DevContainerMount(
                    DevContainerMountKind.Volume,
                    "example-cache",
                    "/home/vscode/.cache"),
            ],
            [new DevContainerForwardedPort(8080, "Example API")],
            "vscode",
            "vscode",
            [
                new DevContainerLifecycleCommand(
                    DevContainerLifecycleStage.PostCreate,
                    null,
                    ["/bin/sh", ".devcontainer/scripts/setup.sh"]),
            ],
            [script]);
    }

    internal static DevContainerImageProfile ImageProfile() =>
        new(string.Concat(
            "mcr.microsoft.com/devcontainers/dotnet@sha256:",
            new string('a', 64)));

    internal static DevContainerOpaqueArtifact Opaque(string path, string content)
    {
        var bytes = Encoding.UTF8.GetBytes(content);
        return new DevContainerOpaqueArtifact(
            path,
            ImmutableArray.Create(bytes),
            Digest(bytes),
            true);
    }

    private static Sha256Digest Digest(ReadOnlySpan<byte> bytes) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(bytes))));

    private static string Text(DevContainerGenerationResult result, string path) =>
        Encoding.UTF8.GetString(
            result.Files.Single(file => file.RelativePath == path).Content.AsSpan());
}
