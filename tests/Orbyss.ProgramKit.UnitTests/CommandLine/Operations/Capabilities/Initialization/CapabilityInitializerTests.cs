using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

[TestClass]
public sealed class CapabilityInitializerTests
{
    private const string CanonicalPathToken =
        "{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}";
    private static readonly string[] CapabilityIds =
    [
        "design-software",
        "develop-software",
        "implement-software-plan",
    ];
    private static readonly string[] Providers =
    [
        "claude",
        "codex",
    ];
    private static readonly JsonSerializerOptions ManifestJsonOptions =
        new(JsonSerializerDefaults.Web);

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task InitializesOnlyPortableCodexWrappersAndOwnershipLock()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "tools", "program-kit");
            CreateKit(kit);
            CapabilityInitializer sut = CreateSubject();

            await sut.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);
            await sut.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);

            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".agents")));
            foreach (var capabilityId in CapabilityIds)
            {
                var wrapper = await File.ReadAllTextAsync(
                    Path.Combine(
                        workspace,
                        ".codex",
                        "skills",
                        capabilityId,
                        "SKILL.md"),
                    TestContext.CancellationToken);
                Assert.Contains(
                    string.Concat(
                        "../../../tools/program-kit/.agent-capabilities/capabilities/",
                        capabilityId,
                        "/CAPABILITY.md"),
                    wrapper);
                Assert.DoesNotContain(CanonicalPathToken, wrapper);
            }

            var lockText = await File.ReadAllTextAsync(
                Path.Combine(
                    workspace,
                    ".program-kit",
                    "capabilities.lock.json"),
                TestContext.CancellationToken);
            Assert.Contains("\"provider\":\"codex\"", lockText);
            Assert.Contains(
                "\"programKitRoot\":\"tools/program-kit\"",
                lockText);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task UpdatesOnlyWrapperBytesOwnedByThePreviousLock()
    {
        var workspace = CreateWorkspace();
        try
        {
            var firstKit = Path.Combine(workspace, "program-kit");
            var secondKit = Path.Combine(workspace, "vendor", "program-kit");
            CreateKit(firstKit);
            CreateKit(secondKit);
            CapabilityInitializer sut = CreateSubject();
            await sut.InitializeAsync(
                "codex",
                workspace,
                firstKit,
                TestContext.CancellationToken);

            await sut.InitializeAsync(
                "codex",
                workspace,
                secondKit,
                TestContext.CancellationToken);

            var wrapper = await File.ReadAllTextAsync(
                Path.Combine(
                    workspace,
                    ".codex",
                    "skills",
                    "design-software",
                    "SKILL.md"),
                TestContext.CancellationToken);
            Assert.Contains(
                "../../../vendor/program-kit/.agent-capabilities/capabilities/design-software/CAPABILITY.md",
                wrapper);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RefusesUnownedWrapperAndTamperedCanonicalSource()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CreateKit(kit);
            var output = Path.Combine(
                workspace,
                ".codex",
                "skills",
                "design-software",
                "SKILL.md");
            Directory.CreateDirectory(Path.GetDirectoryName(output)!);
            await File.WriteAllTextAsync(
                output,
                "human-owned",
                TestContext.CancellationToken);
            CapabilityInitializer sut = CreateSubject();

            var collision =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.InitializeAsync(
                        "codex",
                        workspace,
                        kit,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI008", collision.DiagnosticId);
            Assert.AreEqual(
                "human-owned",
                await File.ReadAllTextAsync(
                    output,
                    TestContext.CancellationToken));

            File.Delete(output);
            await File.AppendAllTextAsync(
                Path.Combine(
                    kit,
                    ".agent-capabilities",
                    "capabilities",
                    "design-software",
                    "CAPABILITY.md"),
                "tampered",
                TestContext.CancellationToken);

            var tamper =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.InitializeAsync(
                        "codex",
                        workspace,
                        kit,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI008", tamper.DiagnosticId);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task InitializesOnlyPortableClaudeWrappersAndOwnershipLock()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "tools", "program-kit");
            CreateKit(kit);
            CapabilityInitializer sut = CreateSubject();

            await sut.InitializeAsync(
                "claude",
                workspace,
                kit,
                TestContext.CancellationToken);
            await sut.InitializeAsync(
                "claude",
                workspace,
                kit,
                TestContext.CancellationToken);

            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".codex")));
            foreach (var capabilityId in CapabilityIds)
            {
                var wrapper = await File.ReadAllTextAsync(
                    Path.Combine(
                        workspace,
                        ".claude",
                        "skills",
                        capabilityId,
                        "SKILL.md"),
                    TestContext.CancellationToken);
                Assert.Contains(
                    string.Concat(
                        "../../../tools/program-kit/.agent-capabilities/capabilities/",
                        capabilityId,
                        "/CAPABILITY.md"),
                    wrapper);
                Assert.DoesNotContain(CanonicalPathToken, wrapper);
            }

            var lockText = await File.ReadAllTextAsync(
                Path.Combine(
                    workspace,
                    ".program-kit",
                    "capabilities.lock.json"),
                TestContext.CancellationToken);
            Assert.Contains("\"provider\":\"claude\"", lockText);
            Assert.Contains(
                "\"outputPath\":\".claude/skills/design-software/SKILL.md\"",
                lockText);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task InitializingSecondProviderKeepsFirstWrappersAndRewritesLock()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CreateKit(kit);
            CapabilityInitializer sut = CreateSubject();
            await sut.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);
            var codexWrapperPath = Path.Combine(
                workspace,
                ".codex",
                "skills",
                "design-software",
                "SKILL.md");
            var codexWrapperBytes = await File.ReadAllBytesAsync(
                codexWrapperPath,
                TestContext.CancellationToken);

            await sut.InitializeAsync(
                "claude",
                workspace,
                kit,
                TestContext.CancellationToken);

            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".claude",
                        "skills",
                        "design-software",
                        "SKILL.md")));
            Assert.AreSequenceEqual(
                codexWrapperBytes,
                await File.ReadAllBytesAsync(
                    codexWrapperPath,
                    TestContext.CancellationToken));
            var lockText = await File.ReadAllTextAsync(
                Path.Combine(
                    workspace,
                    ".program-kit",
                    "capabilities.lock.json"),
                TestContext.CancellationToken);
            Assert.Contains("\"provider\":\"claude\"", lockText);
            Assert.DoesNotContain(".codex/skills/", lockText);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsUnreviewedProviderBeforeFilesystemWork()
    {
        CapabilityInitializer sut = CreateSubject();

        var exception =
            await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                () => sut.InitializeAsync(
                    "cursor",
                    "missing-workspace",
                    "missing-program-kit",
                    TestContext.CancellationToken).AsTask());

        Assert.AreEqual("PKCLI008", exception.DiagnosticId);
        Assert.AreEqual("/provider", exception.Path);
    }

    private static CapabilityInitializer CreateSubject() =>
        new(
            new CommandFileSystem(),
            new CapabilityBundleManifestReader());

    private static string CreateWorkspace()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-capability-initialization-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    private static void CreateKit(string kit)
    {
        var capabilities = new List<CapabilityBundlePayloadEntry>();
        var adapters = new List<CapabilityBundleProviderAdapter>();
        foreach (var capabilityId in CapabilityIds)
        {
            var canonicalRelative = string.Concat(
                ".agent-capabilities/capabilities/",
                capabilityId,
                "/CAPABILITY.md");
            var canonicalBytes = Encoding.UTF8.GetBytes(
                string.Concat("# ", capabilityId, "\n"));
            Write(kit, canonicalRelative, canonicalBytes);
            capabilities.Add(
                new CapabilityBundlePayloadEntry(
                    capabilityId,
                    string.Concat(
                        "contentFiles/any/any/",
                        canonicalRelative),
                    Digest(canonicalBytes),
                    canonicalRelative));
            foreach (var provider in Providers)
            {
                var adapterRelative = string.Concat(
                    ".agent-capabilities/provider-adapters/",
                    provider,
                    "/",
                    capabilityId,
                    "/SKILL.md");
                var adapterBytes = Encoding.UTF8.GetBytes(
                    string.Concat(
                        "---\nname: ",
                        capabilityId,
                        "\n---\n\nLoad `",
                        CanonicalPathToken,
                        "` for ",
                        provider,
                        ".\n"));
                Write(kit, adapterRelative, adapterBytes);
                adapters.Add(
                    new CapabilityBundleProviderAdapter(
                        capabilityId,
                        string.Concat(
                            "contentFiles/any/any/",
                            adapterRelative),
                        provider,
                        Digest(adapterBytes),
                        adapterRelative));
            }
        }

        var manifest = new CapabilityBundleManifest(
            "2.0.0",
            capabilities.ToArray(),
            "0.1.0-alpha.1",
            adapters.ToArray());
        Write(
            kit,
            ".agent-capabilities/capability-bundle-manifest.json",
            JsonSerializer.SerializeToUtf8Bytes(
                manifest,
                ManifestJsonOptions));
    }

    private static void Write(
        string root,
        string relativePath,
        ReadOnlySpan<byte> content)
    {
        var path = Path.Combine(
            root,
            relativePath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllBytes(path, content.ToArray());
    }

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());
}
