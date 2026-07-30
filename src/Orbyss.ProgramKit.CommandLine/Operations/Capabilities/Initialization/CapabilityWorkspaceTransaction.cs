using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Journaled exact workspace mutation with rollback and next-operation
/// recovery.
/// </summary>
public sealed class CapabilityWorkspaceTransaction :
    ICapabilityWorkspaceTransaction
{
    private const string TransactionDirectory =
        ".program-kit/capabilities.transaction";
    private const string JournalRelativePath =
        ".program-kit/capabilities.transaction/journal.json";
    private const string TransactionVersion = "1.0.0";
    private const int MaximumTransactionFileBytes = 1024 * 1024;
    private readonly ICommandFileSystem fileSystem;

    /// <summary>Creates the transaction over one explicit filesystem.</summary>
    public CapabilityWorkspaceTransaction(ICommandFileSystem fileSystem)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
    }

    /// <inheritdoc />
    public async ValueTask RecoverAsync(
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var transactionRoot = ResolveUnder(
            workspaceRoot,
            TransactionDirectory);
        if (!fileSystem.DirectoryExists(transactionRoot))
        {
            return;
        }

        var journalPath = ResolveUnder(workspaceRoot, JournalRelativePath);
        if (!fileSystem.FileExists(journalPath))
        {
            fileSystem.DeleteDirectory(transactionRoot);
            return;
        }

        var journal = await ReadJournalAsync(
            journalPath,
            cancellationToken).ConfigureAwait(false);
        ValidateJournal(journal);
        if (!await MatchesDesiredStateAsync(
                workspaceRoot,
                journal,
                cancellationToken).ConfigureAwait(false))
        {
            await RestoreAsync(
                workspaceRoot,
                journal,
                cancellationToken).ConfigureAwait(false);
        }

        fileSystem.DeleteDirectory(transactionRoot);
    }

    /// <inheritdoc />
    public async ValueTask ApplyAsync(
        string workspaceRoot,
        IReadOnlyList<CapabilityWorkspaceMutation> mutations,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(mutations);
        cancellationToken.ThrowIfCancellationRequested();
        if (mutations.Count == 0)
        {
            return;
        }

        await RecoverAsync(
            workspaceRoot,
            cancellationToken).ConfigureAwait(false);
        ValidateMutations(mutations);
        var transactionRoot = ResolveUnder(
            workspaceRoot,
            TransactionDirectory);
        fileSystem.CreateDirectory(transactionRoot);
        CapabilityWorkspaceTransactionJournal? journal = null;
        try
        {
            journal = await PrepareAsync(
                workspaceRoot,
                mutations,
                cancellationToken).ConfigureAwait(false);
            var journalBytes =
                CapabilityWorkspaceTransactionSerializer.Write(journal);
            await fileSystem.WriteAllBytesAsync(
                ResolveUnder(workspaceRoot, JournalRelativePath),
                journalBytes,
                cancellationToken).ConfigureAwait(false);
            cancellationToken.ThrowIfCancellationRequested();

            foreach (var entry in journal.Entries)
            {
                var target = ResolveUnder(
                    workspaceRoot,
                    entry.RelativePath);
                if (entry.StagePath is null)
                {
                    fileSystem.DeleteFile(target);
                    continue;
                }

                var content = await ReadBoundedAsync(
                    ResolveUnder(workspaceRoot, entry.StagePath),
                    CancellationToken.None).ConfigureAwait(false);
                if (!string.Equals(
                        Digest(content.Span),
                        entry.DesiredSha256,
                        StringComparison.Ordinal))
                {
                    throw InvalidTransaction(
                        "A staged capability transaction file differs from its journal digest.",
                        "/transaction/entries");
                }

                await fileSystem.WriteAllBytesAsync(
                    target,
                    content,
                    CancellationToken.None).ConfigureAwait(false);
            }

            fileSystem.DeleteDirectory(transactionRoot);
        }
        catch (Exception exception)
            when (exception is OperationCanceledException or
                CapabilityOperationException or
                IOException or
                UnauthorizedAccessException)
        {
            if (journal is not null)
            {
                await RestoreAsync(
                    workspaceRoot,
                    journal,
                    CancellationToken.None).ConfigureAwait(false);
            }

            fileSystem.DeleteDirectory(transactionRoot);
            throw;
        }
    }

    private async ValueTask<CapabilityWorkspaceTransactionJournal> PrepareAsync(
        string workspaceRoot,
        IReadOnlyList<CapabilityWorkspaceMutation> mutations,
        CancellationToken cancellationToken)
    {
        var entries = new List<CapabilityWorkspaceTransactionEntry>(
            mutations.Count);
        for (var index = 0; index < mutations.Count; index++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var mutation = mutations[index];
            var target = ResolveUnder(workspaceRoot, mutation.RelativePath);
            var hadOriginal = fileSystem.FileExists(target);
            string? backupPath = null;
            string? originalSha256 = null;
            if (hadOriginal)
            {
                backupPath = TransactionPath("backup", index);
                var original = await ReadBoundedAsync(
                    target,
                    cancellationToken).ConfigureAwait(false);
                originalSha256 = Digest(original.Span);
                await fileSystem.WriteAllBytesAsync(
                    ResolveUnder(workspaceRoot, backupPath),
                    original,
                    cancellationToken).ConfigureAwait(false);
            }

            string? stagePath = null;
            string? desiredSha256 = null;
            if (mutation.DesiredContent is { } desired)
            {
                stagePath = TransactionPath("stage", index);
                desiredSha256 = Digest(desired.Span);
                await fileSystem.WriteAllBytesAsync(
                    ResolveUnder(workspaceRoot, stagePath),
                    desired,
                    cancellationToken).ConfigureAwait(false);
            }

            entries.Add(
                new CapabilityWorkspaceTransactionEntry(
                    mutation.RelativePath,
                    hadOriginal,
                    originalSha256,
                    desiredSha256,
                    stagePath,
                    backupPath));
        }

        return new CapabilityWorkspaceTransactionJournal(
            TransactionVersion,
            entries.ToArray());
    }

    private async ValueTask RestoreAsync(
        string workspaceRoot,
        CapabilityWorkspaceTransactionJournal journal,
        CancellationToken cancellationToken)
    {
        foreach (var entry in journal.Entries.Reverse())
        {
            var target = ResolveUnder(workspaceRoot, entry.RelativePath);
            if (!entry.HadOriginal)
            {
                fileSystem.DeleteFile(target);
                continue;
            }

            if (entry.BackupPath is null)
            {
                throw InvalidTransaction(
                    "A capability transaction backup is missing.",
                    "/transaction/entries");
            }

            var backup = await ReadBoundedAsync(
                ResolveUnder(workspaceRoot, entry.BackupPath),
                cancellationToken).ConfigureAwait(false);
            if (!string.Equals(
                    Digest(backup.Span),
                    entry.OriginalSha256,
                    StringComparison.Ordinal))
            {
                throw InvalidTransaction(
                    "A capability transaction backup differs from its journal digest.",
                    "/transaction/entries");
            }

            await fileSystem.WriteAllBytesAsync(
                target,
                backup,
                cancellationToken).ConfigureAwait(false);
        }
    }

    private async ValueTask<bool> MatchesDesiredStateAsync(
        string workspaceRoot,
        CapabilityWorkspaceTransactionJournal journal,
        CancellationToken cancellationToken)
    {
        foreach (var entry in journal.Entries)
        {
            var target = ResolveUnder(workspaceRoot, entry.RelativePath);
            if (entry.DesiredSha256 is null)
            {
                if (fileSystem.FileExists(target))
                {
                    return false;
                }

                continue;
            }

            if (!fileSystem.FileExists(target))
            {
                return false;
            }

            var bytes = await ReadBoundedAsync(
                target,
                cancellationToken).ConfigureAwait(false);
            if (!string.Equals(
                    Digest(bytes.Span),
                    entry.DesiredSha256,
                    StringComparison.Ordinal))
            {
                return false;
            }
        }

        return true;
    }

    private async ValueTask<CapabilityWorkspaceTransactionJournal>
        ReadJournalAsync(
            string journalPath,
            CancellationToken cancellationToken)
    {
        var bytes = await ReadBoundedAsync(
            journalPath,
            cancellationToken).ConfigureAwait(false);
        try
        {
            return CapabilityWorkspaceTransactionSerializer.Read(bytes.Span);
        }
        catch (JsonException exception)
        {
            throw InvalidTransaction(
                string.Concat(
                    "The capability transaction journal is invalid: ",
                    exception.Message),
                "/transaction");
        }
    }

    private async ValueTask<ReadOnlyMemory<byte>> ReadBoundedAsync(
        string path,
        CancellationToken cancellationToken)
    {
        if (!fileSystem.FileExists(path) ||
            fileSystem.GetFileSize(path) > MaximumTransactionFileBytes)
        {
            throw InvalidTransaction(
                "A capability transaction file is missing or too large.",
                "/transaction");
        }

        return await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
    }

    private static void ValidateMutations(
        IReadOnlyList<CapabilityWorkspaceMutation> mutations)
    {
        var paths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var mutation in mutations)
        {
            ValidateRelativePath(mutation.RelativePath);
            if (mutation.RelativePath.StartsWith(
                    string.Concat(TransactionDirectory, "/"),
                    StringComparison.Ordinal) ||
                !paths.Add(mutation.RelativePath))
            {
                throw InvalidTransaction(
                    "Capability transaction paths must be unique and cannot target transaction state.",
                    "/mutations");
            }
        }
    }

    private static void ValidateJournal(
        CapabilityWorkspaceTransactionJournal journal)
    {
        if (!string.Equals(
                journal.TransactionVersion,
                TransactionVersion,
                StringComparison.Ordinal) ||
            journal.Entries is null ||
            journal.Entries.Length == 0)
        {
            throw InvalidTransaction(
                "The capability transaction journal version or entries are unsupported.",
                "/transaction");
        }

        var paths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var entry in journal.Entries)
        {
            ValidateRelativePath(entry.RelativePath);
            if (!paths.Add(entry.RelativePath) ||
                entry.RelativePath.StartsWith(
                    string.Concat(TransactionDirectory, "/"),
                    StringComparison.Ordinal) ||
                entry.StagePath is not null &&
                !entry.StagePath.StartsWith(
                    string.Concat(TransactionDirectory, "/stage/"),
                    StringComparison.Ordinal) ||
                entry.BackupPath is not null &&
                !entry.BackupPath.StartsWith(
                    string.Concat(TransactionDirectory, "/backup/"),
                    StringComparison.Ordinal) ||
                entry.HadOriginal != (entry.BackupPath is not null) ||
                entry.HadOriginal != (entry.OriginalSha256 is not null) ||
                entry.OriginalSha256 is not null &&
                !IsDigest(entry.OriginalSha256) ||
                (entry.StagePath is null) !=
                (entry.DesiredSha256 is null) ||
                entry.DesiredSha256 is not null &&
                !IsDigest(entry.DesiredSha256))
            {
                throw InvalidTransaction(
                    "The capability transaction journal contains invalid ownership evidence.",
                    "/transaction/entries");
            }

            if (entry.StagePath is not null)
            {
                ValidateRelativePath(entry.StagePath);
            }

            if (entry.BackupPath is not null)
            {
                ValidateRelativePath(entry.BackupPath);
            }
        }
    }

    private static string ResolveUnder(
        string root,
        string relativePath)
    {
        ValidateRelativePath(relativePath);
        var fullRoot = Path.TrimEndingDirectorySeparator(
            Path.GetFullPath(root));
        var fullPath = Path.GetFullPath(
            Path.Combine(
                fullRoot,
                relativePath.Replace(
                    '/',
                    Path.DirectorySeparatorChar)));
        if (!fullPath.StartsWith(
                string.Concat(
                    fullRoot,
                    Path.DirectorySeparatorChar),
                PathComparison()))
        {
            throw InvalidTransaction(
                "A capability transaction path escapes its workspace.",
                "/transaction");
        }

        return fullPath;
    }

    private static void ValidateRelativePath(string value)
    {
        if (string.IsNullOrWhiteSpace(value) ||
            Path.IsPathRooted(value) ||
            value.Contains('\\') ||
            value.Any(char.IsControl) ||
            value.Split('/').Any(
                static segment =>
                    string.IsNullOrWhiteSpace(segment) ||
                    segment is "." or ".."))
        {
            throw InvalidTransaction(
                "A capability transaction path is not a safe normalized relative path.",
                "/transaction");
        }
    }

    private static string TransactionPath(string kind, int index) =>
        string.Concat(
            TransactionDirectory,
            "/",
            kind,
            "/",
            index.ToString("D4", System.Globalization.CultureInfo.InvariantCulture),
            ".bin");

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());

    private static bool IsDigest(string value)
    {
        if (value.Length != 71 ||
            !value.StartsWith("sha256:", StringComparison.Ordinal))
        {
            return false;
        }

        foreach (var character in value.AsSpan(7))
        {
            if (character is not (>= '0' and <= '9') and
                not (>= 'a' and <= 'f'))
            {
                return false;
            }
        }

        return true;
    }

    private static StringComparison PathComparison() =>
        OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    private static CapabilityOperationException InvalidTransaction(
        string message,
        string path) =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.InvalidCapabilityInitialization,
            path,
            message);
}
