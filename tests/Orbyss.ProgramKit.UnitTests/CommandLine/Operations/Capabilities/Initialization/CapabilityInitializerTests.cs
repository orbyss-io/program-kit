using System.Text;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

[TestClass]
public sealed class CapabilityInitializerTests
{
    private static readonly string[] CapabilityIds =
    [
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
        "maintain-software",
        "publish-dotnet-application-locally",
    ];

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task InitializesAndReadsExactThinCodexWrappersIdempotently()
    {
        var workspace = CreateWorkspace();
        try
        {
            var first = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
            var second = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(CommandExitCode.Success, first.ExitCode);
            Assert.Contains("created=6", first.Output);
            Assert.AreEqual(CommandExitCode.Success, second.ExitCode);
            Assert.Contains("unchanged=6", second.Output);
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
                        "program-kit capabilities preflight ",
                        capabilityId,
                        " --workspace-root ."),
                    wrapper);
                Assert.Contains(
                    string.Concat(
                        "program-kit capabilities read ",
                        capabilityId,
                        " --workspace-root ."),
                    wrapper);
                Assert.DoesNotContain(".agent-capabilities/", wrapper);
            }

            var read = await RunAsync(
                workspace,
                "capabilities",
                "read",
                "design-software",
                "--workspace-root",
                workspace);
            Assert.AreEqual(CommandExitCode.Success, read.ExitCode);
            Assert.StartsWith("# design-software", read.Output);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task AddsClaudeWithoutOrphaningCodexOwnership()
    {
        var workspace = CreateWorkspace();
        try
        {
            _ = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
            var codexPath = Path.Combine(
                workspace,
                ".agents",
                "skills",
                "design-software",
                "SKILL.md");
            var codexBytes = await File.ReadAllBytesAsync(
                codexPath,
                TestContext.CancellationToken);

            var result = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "claude",
                "--workspace-root",
                workspace);

            Assert.AreEqual(CommandExitCode.Success, result.ExitCode);
            Assert.AreSequenceEqual(
                codexBytes,
                await File.ReadAllBytesAsync(
                    codexPath,
                    TestContext.CancellationToken));
            var lockText = await File.ReadAllTextAsync(
                Path.Combine(
                    workspace,
                    ".program-kit",
                    "capabilities.lock.json"),
                TestContext.CancellationToken);
            Assert.Contains("\"provider\":\"claude\"", lockText);
            Assert.Contains("\"provider\":\"codex\"", lockText);
            Assert.Contains(
                "\"resourceId\":\"csharp-gate-alpha1-alpha2-migration\"",
                lockText);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RefusesUnownedCollisionWithoutPartialInitialization()
    {
        var workspace = CreateWorkspace();
        try
        {
            var collision = Path.Combine(
                workspace,
                ".agents",
                "skills",
                "design-software",
                "SKILL.md");
            Directory.CreateDirectory(Path.GetDirectoryName(collision)!);
            await File.WriteAllTextAsync(
                collision,
                "human-owned",
                TestContext.CancellationToken);

            var result = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                result.ExitCode);
            Assert.Contains("PKCLI008", result.Error);
            Assert.AreEqual(
                "human-owned",
                await File.ReadAllTextAsync(
                    collision,
                    TestContext.CancellationToken));
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
    public async Task RejectsProgramKitAuthoringMarkerWithoutProviderOutput()
    {
        var workspace = CreateWorkspace();
        try
        {
            var marker = Path.Combine(
                workspace,
                ".agent-capabilities",
                "authoring-workspace.json");
            Directory.CreateDirectory(Path.GetDirectoryName(marker)!);
            await File.WriteAllTextAsync(
                marker,
                "{\"capabilityInitialization\":\"denied\"}",
                TestContext.CancellationToken);

            var result = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);

            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                result.ExitCode);
            Assert.Contains("source authoring workspace", result.Error);
            Assert.IsFalse(
                Directory.Exists(Path.Combine(workspace, ".agents")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task MigratesExactAlpha3CodexWrappersToCurrentRoot()
    {
        var workspace = CreateWorkspace();
        try
        {
            var initialized = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
            Assert.AreEqual(CommandExitCode.Success, initialized.ExitCode);
            var currentRoot = Path.Combine(workspace, ".agents", "skills");
            var legacyRoot = Path.Combine(workspace, ".codex", "skills");
            Directory.CreateDirectory(Path.Combine(workspace, ".codex"));
            Directory.Move(currentRoot, legacyRoot);
            var lockPath = Path.Combine(
                workspace,
                ".program-kit",
                "capabilities.lock.json");
            var lockText = await File.ReadAllTextAsync(
                lockPath,
                TestContext.CancellationToken);
            lockText = lockText.Replace(
                ".agents/skills/",
                ".codex/skills/",
                StringComparison.Ordinal);
            await File.WriteAllTextAsync(
                lockPath,
                lockText,
                new UTF8Encoding(false),
                TestContext.CancellationToken);

            var migrated = await RunAsync(
                workspace,
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                workspace);
            var preflight = await RunAsync(
                workspace,
                "capabilities",
                "preflight",
                "design-software",
                "--workspace-root",
                workspace);

            Assert.AreEqual(CommandExitCode.Success, migrated.ExitCode);
            Assert.AreEqual(CommandExitCode.Success, preflight.ExitCode);
            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        currentRoot,
                        "design-software",
                        "SKILL.md")));
            Assert.IsFalse(
                File.Exists(
                    Path.Combine(
                        legacyRoot,
                        "design-software",
                        "SKILL.md")));
            Assert.Contains(
                "\"outputPath\":\".agents/skills/design-software/SKILL.md\"",
                await File.ReadAllTextAsync(
                    lockPath,
                    TestContext.CancellationToken));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

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

    private async Task<CommandResult> RunAsync(
        string workspace,
        params string[] arguments)
    {
        _ = workspace;
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

}
