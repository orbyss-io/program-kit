using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Publication;

public sealed record PublicationResult(
    IReadOnlyList<OperationChange> Changes,
    IReadOnlyList<string> CompletedPaths,
    string LiveStateDigest,
    string JournalDigest);

public interface IPublicationFaultInjector
{
    void Observe(string boundary, int completedOperations);
}

public sealed class NoPublicationFaults : IPublicationFaultInjector
{
    public void Observe(string boundary, int completedOperations) { }
}

public sealed class PublicationInterruptedException : IOException
{
    public PublicationInterruptedException(string message, EffectState provenEffect, string journalPath, Exception innerException)
        : base(message, innerException)
    {
        ProvenEffect = provenEffect;
        JournalPath = journalPath;
    }

    public EffectState ProvenEffect { get; }

    public string JournalPath { get; }
}

public sealed class RecoverablePublisher
{
    private readonly IPublicationFaultInjector faults;

    public RecoverablePublisher(IPublicationFaultInjector? faults = null)
    {
        this.faults = faults ?? new NoPublicationFaults();
    }

    public PublicationResult Publish(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        ConstructionMode mode,
        string expectedLiveState)
    {
        string stateRoot = Path.Combine(workspaceRoot, ".program-kit");
        Directory.CreateDirectory(stateRoot);
        string journalPath = Path.Combine(stateRoot, "publication.journal.json");
        RefuseUnresolvedJournal(journalPath);

        string lockPath = Path.Combine(stateRoot, "workspace.lock");
        using FileStream workspaceLock = new(lockPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        string observedBefore = LiveState.Compute(workspaceRoot, candidate.Artifacts);
        if (!string.Equals(observedBefore, expectedLiveState, StringComparison.Ordinal))
        {
            throw new IOException("The exact live publication precondition changed before publication.");
        }

        JsonArray operations = new(candidate.Artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).Select(artifact =>
        {
            string target = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
            string? existing = File.Exists(target) ? Digests.Sha256(File.ReadAllBytes(target)) : null;
            JsonObject operation = new()
            {
                ["identity"] = OperationIdentity(artifact.LogicalPath, existing, artifact.Digest),
                ["kind"] = existing is null ? "create" : "replace",
                ["logicalPath"] = artifact.LogicalPath,
                ["newDigest"] = artifact.Digest,
                ["ownership"] = ContractJson.Kebab(artifact.Ownership),
            };
            if (existing is not null)
            {
                operation["expectedDigest"] = existing;
            }

            return operation;
        }).ToArray());
        JsonObject journal = new()
        {
            ["schema"] = "program-kit.publication-journal/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["constructionIdentity"] = candidate.ConstructionIdentity,
            ["expectedLiveState"] = expectedLiveState,
            ["operations"] = operations,
            ["completedOperations"] = new JsonArray(),
            ["state"] = "prepared",
        };
        WriteDurable(journalPath, CanonicalJson.Encode(journal));

        List<OperationChange> changes = new();
        List<string> completed = new();
        string backupRoot = Path.Combine(stateRoot, "backups", candidate.ConstructionIdentity["sha256:".Length..]);
        try
        {
            faults.Observe("journal-prepared", 0);
            string observedUnderLock = LiveState.Compute(workspaceRoot, candidate.Artifacts);
            if (!string.Equals(observedUnderLock, expectedLiveState, StringComparison.Ordinal))
            {
                throw new IOException("The exact live publication precondition changed while acquiring publication authority.");
            }

            journal["state"] = "publishing";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            faults.Observe("publishing-started", 0);
            foreach (ArtifactManifestEntry artifact in candidate.Artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal))
            {
                string source = LogicalPaths.ResolveInside(candidate.CandidateRoot, artifact.LogicalPath);
                string target = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
                bool existed = File.Exists(target);
                string? existingDigest = existed ? Digests.Sha256(File.ReadAllBytes(target)) : null;
                string operationIdentity = OperationIdentity(artifact.LogicalPath, existingDigest, artifact.Digest);

                if (existed && string.Equals(existingDigest, artifact.Digest, StringComparison.Ordinal))
                {
                    if (mode == ConstructionMode.New)
                    {
                        throw new IOException($"Publication collision at {artifact.LogicalPath}.");
                    }

                    changes.Add(new OperationChange("unchanged", artifact.LogicalPath, EffectState.Committed));
                    completed.Add(artifact.LogicalPath);
                    ((JsonArray)journal["completedOperations"]!).Add(operationIdentity);
                    WriteDurable(journalPath, CanonicalJson.Encode(journal));
                    faults.Observe("operation-recorded", completed.Count);
                    continue;
                }

                if (existed)
                {
                    if (mode != ConstructionMode.Repair || artifact.Ownership != ArtifactOwnership.GeneratedOwned)
                    {
                        throw new IOException($"Publication collision at {artifact.LogicalPath}.");
                    }

                    string backup = LogicalPaths.ResolveInside(backupRoot, artifact.LogicalPath);
                    Directory.CreateDirectory(Path.GetDirectoryName(backup)!);
                    File.Move(target, backup, overwrite: false);
                    faults.Observe("backup-created", completed.Count);
                }

                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                string temporary = $"{target}.program-kit-{candidate.ConstructionIdentity["sha256:".Length..12]}.tmp";
                File.Copy(source, temporary, overwrite: false);
                File.Move(temporary, target, overwrite: false);
                faults.Observe("live-write-completed", completed.Count);
                string observed = Digests.Sha256(File.ReadAllBytes(target));
                if (!string.Equals(observed, artifact.Digest, StringComparison.Ordinal))
                {
                    throw new IOException($"Post-publication digest mismatch at {artifact.LogicalPath}.");
                }

                completed.Add(artifact.LogicalPath);
                changes.Add(new OperationChange(existed ? "replaced" : "created", artifact.LogicalPath, EffectState.Committed));
                ((JsonArray)journal["completedOperations"]!).Add(operationIdentity);
                WriteDurable(journalPath, CanonicalJson.Encode(journal));
                faults.Observe("operation-recorded", completed.Count);
            }

            string liveStateDigest = LiveState.Compute(workspaceRoot, candidate.Artifacts);
            string expectedPublishedState = Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', candidate.Artifacts
                .OrderBy(static item => item.LogicalPath, StringComparer.Ordinal)
                .Select(static item => $"{item.LogicalPath}:{item.Digest}"))));
            if (!string.Equals(liveStateDigest, expectedPublishedState, StringComparison.Ordinal))
            {
                throw new IOException("The published live-state digest is not the complete candidate state.");
            }

            faults.Observe("before-journal-commit", completed.Count);
            journal["state"] = "committed";
            journal["observedLiveState"] = liveStateDigest;
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            return new PublicationResult(changes, completed, liveStateDigest, Digests.Sha256(File.ReadAllBytes(journalPath)));
        }
        catch (Exception exception)
        {
            string interruptedFrom = journal["state"]?.GetValue<string>() ?? "unknown";
            journal["state"] = "incomplete";
            journal["interruptedFrom"] = interruptedFrom;
            journal["observedLiveState"] = LiveState.Compute(workspaceRoot, candidate.Artifacts);
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            EffectState effect = string.Equals(interruptedFrom, "prepared", StringComparison.Ordinal)
                ? EffectState.CandidateOnly : EffectState.Indeterminate;
            throw new PublicationInterruptedException("Publication was interrupted and requires separately authorized recovery.", effect, journalPath, exception);
        }
        finally
        {
            workspaceLock.Dispose();
            File.Delete(lockPath);
        }
    }

    private static void RefuseUnresolvedJournal(string journalPath)
    {
        if (!File.Exists(journalPath))
        {
            return;
        }

        JsonObject existing = CanonicalJson.Parse(File.ReadAllBytes(journalPath)) as JsonObject
            ?? throw new IOException("The existing publication journal is invalid.");
        string stateRoot = Path.GetDirectoryName(journalPath) ?? throw new IOException("The publication state root is unavailable.");
        string workspaceRoot = Path.GetDirectoryName(stateRoot) ?? throw new IOException("The publication workspace root is unavailable.");
        PublicationRecoveryState? observed = new PublicationRecovery().Inspect(workspaceRoot);
        if (observed is not null && observed.State is not ("admitted" or "rolled-back"))
        {
            throw new IOException("An unresolved publication journal requires separately authorized recovery.");
        }
    }

    private static string OperationIdentity(string logicalPath, string? expected, string next) =>
        Digests.Sha256(System.Text.Encoding.UTF8.GetBytes($"{logicalPath}\n{expected ?? "missing"}\n{next}"));

    internal static void WriteDurable(string path, byte[] bytes)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using FileStream stream = new(path, FileMode.Create, FileAccess.Write, FileShare.Read);
        stream.Write(bytes);
        stream.Flush(flushToDisk: true);
    }
}
