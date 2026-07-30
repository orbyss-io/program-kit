using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Files;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

[TestClass]
public sealed class CapabilityWorkspaceTransactionTests
{
    private static readonly JsonSerializerOptions JsonOptions =
        new(JsonSerializerDefaults.Web);

    [TestMethod]
    public async Task AppliesCompleteWriteAndDeleteSetAndCleansJournal()
    {
        var workspace = CreateWorkspace();
        try
        {
            var deleted = Path.Combine(workspace, "deleted.txt");
            await File.WriteAllTextAsync(
                deleted,
                "old",
                TestContext.CancellationToken);
            CapabilityWorkspaceTransaction sut = new(
                new CommandFileSystem());

            await sut.ApplyAsync(
                workspace,
                [
                    new CapabilityWorkspaceMutation(
                        "written.txt",
                        Encoding.UTF8.GetBytes("new")),
                    new CapabilityWorkspaceMutation(
                        "deleted.txt",
                        null),
                ],
                TestContext.CancellationToken);

            Assert.AreEqual(
                "new",
                await File.ReadAllTextAsync(
                    Path.Combine(workspace, "written.txt"),
                    TestContext.CancellationToken));
            Assert.IsFalse(File.Exists(deleted));
            Assert.IsFalse(
                Directory.Exists(
                    Path.Combine(
                        workspace,
                        ".program-kit",
                        "capabilities.transaction")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task CancellationBeforePrepareLeavesWorkspaceUnchanged()
    {
        var workspace = CreateWorkspace();
        try
        {
            CapabilityWorkspaceTransaction sut = new(
                new CommandFileSystem());
            using CancellationTokenSource cancellation = new();
            cancellation.Cancel();

            await Assert.ThrowsExactlyAsync<OperationCanceledException>(
                () => sut.ApplyAsync(
                    workspace,
                    [
                        new CapabilityWorkspaceMutation(
                            "written.txt",
                            Encoding.UTF8.GetBytes("new")),
                    ],
                    cancellation.Token).AsTask());

            Assert.IsFalse(
                File.Exists(Path.Combine(workspace, "written.txt")));
            Assert.IsFalse(
                Directory.Exists(
                    Path.Combine(
                        workspace,
                        ".program-kit",
                        "capabilities.transaction")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RecoversInterruptedPartialCommitFromExactBackup()
    {
        var workspace = CreateWorkspace();
        try
        {
            var target = Path.Combine(workspace, "owned.txt");
            await File.WriteAllTextAsync(
                target,
                "partially-new",
                TestContext.CancellationToken);
            var transactionRoot = Path.Combine(
                workspace,
                ".program-kit",
                "capabilities.transaction");
            var stagePath = Path.Combine(
                transactionRoot,
                "stage",
                "0000.bin");
            var backupPath = Path.Combine(
                transactionRoot,
                "backup",
                "0000.bin");
            Directory.CreateDirectory(Path.GetDirectoryName(stagePath)!);
            Directory.CreateDirectory(Path.GetDirectoryName(backupPath)!);
            var desired = Encoding.UTF8.GetBytes("new");
            await File.WriteAllBytesAsync(
                stagePath,
                desired,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                backupPath,
                "old",
                TestContext.CancellationToken);
            var journal = new
            {
                TransactionVersion = "1.0.0",
                Entries = new[]
                {
                    new
                    {
                        RelativePath = "owned.txt",
                        HadOriginal = true,
                        OriginalSha256 = Digest(
                            Encoding.UTF8.GetBytes("old")),
                        DesiredSha256 = Digest(desired),
                        StagePath =
                            ".program-kit/capabilities.transaction/stage/0000.bin",
                        BackupPath =
                            ".program-kit/capabilities.transaction/backup/0000.bin",
                    },
                },
            };
            await File.WriteAllBytesAsync(
                Path.Combine(transactionRoot, "journal.json"),
                JsonSerializer.SerializeToUtf8Bytes(
                    journal,
                    JsonOptions),
                TestContext.CancellationToken);
            CapabilityWorkspaceTransaction sut = new(
                new CommandFileSystem());

            await sut.RecoverAsync(
                workspace,
                TestContext.CancellationToken);

            Assert.AreEqual(
                "old",
                await File.ReadAllTextAsync(
                    target,
                    TestContext.CancellationToken));
            Assert.IsFalse(Directory.Exists(transactionRoot));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public async Task RefusesTamperedRecoveryBackupWithoutChangingTarget()
    {
        var workspace = CreateWorkspace();
        try
        {
            var target = Path.Combine(workspace, "owned.txt");
            await File.WriteAllTextAsync(
                target,
                "partially-new",
                TestContext.CancellationToken);
            var transactionRoot = Path.Combine(
                workspace,
                ".program-kit",
                "capabilities.transaction");
            var stagePath = Path.Combine(
                transactionRoot,
                "stage",
                "0000.bin");
            var backupPath = Path.Combine(
                transactionRoot,
                "backup",
                "0000.bin");
            Directory.CreateDirectory(Path.GetDirectoryName(stagePath)!);
            Directory.CreateDirectory(Path.GetDirectoryName(backupPath)!);
            var desired = Encoding.UTF8.GetBytes("new");
            await File.WriteAllBytesAsync(
                stagePath,
                desired,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                backupPath,
                "tampered",
                TestContext.CancellationToken);
            var journal = new
            {
                TransactionVersion = "1.0.0",
                Entries = new[]
                {
                    new
                    {
                        RelativePath = "owned.txt",
                        HadOriginal = true,
                        OriginalSha256 = Digest(
                            Encoding.UTF8.GetBytes("old")),
                        DesiredSha256 = Digest(desired),
                        StagePath =
                            ".program-kit/capabilities.transaction/stage/0000.bin",
                        BackupPath =
                            ".program-kit/capabilities.transaction/backup/0000.bin",
                    },
                },
            };
            await File.WriteAllBytesAsync(
                Path.Combine(transactionRoot, "journal.json"),
                JsonSerializer.SerializeToUtf8Bytes(
                    journal,
                    JsonOptions),
                TestContext.CancellationToken);
            CapabilityWorkspaceTransaction sut = new(
                new CommandFileSystem());

            var exception =
                await Assert.ThrowsExactlyAsync<CapabilityOperationException>(
                    () => sut.RecoverAsync(
                        workspace,
                        TestContext.CancellationToken).AsTask());

            Assert.AreEqual("/transaction/entries", exception.Path);
            Assert.AreEqual(
                "partially-new",
                await File.ReadAllTextAsync(
                    target,
                    TestContext.CancellationToken));
            Assert.IsTrue(Directory.Exists(transactionRoot));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    public TestContext TestContext { get; set; } = null!;

    private static string CreateWorkspace()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-capability-transaction-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());
}
