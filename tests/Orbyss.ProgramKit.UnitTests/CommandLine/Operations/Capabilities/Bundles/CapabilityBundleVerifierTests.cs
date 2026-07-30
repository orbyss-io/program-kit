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
        "design-csharp-build-gate",
        "develop-software",
        "design-software",
        "implement-software-plan",
        "maintain-software",
        "publish-dotnet-application-locally",
    ];
    private static readonly string[] Providers =
    [
        "claude",
        "codex",
    ];
    private static readonly Dictionary<string, string> SupportingResourcePaths =
        new(StringComparer.Ordinal)
        {
            ["consumer-capability-catalog"] =
                ".agent-capabilities/supporting-resources/catalogs/consumer-capability-catalog-0.1.0-alpha.1.json",
            ["csharp-gate-alpha1-alpha2-migration"] =
                "schemas/csharp-build-gates/csharp-build-gate-definition-alpha.1-to-alpha.2-migration.json",
            ["csharp-gate-authoring-catalog"] =
                ".agent-capabilities/supporting-resources/csharp-gates/csharp-gate-authoring-catalog-0.1.0-alpha.1.json",
            ["dotnet-console-input-materialization-guide"] =
                ".agent-capabilities/supporting-resources/dotnet/dotnet-console-input-materialization-guide.md",
            ["dotnet-console-command-sketch-example"] =
                ".agent-capabilities/supporting-resources/dotnet/dotnet-console-command-sketch-example.json",
            ["dotnet-console-contract-style"] =
                ".agent-capabilities/supporting-resources/dotnet/dotnet-console-contract-style-0.1.0-alpha.1.json",
            ["dotnet-console-integration-project-example"] =
                ".agent-capabilities/supporting-resources/dotnet/Example.ConsoleIntegration.csproj",
            ["dotnet-console-integration-source-example"] =
                ".agent-capabilities/supporting-resources/dotnet/ConsoleIntegration.cs",
            ["dotnet-console-input-request-example"] =
                ".agent-capabilities/supporting-resources/dotnet/dotnet-console-input-request-example.json",
            ["software-change-completion-profile-set"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.json",
            ["software-change-completion-profile-set-schema"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.schema.json",
            ["software-change-profile-commit-and-push-coherently"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/commit-and-push-coherently.md",
            ["software-change-profile-publish-with-separate-authority"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/publish-with-separate-authority.md",
            ["software-change-profile-record-evidence-and-review-diff"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/record-evidence-and-review-diff.md",
            ["software-change-profile-refresh-affected-output"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/refresh-affected-output.md",
            ["software-change-profile-review-source"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/review-source.md",
            ["software-change-profile-select-build-and-test"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/select-build-and-test.md",
            ["software-change-profile-verify-integrity"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/verify-integrity.md",
            ["software-change-troubleshooting"] =
                ".agent-capabilities/supporting-resources/troubleshooting/software-change-troubleshooting.md",
        };

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
    public async Task RejectsUnsupportedManifestFormatIndependentlyOfBundleRelease()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                manifestVersion: "0.1.0-alpha.2");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI007", exception.DiagnosticId);
            Assert.Contains("manifest format", exception.Message);
            Assert.AreEqual(
                "/bundle/manifest/manifestVersion",
                exception.Path);
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
    public async Task RejectsTamperedSharedCompletionProfileBytes()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                tamperedResourceId:
                    "software-change-profile-review-source");
            CapabilityBundleVerifier sut = new(
                new CapabilityBundleManifestReader());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.VerifyAsync(
                        bundle,
                        TestContext.CancellationToken).AsTask());

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
    public async Task RejectsContributorOnlyAuthoringCapabilityFromDistribution()
    {
        var root = CreateRoot();
        try
        {
            var bundle = CreateBundle(
                root,
                extraPath:
                    "contentFiles/any/any/.agent-capabilities/capabilities/author-and-maintain-skills/CAPABILITY.md");
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
        string? tamperedResourceId = null,
        string? extraPath = null,
        string[]? adapterProviders = null,
        string manifestVersion = "0.1.0-alpha.1")
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
        var resources = SupportingResourcePaths
            .Select(
                pair =>
                {
                    var bytes = Encoding.UTF8.GetBytes(
                        string.Concat("# ", pair.Key, "\n"));
                    return new BundleTestEntry(
                        pair.Key,
                        pair.Value,
                        string.Equals(
                                pair.Key,
                                "csharp-gate-alpha1-alpha2-migration",
                                StringComparison.Ordinal)
                            ? "contentFiles/any/any/.agent-capabilities/supporting-resources/csharp-gates/csharp-build-gate-definition-alpha.1-to-alpha.2-migration.json"
                            : string.Concat(
                                "contentFiles/any/any/",
                                pair.Value),
                        bytes,
                        Digest(bytes));
                })
            .ToArray();
        var manifest = BuildManifest(
            capabilities,
            adapters,
            resources,
            manifestVersion);

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

        foreach (var resource in resources)
        {
            var bytes = string.Equals(
                    resource.CapabilityId,
                    tamperedResourceId,
                    StringComparison.Ordinal)
                ? Encoding.UTF8.GetBytes("tampered")
                : resource.Content;
            WriteEntry(archive, resource.PackagePath, bytes);
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
        IReadOnlyList<BundleTestEntry> adapters,
        IReadOnlyList<BundleTestEntry> resources,
        string manifestVersion) =>
        string.Concat(
            "{\"manifestVersion\":\"",
            manifestVersion,
            "\"," +
            "\"bundleVersion\":\"0.1.0-alpha.3\",\"capabilities\":[",
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
            "],\"kitVersion\":\"0.1.0-alpha.3\"," +
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
            "],\"supportingResources\":[",
            string.Join(
                ',',
                resources.Select(
                    entry => string.Concat(
                        "{\"packagePath\":\"",
                        entry.PackagePath,
                        "\",\"resourceId\":\"",
                        entry.CapabilityId,
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
