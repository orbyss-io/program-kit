using System.Text;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Generation;

[TestClass]
public sealed class FileSystemWorkbenchOutputWorkspaceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task StagedFilesRemainPrivateUntilOneRootCommit()
    {
        var testParent = CreateTestParent();
        var outputRoot = Path.Combine(testParent, "generated");
        try
        {
            FileSystemWorkbenchOutputWorkspace workspace =
                new FileSystemWorkbenchOutputWorkspace();
            var transaction = await workspace.BeginAsync(
                outputRoot,
                GenerationCollisionPolicy.Fail,
                CancellationToken.None);

            await transaction.StageAsync(
                new GeneratedOutput(
                    "nested/a.txt",
                    Encoding.UTF8.GetBytes("a")),
                CancellationToken.None);
            await transaction.StageAsync(
                new GeneratedOutput(
                    "z.txt",
                    Encoding.UTF8.GetBytes("z")),
                CancellationToken.None);

            Assert.IsFalse(Directory.Exists(outputRoot));
            await transaction.CommitAsync(CancellationToken.None);

            Assert.AreEqual(
                "a",
                await File.ReadAllTextAsync(
                    Path.Combine(outputRoot, "nested", "a.txt"),
                    TestContext.CancellationToken));
            Assert.AreEqual(
                "z",
                await File.ReadAllTextAsync(
                    Path.Combine(outputRoot, "z.txt"),
                    TestContext.CancellationToken));
            Assert.IsEmpty(FindStagingDirectories(testParent));
        }
        finally
        {
            DeleteTestParent(testParent);
        }
    }

    [TestMethod]
    public async Task PostStagingCancellationExposesNoDeclaredFileAndRollbackRemovesStaging()
    {
        var testParent = CreateTestParent();
        var outputRoot = Path.Combine(testParent, "generated");
        try
        {
            FileSystemWorkbenchOutputWorkspace workspace =
                new FileSystemWorkbenchOutputWorkspace();
            var transaction = await workspace.BeginAsync(
                outputRoot,
                GenerationCollisionPolicy.Fail,
                TestContext.CancellationToken);
            await transaction.StageAsync(
                new GeneratedOutput("a.txt", Encoding.UTF8.GetBytes("a")),
                TestContext.CancellationToken);
            using var cancellation = new CancellationTokenSource();
            cancellation.Cancel();

            await Assert.ThrowsExactlyAsync<OperationCanceledException>(
                async () => await transaction.CommitAsync(cancellation.Token));

            Assert.IsFalse(Directory.Exists(outputRoot));
            Assert.IsFalse(File.Exists(Path.Combine(outputRoot, "a.txt")));
            await transaction.RollbackAsync(TestContext.CancellationToken);
            Assert.IsEmpty(FindStagingDirectories(testParent));
        }
        finally
        {
            DeleteTestParent(testParent);
        }
    }

    [TestMethod]
    public async Task CancellationRollsBackPrivateStagingWithoutExposingDeclaredFiles()
    {
        var testParent = CreateTestParent();
        var outputRoot = Path.Combine(testParent, "generated");
        try
        {
            IWorkbenchGenerator<string> generator = new TestSupport.TestWorkbenchGenerator(
            [
                new GeneratedOutput("a.txt", Encoding.UTF8.GetBytes("a")),
            ]);
            IWorkbenchOutputWorkspace workspace =
                new FileSystemWorkbenchOutputWorkspace();
            var service =
                new WorkbenchGenerationService<string>(generator, workspace);
            using var cancellation = new CancellationTokenSource();
            cancellation.Cancel();

            var result = await service.GenerateAsync(
                new GenerationRequest<string>(
                    "input",
                    outputRoot,
                    GenerationCollisionPolicy.Fail,
                    GenerationLimits.Default),
                cancellation.Token);

            Assert.IsFalse(result.IsSuccessful);
            Assert.IsFalse(Directory.Exists(outputRoot));
            Assert.IsFalse(File.Exists(Path.Combine(outputRoot, "a.txt")));
            Assert.IsEmpty(FindStagingDirectories(testParent));
        }
        finally
        {
            DeleteTestParent(testParent);
        }
    }

    [TestMethod]
    public async Task CommitCollisionLeavesExistingRootUntouchedAndExposesNoDeclaredFile()
    {
        var testParent = CreateTestParent();
        var outputRoot = Path.Combine(testParent, "generated");
        try
        {
            Directory.CreateDirectory(outputRoot);
            var sentinelPath = Path.Combine(outputRoot, "sentinel.txt");
            await File.WriteAllTextAsync(
                sentinelPath,
                "existing",
                TestContext.CancellationToken);
            IWorkbenchGenerator<string> generator = new TestSupport.TestWorkbenchGenerator(
            [
                new GeneratedOutput("a.txt", Encoding.UTF8.GetBytes("a")),
            ]);
            IWorkbenchOutputWorkspace workspace =
                new FileSystemWorkbenchOutputWorkspace();
            var service =
                new WorkbenchGenerationService<string>(generator, workspace);

            var result = await service.GenerateAsync(
                new GenerationRequest<string>(
                    "input",
                    outputRoot,
                    GenerationCollisionPolicy.Fail,
                    GenerationLimits.Default),
                CancellationToken.None);

            Assert.IsFalse(result.IsSuccessful);
            Assert.AreEqual(
                "existing",
                await File.ReadAllTextAsync(
                    sentinelPath,
                    TestContext.CancellationToken));
            Assert.IsFalse(File.Exists(Path.Combine(outputRoot, "a.txt")));
            Assert.IsEmpty(FindStagingDirectories(testParent));
        }
        finally
        {
            DeleteTestParent(testParent);
        }
    }

    private static string CreateTestParent()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-workbench-output-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    private static string[] FindStagingDirectories(string testParent) =>
        Directory.GetDirectories(
            testParent,
            ".*.program-kit-stage-*",
            SearchOption.TopDirectoryOnly);

    private static void DeleteTestParent(string testParent)
    {
        var resolved = Path.GetFullPath(testParent);
        var tempRoot = Path.GetFullPath(Path.GetTempPath())
            .TrimEnd(Path.DirectorySeparatorChar);
        var expectedPrefix = string.Concat(
            tempRoot,
            Path.DirectorySeparatorChar,
            "program-kit-workbench-output-");
        var comparison = OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;
        if (!resolved.StartsWith(expectedPrefix, comparison))
        {
            throw new InvalidOperationException(
                "Refusing to remove a directory outside the test-owned root.");
        }

        if (Directory.Exists(resolved))
        {
            Directory.Delete(resolved, recursive: true);
        }
    }
}
