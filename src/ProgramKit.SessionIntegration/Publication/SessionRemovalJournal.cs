using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed record SessionRemovalResult(
    IReadOnlyList<OperationChange> Changes,
    string JournalLogicalPath,
    string JournalDigest,
    string ReceiptLogicalPath,
    string ReceiptDigest);

public interface ISessionRemovalObserver
{
    void Removed(int completedCount, string logicalPath);
}

public sealed class SessionRemovalJournal
{
    private readonly ISessionRemovalObserver? observer;

    public SessionRemovalJournal(ISessionRemovalObserver? observer = null)
    {
        this.observer = observer;
    }

    public SessionRemovalResult Remove(string workspaceRoot, string providerName, SessionInstallationRecord record)
    {
        string workspace = Path.GetFullPath(workspaceRoot);
        string stateRoot = LogicalPaths.ResolveInside(Path.Combine(workspace, ".program-kit"), $"session-integrations/{providerName.ToLowerInvariant()}");
        string recordPath = Path.Combine(stateRoot, "installation.json");
        string journalPath = Path.Combine(stateRoot, "removal.journal.json");
        string receiptPath = Path.Combine(stateRoot, "removal.json");
        string backupRoot = Path.Combine(stateRoot, "removal-backups", Digests.Sha256(Encoding.UTF8.GetBytes(record.InstallationIdentity.StableKey))["sha256:".Length..]);
        string lockPath = Path.Combine(workspace, ".program-kit", "workspace.lock");

        PreparedRemoval[] removals = record.ProjectionSet
            .OrderBy(static item => item.LogicalPath, StringComparer.Ordinal)
            .Select(item => Prepare(workspace, item.LogicalPath, item.ContentDigest))
            .ToArray();
        if (!File.Exists(recordPath)) throw new InvalidDataException("The exact admitted installation record is unavailable.");
        Directory.CreateDirectory(stateRoot);
        using SessionWorkspaceLock workspaceLock = SessionWorkspaceLock.Acquire(lockPath);
        foreach (PreparedRemoval removal in removals)
        {
            if (!File.Exists(removal.TargetPath) || !string.Equals(Digests.Sha256(File.ReadAllBytes(removal.TargetPath)), removal.ExpectedDigest, StringComparison.Ordinal))
                throw new InvalidDataException($"Removal refused drifted or missing admitted content at {removal.LogicalPath}.");
        }
        Directory.CreateDirectory(backupRoot);
        foreach (PreparedRemoval removal in removals)
        {
            string backup = LogicalPaths.ResolveInside(backupRoot, removal.LogicalPath);
            Directory.CreateDirectory(Path.GetDirectoryName(backup)!);
            File.Copy(removal.TargetPath, backup, overwrite: false);
        }
        File.Copy(recordPath, Path.Combine(backupRoot, "installation.json"), overwrite: false);

        JsonObject journal = new()
        {
            ["schema"] = "program-kit.session-removal-journal/v1",
            ["installationIdentity"] = record.InstallationIdentity.StableKey,
            ["state"] = "prepared",
            ["operations"] = new JsonArray(removals.Select(static item => new JsonObject { ["logicalPath"] = item.LogicalPath, ["expectedDigest"] = item.ExpectedDigest }).ToArray()),
            ["completedOperations"] = new JsonArray(),
        };
        WriteDurable(journalPath, CanonicalJson.Encode(journal));
        List<PreparedRemoval> completed = new();
        try
        {
            journal["state"] = "removing";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            foreach (PreparedRemoval removal in removals)
            {
                File.Delete(removal.TargetPath);
                completed.Add(removal);
                ((JsonArray)journal["completedOperations"]!).Add(removal.LogicalPath);
                WriteDurable(journalPath, CanonicalJson.Encode(journal));
                observer?.Removed(completed.Count, removal.LogicalPath);
            }

            File.Delete(recordPath);
            JsonObject receipt = new()
            {
                ["schema"] = "program-kit.session-removal-receipt/v1",
                ["installationIdentity"] = record.InstallationIdentity.StableKey,
                ["recordDigest"] = record.RecordDigest,
                ["state"] = "removed",
                ["removed"] = new JsonArray(removals.Select(static item => new JsonObject { ["logicalPath"] = item.LogicalPath, ["digest"] = item.ExpectedDigest }).ToArray()),
            };
            WriteDurable(receiptPath, CanonicalJson.Encode(receipt));
            journal["state"] = "committed";
            journal["receiptDigest"] = Digests.Sha256(File.ReadAllBytes(receiptPath));
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            DeleteInternalDirectory(backupRoot, stateRoot);
            return new(
                removals.Select(static item => new OperationChange("removed", item.LogicalPath, EffectState.Committed)).ToArray(),
                Relative(workspace, journalPath), Digests.Sha256(File.ReadAllBytes(journalPath)),
                Relative(workspace, receiptPath), Digests.Sha256(File.ReadAllBytes(receiptPath)));
        }
        catch
        {
            bool restored = Restore(completed, backupRoot, recordPath);
            journal["state"] = restored ? "rolled-back" : "incomplete";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            if (restored) DeleteInternalDirectory(backupRoot, stateRoot);
            throw;
        }
    }

    private static PreparedRemoval Prepare(string workspace, string logicalPath, string expectedDigest) =>
        new(LogicalPaths.Normalize(logicalPath), LogicalPaths.ResolveInside(workspace, logicalPath), expectedDigest);

    private static bool Restore(IEnumerable<PreparedRemoval> completed, string backupRoot, string recordPath)
    {
        try
        {
            foreach (PreparedRemoval removal in completed.Reverse())
            {
                string backup = LogicalPaths.ResolveInside(backupRoot, removal.LogicalPath);
                Directory.CreateDirectory(Path.GetDirectoryName(removal.TargetPath)!);
                File.Copy(backup, removal.TargetPath, overwrite: false);
            }
            if (!File.Exists(recordPath)) File.Copy(Path.Combine(backupRoot, "installation.json"), recordPath, overwrite: false);
            return true;
        }
        catch { return false; }
    }

    private static void WriteDurable(string path, byte[] bytes)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using FileStream stream = new(path, FileMode.Create, FileAccess.Write, FileShare.Read);
        stream.Write(bytes);
        stream.Flush(flushToDisk: true);
    }

    private static void DeleteInternalDirectory(string path, string stateRoot)
    {
        string root = Path.GetFullPath(stateRoot).TrimEnd(Path.DirectorySeparatorChar);
        string target = Path.GetFullPath(path);
        if (!target.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Refusing removal cleanup outside the owned state namespace.");
        if (Directory.Exists(target)) Directory.Delete(target, recursive: true);
    }

    private sealed class SessionWorkspaceLock : IDisposable
    {
        private readonly string path;
        private readonly FileStream stream;
        private bool disposed;

        private SessionWorkspaceLock(string path, FileStream stream)
        {
            this.path = path;
            this.stream = stream;
        }

        public static SessionWorkspaceLock Acquire(string path) => new(path, new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None));

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            stream.Dispose();
            File.Delete(path);
        }
    }

    private static string Relative(string workspace, string path) => LogicalPaths.Normalize(Path.GetRelativePath(workspace, path).Replace('\\', '/'));
    private sealed record PreparedRemoval(string LogicalPath, string TargetPath, string ExpectedDigest);
}
