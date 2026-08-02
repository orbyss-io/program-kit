using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Artifacts;

public sealed record NamespacedArtifact(string LogicalPath, byte[] Content, string? ExpectedLiveDigest = null);

public sealed record NamespacedPublicationResult(
    IReadOnlyList<OperationChange> Changes,
    IReadOnlyList<string> CompletedPaths,
    string LiveStateDigest,
    string JournalLogicalPath,
    string JournalDigest);

public interface IArtifactPublicationObserver
{
    void Published(int completedCount, string logicalPath);
}

public sealed class NamespacedArtifactSetPublisher
{
    private readonly IArtifactPublicationObserver? observer;

    public NamespacedArtifactSetPublisher(IArtifactPublicationObserver? observer = null)
    {
        this.observer = observer;
    }

    public NamespacedPublicationResult Publish(
        string workspaceRoot,
        string stateNamespace,
        string transactionIdentity,
        IReadOnlyList<NamespacedArtifact> artifacts)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(transactionIdentity);
        string workspace = Path.GetFullPath(workspaceRoot);
        string normalizedNamespace = string.IsNullOrWhiteSpace(stateNamespace) ? string.Empty : LogicalPaths.Normalize(stateNamespace);
        string programKitRoot = Path.Combine(workspace, ".program-kit");
        string stateRoot = string.IsNullOrEmpty(normalizedNamespace) ? programKitRoot : LogicalPaths.ResolveInside(programKitRoot, normalizedNamespace);
        string stagingParent = Path.Combine(stateRoot, "staging");
        if (Directory.Exists(stagingParent) && Directory.EnumerateFileSystemEntries(stagingParent).Any())
            throw new InvalidOperationException("Stale publication staging exists; blind retry is refused.");

        IReadOnlyList<PreparedArtifact> ordered = Prepare(workspace, artifacts);
        string journalPath = Path.Combine(stateRoot, "publication.journal.json");
        if (ordered.All(static value => value.Unchanged) && File.Exists(journalPath))
        {
            string exactLiveState = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', ordered.Select(static item => $"{item.LogicalPath}:{item.ContentDigest}"))));
            return new NamespacedPublicationResult(
                ordered.Select(static item => new OperationChange("unchanged", item.LogicalPath, EffectState.None)).ToArray(),
                Array.Empty<string>(),
                exactLiveState,
                LogicalPaths.Normalize(Path.GetRelativePath(workspace, journalPath).Replace('\\', '/')),
                Digests.Sha256(File.ReadAllBytes(journalPath)));
        }

        Directory.CreateDirectory(stateRoot);
        string lockPath = Path.Combine(programKitRoot, "workspace.lock");
        using FileStream workspaceLock = new(lockPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        Preflight(ordered);

        string transactionDirectory = Digests.Sha256(Encoding.UTF8.GetBytes(transactionIdentity))["sha256:".Length..];
        string stagingRoot = Path.Combine(stagingParent, transactionDirectory);
        string backupRoot = Path.Combine(stateRoot, "backups", transactionDirectory);
        Directory.CreateDirectory(stagingRoot);
        foreach (PreparedArtifact artifact in ordered.Where(static value => !value.Unchanged))
        {
            string staged = LogicalPaths.ResolveInside(stagingRoot, artifact.LogicalPath);
            Directory.CreateDirectory(Path.GetDirectoryName(staged)!);
            WriteDurable(staged, artifact.Content);
            if (!string.Equals(Digests.Sha256(File.ReadAllBytes(staged)), artifact.ContentDigest, StringComparison.Ordinal))
                throw new IOException($"Staged artifact digest mismatch at {artifact.LogicalPath}.");
        }

        JsonObject journal = Journal(transactionIdentity, normalizedNamespace, ordered, "prepared");
        WriteDurable(journalPath, CanonicalJson.Encode(journal));
        List<PreparedArtifact> completed = new();
        try
        {
            journal["state"] = "publishing";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            foreach (PreparedArtifact artifact in ordered.Where(static value => !value.Unchanged))
            {
                if (artifact.Existed)
                {
                    string backup = LogicalPaths.ResolveInside(backupRoot, artifact.LogicalPath);
                    Directory.CreateDirectory(Path.GetDirectoryName(backup)!);
                    File.Move(artifact.TargetPath, backup, overwrite: false);
                }

                Directory.CreateDirectory(Path.GetDirectoryName(artifact.TargetPath)!);
                string staged = LogicalPaths.ResolveInside(stagingRoot, artifact.LogicalPath);
                File.Move(staged, artifact.TargetPath, overwrite: false);
                if (!string.Equals(Digests.Sha256(File.ReadAllBytes(artifact.TargetPath)), artifact.ContentDigest, StringComparison.Ordinal))
                    throw new IOException($"Post-publication digest mismatch at {artifact.LogicalPath}.");

                completed.Add(artifact);
                ((JsonArray)journal["completedOperations"]!).Add(artifact.LogicalPath);
                WriteDurable(journalPath, CanonicalJson.Encode(journal));
                observer?.Published(completed.Count, artifact.LogicalPath);
            }

            string liveStateDigest = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', ordered.Select(static item => $"{item.LogicalPath}:{item.ContentDigest}"))));
            journal["state"] = "committed";
            journal["observedLiveState"] = liveStateDigest;
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            DeleteInternalDirectory(stagingRoot, stateRoot);
            DeleteInternalDirectory(backupRoot, stateRoot);
            string journalDigest = Digests.Sha256(File.ReadAllBytes(journalPath));
            return new NamespacedPublicationResult(
                ordered.Select(static item => new OperationChange(item.Unchanged ? "unchanged" : item.Existed ? "replaced" : "created", item.LogicalPath, EffectState.Committed)).ToArray(),
                completed.Select(static item => item.LogicalPath).ToArray(),
                liveStateDigest,
                LogicalPaths.Normalize(Path.GetRelativePath(workspace, journalPath).Replace('\\', '/')),
                journalDigest);
        }
        catch
        {
            bool rollbackComplete = Rollback(completed, backupRoot);
            journal["state"] = rollbackComplete ? "rolled-back" : "incomplete";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            if (rollbackComplete) DeleteInternalDirectory(stagingRoot, stateRoot);
            throw;
        }
        finally
        {
            workspaceLock.Dispose();
            File.Delete(lockPath);
        }
    }

    private static IReadOnlyList<PreparedArtifact> Prepare(string workspace, IReadOnlyList<NamespacedArtifact> artifacts)
    {
        if (artifacts.Count == 0) throw new ArgumentException("A publication set must contain at least one artifact.", nameof(artifacts));
        List<PreparedArtifact> prepared = new();
        HashSet<string> paths = new(StringComparer.Ordinal);
        foreach (NamespacedArtifact artifact in artifacts)
        {
            string logicalPath = LogicalPaths.Normalize(artifact.LogicalPath);
            if (!paths.Add(logicalPath)) throw new ArgumentException($"Duplicate publication path: {logicalPath}", nameof(artifacts));
            byte[] content = artifact.Content.ToArray();
            string target = LogicalPaths.ResolveInside(workspace, logicalPath);
            bool existed = File.Exists(target);
            string? observed = existed ? Digests.Sha256(File.ReadAllBytes(target)) : null;
            string digest = Digests.Sha256(content);
            prepared.Add(new PreparedArtifact(logicalPath, content, target, digest, artifact.ExpectedLiveDigest, existed, string.Equals(observed, digest, StringComparison.Ordinal), observed));
        }

        return prepared.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ToArray();
    }

    private static void Preflight(IReadOnlyList<PreparedArtifact> artifacts)
    {
        foreach (PreparedArtifact artifact in artifacts)
        {
            if (!artifact.Existed || artifact.Unchanged) continue;
            if (artifact.ExpectedLiveDigest is null || !string.Equals(artifact.ExpectedLiveDigest, artifact.ObservedLiveDigest, StringComparison.Ordinal))
                throw new IOException($"Publication collision at {artifact.LogicalPath}.");
        }
    }

    private static bool Rollback(IEnumerable<PreparedArtifact> completed, string backupRoot)
    {
        try
        {
            foreach (PreparedArtifact artifact in completed.Reverse())
            {
                if (File.Exists(artifact.TargetPath)) File.Delete(artifact.TargetPath);
                if (!artifact.Existed) continue;
                string backup = LogicalPaths.ResolveInside(backupRoot, artifact.LogicalPath);
                Directory.CreateDirectory(Path.GetDirectoryName(artifact.TargetPath)!);
                File.Move(backup, artifact.TargetPath, overwrite: false);
            }

            return true;
        }
        catch { return false; }
    }

    private static JsonObject Journal(string transactionIdentity, string stateNamespace, IReadOnlyList<PreparedArtifact> artifacts, string state) => new()
    {
        ["schema"] = "program-kit.namespaced-publication-journal/v1",
        ["transactionIdentity"] = transactionIdentity,
        ["namespace"] = stateNamespace,
        ["state"] = state,
        ["operations"] = new JsonArray(artifacts.Select(static item => new JsonObject { ["logicalPath"] = item.LogicalPath, ["digest"] = item.ContentDigest }).ToArray()),
        ["completedOperations"] = new JsonArray(),
    };

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
        if (!target.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Refusing to clean publication data outside the owned namespace.");
        if (Directory.Exists(target)) Directory.Delete(target, recursive: true);
    }

    private sealed record PreparedArtifact(
        string LogicalPath,
        byte[] Content,
        string TargetPath,
        string ContentDigest,
        string? ExpectedLiveDigest,
        bool Existed,
        bool Unchanged,
        string? ObservedLiveDigest);
}
