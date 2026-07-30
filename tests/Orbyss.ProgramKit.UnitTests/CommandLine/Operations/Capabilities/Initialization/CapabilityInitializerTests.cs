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
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
        "maintain-software",
    ];
    private static readonly string[] Providers =
    [
        "claude",
        "codex",
    ];
    private static readonly Dictionary<string, string> SupportingResourcePaths =
        new(StringComparer.Ordinal)
        {
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
        };
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

            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".codex")));
            Assert.IsFalse(
                Directory.Exists(
                    Path.Combine(workspace, ".agent-capabilities")));
            foreach (var capabilityId in CapabilityIds)
            {
                var wrapper = await File.ReadAllTextAsync(
                    Path.Combine(
                        workspace,
                        ".agents",
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
                    ".agents",
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
    public async Task MigratesExactLegacyLockAndCodexRootAfterHumanSelectedKit()
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
            var lockPath = Path.Combine(
                workspace,
                ".program-kit",
                "capabilities.lock.json");
            CapabilityInitializationLockSerializer serializer = new();
            var current = serializer.Read(
                await File.ReadAllBytesAsync(
                    lockPath,
                    TestContext.CancellationToken));
            var currentProvider = current.Providers.Single();
            var legacy = new
            {
                LockVersion = "1.0.0",
                BundleVersion = "2.2.0",
                currentProvider.Provider,
                currentProvider.ProgramKitRoot,
                currentProvider.ManifestSha256,
                Capabilities = currentProvider.Capabilities
                    .Where(
                        entry =>
                            !string.Equals(
                                entry.CapabilityId,
                                "maintain-software",
                                StringComparison.Ordinal))
                    .Select(
                        entry =>
                            entry with
                            {
                                OutputPath = entry.OutputPath.Replace(
                                    ".agents/skills/",
                                    ".codex/skills/",
                                    StringComparison.Ordinal),
                            })
                    .ToArray(),
            };
            Directory.Move(
                Path.Combine(workspace, ".agents"),
                Path.Combine(workspace, ".codex"));
            await File.WriteAllBytesAsync(
                lockPath,
                JsonSerializer.SerializeToUtf8Bytes(
                    legacy,
                    ManifestJsonOptions),
                TestContext.CancellationToken);
            File.Delete(
                Path.Combine(
                    workspace,
                    ".codex",
                    "skills",
                    "maintain-software",
                    "SKILL.md"));

            await sut.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);

            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".agents",
                        "skills",
                        "maintain-software",
                        "SKILL.md")));
            var upgraded = serializer.Read(
                await File.ReadAllBytesAsync(
                    lockPath,
                    TestContext.CancellationToken));
            Assert.AreEqual("2.0.0", upgraded.LockVersion);
            Assert.AreEqual(
                "4.0.0",
                upgraded.Providers.Single().BundleVersion);
            Assert.HasCount(
                5,
                upgraded.Providers.Single().Capabilities);
            Assert.IsFalse(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".codex",
                        "skills",
                        "design-software",
                        "SKILL.md")));
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
                ".agents",
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
    public async Task MissingGateDesignAdapterIsASetupBlockerWithoutPartialInitialization()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CreateKit(kit);
            File.Delete(
                Path.Combine(
                    kit,
                    ".agent-capabilities",
                    "provider-adapters",
                    "codex",
                    "design-csharp-build-gate",
                    "SKILL.md"));
            CapabilityInitializer sut = CreateSubject();

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.InitializeAsync(
                        "codex",
                        workspace,
                        kit,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI008", exception.DiagnosticId);
            Assert.Contains("/adapter", exception.Path);
            Assert.IsFalse(
                Directory.Exists(
                    Path.Combine(workspace, ".agents", "skills")));
            Assert.IsFalse(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".program-kit",
                        "capabilities.lock.json")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task TamperedSupportingProfileIsASetupBlockerWithoutInitialization()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CreateKit(kit);
            var resourcePath = Path.Combine(
                kit,
                SupportingResourcePaths[
                    "software-change-profile-review-source"]
                    .Replace('/', Path.DirectorySeparatorChar));
            await File.AppendAllTextAsync(
                resourcePath,
                "tampered",
                TestContext.CancellationToken);
            CapabilityInitializer sut = CreateSubject();

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.InitializeAsync(
                        "codex",
                        workspace,
                        kit,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI008", exception.DiagnosticId);
            Assert.Contains("/supportingResources", exception.Path);
            Assert.IsFalse(
                Directory.Exists(
                    Path.Combine(workspace, ".agents", "skills")));
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
                ".agents",
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
            Assert.Contains("\"provider\":\"codex\"", lockText);
            Assert.Contains(".claude/skills/", lockText);
            Assert.Contains(".agents/skills/", lockText);
            CapabilityInitializationLockSerializer serializer = new();
            var ownership = serializer.Read(
                await File.ReadAllBytesAsync(
                    Path.Combine(
                        workspace,
                        ".program-kit",
                        "capabilities.lock.json"),
                    TestContext.CancellationToken));
            Assert.AreSequenceEqual(
                ["claude", "codex"],
                ownership.Providers.Select(
                    static binding => binding.Provider));
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

    [TestMethod]
    public async Task RejectsProgramKitSourceAuthoringWorkspaceWithoutOutput()
    {
        var workspace = CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CreateKit(kit);
            Write(
                kit,
                ".agent-capabilities/authoring-workspace.json",
                Encoding.UTF8.GetBytes(
                    "{\"capabilityInitialization\":\"denied\"}"));
            CapabilityInitializer sut = CreateSubject();

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.InitializeAsync(
                        "codex",
                        workspace,
                        kit,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI008", exception.DiagnosticId);
            Assert.AreEqual("/programKitRoot", exception.Path);
            Assert.Contains("source authoring workspace", exception.Message);
            Assert.IsFalse(
                Directory.Exists(
                    Path.Combine(workspace, ".agents")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RejectsUserGlobalProviderWorkspaceBeforeContainment()
    {
        var kit = CreateWorkspace();
        try
        {
            CreateKit(kit);
            var userProfile = Environment.GetFolderPath(
                Environment.SpecialFolder.UserProfile);
            Assert.IsFalse(string.IsNullOrWhiteSpace(userProfile));
            CapabilityInitializer sut = CreateSubject();

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.InitializeAsync(
                        "codex",
                        userProfile,
                        kit,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("PKCLI008", exception.DiagnosticId);
            Assert.AreEqual("/workspaceRoot", exception.Path);
            Assert.Contains("user-global", exception.Message);
        }
        finally
        {
            Directory.Delete(kit, recursive: true);
        }
    }

    internal static CapabilityInitializer CreateSubject() =>
        CreateSubject(new CommandFileSystem());

    internal static CapabilityInitializer CreateSubject(
        ICommandFileSystem fileSystem) =>
        new(
            fileSystem,
            new CapabilityBundleManifestReader(),
            new CapabilityInitializationLockSerializer(),
            new CapabilityWorkspaceTransaction(fileSystem));

    internal static string CreateWorkspace()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-capability-initialization-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    internal static void CreateKit(string kit)
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

        var resources = SupportingResourcePaths
            .Select(
                pair =>
                {
                    var bytes = Encoding.UTF8.GetBytes(
                        string.Concat("# ", pair.Key, "\n"));
                    Write(kit, pair.Value, bytes);
                    return new CapabilityBundleSupportingResource(
                        string.Concat(
                            "contentFiles/any/any/",
                            pair.Value),
                        pair.Key,
                        Digest(bytes),
                        pair.Value);
                })
            .ToArray();
        var manifest = new CapabilityBundleManifest(
            "4.0.0",
            capabilities.ToArray(),
            "0.1.0-alpha.1",
            adapters.ToArray(),
            resources);
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
