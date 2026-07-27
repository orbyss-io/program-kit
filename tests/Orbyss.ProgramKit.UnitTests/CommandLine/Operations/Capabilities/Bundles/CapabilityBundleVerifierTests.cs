using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Bundles;

[TestClass]
public sealed class CapabilityBundleVerifierTests
{
    private static readonly string[] CapabilityIds =
    [
        "develop-software",
        "design-software",
        "implement-software-plan",
    ];
    private static readonly string[] Providers =
    [
        "claude",
        "codex",
    ];

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task VerifiesExactDefinitionsAndSeparatelyListedAdapters()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(root);
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            await sut.VerifyAsync(bundle, TestContext.CancellationToken);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsBundleMissingRegisteredProviderAdapters()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                adapterProviders: ["codex"]);
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI007", exception.DiagnosticId);
            Assert.Contains("provider-adapter", exception.Message);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsTamperedCapabilityBytes()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                tamperedCapabilityId: "design-software");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual(CommandExitCode.ConformanceFailure, exception.ExitCode);
            Assert.AreEqual("PKCLI007", exception.DiagnosticId);
            Assert.Contains("does not match", exception.Message);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsCopiedIndexBecauseBundleBytesDoNotRegisterCapabilities()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                extraPath:
                    "contentFiles/any/any/.agent-capabilities/capabilities/INDEX.md");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.Contains("allow-list", exception.Message);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsRepositoryOnlyPublishCapabilityFromDistribution()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                extraPath:
                    "contentFiles/any/any/.agent-capabilities/capabilities/publish-dotnet-application-locally/CAPABILITY.md");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.Contains("allow-list", exception.Message);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsUndeclaredContentFile()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                extraPath:
                    "contentFiles/any/any/.program-kit/undeclared.json");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.Contains("undeclared content", exception.Message);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsCompiledAsset()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                extraPath: "lib/net10.0/Injected.dll");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.Contains("executable or build asset", exception.Message);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsMalformedManifestWithStableBundleDiagnostic()
    {
        var root = CreateRoot();
        try
        {
            var bundle = Path.Combine(root, "capabilities.nupkg");
            using (var archive = ZipFile.Open(
                       bundle,
                       ZipArchiveMode.Create))
            {
                WriteEntry(
                    archive,
                    "contentFiles/any/any/.agent-capabilities/capability-bundle-manifest.json",
                    Encoding.UTF8.GetBytes("{"));
            }

            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI007", exception.DiagnosticId);
            Assert.AreEqual("/bundle", exception.Path);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static string CreateRoot()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-capability-bundle-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        return root;
    }

    private static string CreateBundle(
        string root,
        string? tamperedCapabilityId = null,
        string? extraPath = null,
        string[]? adapterProviders = null)
    {
        var bundlePath = Path.Combine(root, "capabilities.nupkg");
        var capabilities = CapabilityIds
            .Select(
                capabilityId =>
                {
                    var bytes = Encoding.UTF8.GetBytes(
                        string.Concat("# ", capabilityId, "\n"));
                    return new BundleTestEntry(
                        capabilityId,
                        string.Concat(
                            ".agent-capabilities/capabilities/",
                            capabilityId,
                            "/CAPABILITY.md"),
                        string.Concat(
                            "contentFiles/any/any/.agent-capabilities/capabilities/",
                            capabilityId,
                            "/CAPABILITY.md"),
                        bytes,
                        Digest(bytes));
                })
            .ToArray();
        var adapters = (adapterProviders ?? Providers)
            .SelectMany(
                provider => CapabilityIds.Select(
                    capabilityId =>
                    {
                        var bytes = Encoding.UTF8.GetBytes(
                            string.Concat(
                                "---\nname: ",
                                capabilityId,
                                "\nprovider: ",
                                provider,
                                "\n---\n"));
                        return new BundleTestEntry(
                            capabilityId,
                            string.Concat(
                                ".agent-capabilities/provider-adapters/",
                                provider,
                                "/",
                                capabilityId,
                                "/SKILL.md"),
                            string.Concat(
                                "contentFiles/any/any/.agent-capabilities/provider-adapters/",
                                provider,
                                "/",
                                capabilityId,
                                "/SKILL.md"),
                            bytes,
                            Digest(bytes),
                            provider);
                    }))
            .ToArray();
        var manifest = BuildManifest(capabilities, adapters);

        using var archive = ZipFile.Open(
            bundlePath,
            ZipArchiveMode.Create);
        WriteEntry(
            archive,
            "contentFiles/any/any/.agent-capabilities/capability-bundle-manifest.json",
            Encoding.UTF8.GetBytes(manifest));
        foreach (var capability in capabilities)
        {
            var bytes = string.Equals(
                    capability.CapabilityId,
                    tamperedCapabilityId,
                    StringComparison.Ordinal)
                ? Encoding.UTF8.GetBytes("tampered")
                : capability.Content;
            WriteEntry(archive, capability.PackagePath, bytes);
        }

        foreach (var adapter in adapters)
        {
            WriteEntry(archive, adapter.PackagePath, adapter.Content);
        }

        if (extraPath is not null)
        {
            WriteEntry(
                archive,
                extraPath,
                Encoding.UTF8.GetBytes("not allow-listed"));
        }

        return bundlePath;
    }

    private static string BuildManifest(
        IReadOnlyList<BundleTestEntry> capabilities,
        IReadOnlyList<BundleTestEntry> adapters) =>
        string.Concat(
            "{\"bundleVersion\":\"2.0.0\",\"capabilities\":[",
            string.Join(
                ',',
                capabilities.Select(
                    entry => string.Concat(
                        "{\"capabilityId\":\"",
                        entry.CapabilityId,
                        "\",\"packagePath\":\"",
                        entry.PackagePath,
                        "\",\"sha256\":\"",
                        entry.Digest,
                        "\",\"sourcePath\":\"",
                        entry.SourcePath,
                        "\"}"))),
            "],\"kitVersion\":\"0.1.0-alpha.1\"," +
            "\"optionalProviderAdapters\":[",
            string.Join(
                ',',
                adapters.Select(
                    entry => string.Concat(
                        "{\"capabilityId\":\"",
                        entry.CapabilityId,
                        "\",\"packagePath\":\"",
                        entry.PackagePath,
                        "\",\"provider\":\"",
                        entry.Provider,
                        "\",\"sha256\":\"",
                        entry.Digest,
                        "\",\"sourcePath\":\"",
                        entry.SourcePath,
                        "\"}"))),
            "]}");

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());

    private static void WriteEntry(
        ZipArchive archive,
        string path,
        ReadOnlySpan<byte> content)
    {
        var entry = archive.CreateEntry(
            path,
            CompressionLevel.Optimal);
        using var stream = entry.Open();
        stream.Write(content);
    }

}
