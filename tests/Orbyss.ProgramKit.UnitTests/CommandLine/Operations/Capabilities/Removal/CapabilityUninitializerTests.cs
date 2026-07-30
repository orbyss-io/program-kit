using Orbyss.ProgramKit.CommandLine.Operations.Capabilities;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Removal;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Removal;

[TestClass]
public sealed class CapabilityUninitializerTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task RemovesOneExactProviderAndPreservesOtherOwnership()
    {
        var workspace = CapabilityInitializerTests.CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CapabilityInitializerTests.CreateKit(kit);
            CommandFileSystem fileSystem = new();
            var initializer =
                CapabilityInitializerTests.CreateSubject(fileSystem);
            await initializer.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);
            await initializer.InitializeAsync(
                "claude",
                workspace,
                kit,
                TestContext.CancellationToken);
            var sut = CreateSubject(fileSystem);

            await sut.UninitializeAsync(
                "codex",
                workspace,
                TestContext.CancellationToken);

            Assert.IsFalse(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".agents",
                        "skills",
                        "design-software",
                        "SKILL.md")));
            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".claude",
                        "skills",
                        "design-software",
                        "SKILL.md")));
            CapabilityInitializationLockSerializer serializer = new();
            var ownership = serializer.Read(
                await File.ReadAllBytesAsync(
                    Path.Combine(
                        workspace,
                        ".program-kit",
                        "capabilities.lock.json"),
                    TestContext.CancellationToken));
            Assert.HasCount(1, ownership.Providers);
            Assert.AreEqual("claude", ownership.Providers[0].Provider);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RemovingFinalProviderRemovesOwnershipLock()
    {
        var workspace = CapabilityInitializerTests.CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CapabilityInitializerTests.CreateKit(kit);
            CommandFileSystem fileSystem = new();
            var initializer =
                CapabilityInitializerTests.CreateSubject(fileSystem);
            await initializer.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);
            var sut = CreateSubject(fileSystem);

            await sut.UninitializeAsync(
                "codex",
                workspace,
                TestContext.CancellationToken);

            Assert.IsFalse(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".program-kit",
                        "capabilities.lock.json")));
            Assert.IsFalse(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".agents",
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
    public async Task RefusesTamperedWrapperWithoutRemovingAnything()
    {
        var workspace = CapabilityInitializerTests.CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CapabilityInitializerTests.CreateKit(kit);
            CommandFileSystem fileSystem = new();
            var initializer =
                CapabilityInitializerTests.CreateSubject(fileSystem);
            await initializer.InitializeAsync(
                "codex",
                workspace,
                kit,
                TestContext.CancellationToken);
            var wrapper = Path.Combine(
                workspace,
                ".agents",
                "skills",
                "design-software",
                "SKILL.md");
            await File.AppendAllTextAsync(
                wrapper,
                "human-change",
                TestContext.CancellationToken);
            var lockPath = Path.Combine(
                workspace,
                ".program-kit",
                "capabilities.lock.json");
            var lockBytes = await File.ReadAllBytesAsync(
                lockPath,
                TestContext.CancellationToken);
            var sut = CreateSubject(fileSystem);

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.UninitializeAsync(
                        "codex",
                        workspace,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("/output", exception.Path);
            Assert.IsTrue(File.Exists(wrapper));
            Assert.AreSequenceEqual(
                lockBytes,
                await File.ReadAllBytesAsync(
                    lockPath,
                    TestContext.CancellationToken));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RefusesProviderNotOwnedByCurrentLock()
    {
        var workspace = CapabilityInitializerTests.CreateWorkspace();
        try
        {
            var kit = Path.Combine(workspace, "program-kit");
            CapabilityInitializerTests.CreateKit(kit);
            CommandFileSystem fileSystem = new();
            var initializer =
                CapabilityInitializerTests.CreateSubject(fileSystem);
            await initializer.InitializeAsync(
                "claude",
                workspace,
                kit,
                TestContext.CancellationToken);
            var sut = CreateSubject(fileSystem);

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.UninitializeAsync(
                        "codex",
                        workspace,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("/provider", exception.Path);
            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        workspace,
                        ".claude",
                        "skills",
                        "design-software",
                        "SKILL.md")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    private static CapabilityUninitializer CreateSubject(
        ICommandFileSystem fileSystem) =>
        new(
            fileSystem,
            new CapabilityInitializationLockSerializer(),
            new CapabilityWorkspaceTransaction(fileSystem));
}
