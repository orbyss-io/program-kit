using System.Text;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Removal;

[TestClass]
public sealed class CapabilityUninitializerTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task RemovesOneExactProviderAndPreservesOtherOwnership()
    {
        var workspace = CreateWorkspace();
        try
        {
            _ = await RunAsync(
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
            _ = await RunAsync(
                "capabilities",
                "initialize",
                "--provider",
                "claude",
                "--workspace-root",
                workspace);

            var result = await RunAsync(
                "capabilities",
                "uninitialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(CommandExitCode.Success, result.ExitCode);
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
            var lockText = await File.ReadAllTextAsync(
                Path.Combine(
                    workspace,
                    ".program-kit",
                    "capabilities.lock.json"),
                TestContext.CancellationToken);
            Assert.Contains("\"provider\":\"claude\"", lockText);
            Assert.DoesNotContain("\"provider\":\"codex\"", lockText);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RemovingFinalProviderRemovesOwnershipLock()
    {
        var workspace = CreateWorkspace();
        try
        {
            _ = await RunAsync(
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            var result = await RunAsync(
                "capabilities",
                "uninitialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(CommandExitCode.Success, result.ExitCode);
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
        var workspace = CreateWorkspace();
        try
        {
            _ = await RunAsync(
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
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

            var result = await RunAsync(
                "capabilities",
                "uninitialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                result.ExitCode);
            Assert.Contains("PKCLI008", result.Error);
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
    public async Task RefusesNullLockEntryAsConformanceFailure()
    {
        var workspace = CreateWorkspace();
        try
        {
            _ = await RunAsync(
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
            var lockPath = Path.Combine(
                workspace,
                ".program-kit",
                "capabilities.lock.json");
            var lockText = await File.ReadAllTextAsync(
                lockPath,
                TestContext.CancellationToken);
            var capabilitiesStart = lockText.IndexOf(
                "\"capabilities\":[",
                StringComparison.Ordinal);
            var firstEntryStart = lockText.IndexOf(
                '{',
                capabilitiesStart);
            var firstEntryEnd = lockText.IndexOf(
                '}',
                firstEntryStart);
            var malformed = string.Concat(
                lockText.AsSpan(0, firstEntryStart),
                "null",
                lockText.AsSpan(firstEntryEnd + 1));
            await File.WriteAllTextAsync(
                lockPath,
                malformed,
                TestContext.CancellationToken);

            var result = await RunAsync(
                "capabilities",
                "uninitialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                result.ExitCode);
            Assert.Contains("PKCLI008", result.Error);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    private async Task<CommandResult> RunAsync(params string[] arguments)
    {
        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);
        var exitCode = await application.RunAsync(
            arguments,
            TestContext.CancellationToken);
        return new CommandResult(
            exitCode,
            Encoding.UTF8.GetString(console.StandardOutput),
            Encoding.UTF8.GetString(console.StandardError));
    }

    private static string CreateWorkspace()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-capability-removal-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }
}
