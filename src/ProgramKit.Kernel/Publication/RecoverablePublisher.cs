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
    string LiveStateDigest);

public sealed class RecoverablePublisher
{
    public PublicationResult Publish(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        ConstructionMode mode)
    {
        List<NamespacedArtifact> artifacts = new();
        foreach (ArtifactManifestEntry artifact in candidate.Artifacts)
        {
            string source = LogicalPaths.ResolveInside(candidate.CandidateRoot, artifact.LogicalPath);
            string target = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
            string? expected = null;
            if (File.Exists(target))
            {
                string observed = Digests.Sha256(File.ReadAllBytes(target));
                bool same = string.Equals(observed, artifact.Digest, StringComparison.Ordinal);
                if (artifact.Ownership == ArtifactOwnership.GeneratedOwned)
                {
                    if (mode != ConstructionMode.Repair) throw new IOException($"Publication collision at {artifact.LogicalPath}.");
                    expected = observed;
                }
                else if (!same) throw new IOException($"Publication collision at {artifact.LogicalPath}.");
            }

            artifacts.Add(new NamespacedArtifact(artifact.LogicalPath, File.ReadAllBytes(source), expected));
        }

        NamespacedPublicationResult result = new NamespacedArtifactSetPublisher().Publish(workspaceRoot, string.Empty, candidate.ConstructionIdentity, artifacts);
        return new PublicationResult(result.Changes, result.CompletedPaths, result.LiveStateDigest);
    }

    public PublicationResult PublishLegacy(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        ConstructionMode mode)
    {
        string stateRoot = Path.Combine(workspaceRoot, ".program-kit");
        Directory.CreateDirectory(stateRoot);
        string lockPath = Path.Combine(stateRoot, "workspace.lock");
        using FileStream workspaceLock = new(lockPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        string journalPath = Path.Combine(stateRoot, "publication.journal.json");
        JsonObject journal = new()
        {
            ["schema"] = "program-kit.publication-journal/v1",
            ["constructionIdentity"] = candidate.ConstructionIdentity,
            ["state"] = "prepared",
            ["operations"] = new JsonArray(candidate.Artifacts.Select(static item => JsonValue.Create(item.LogicalPath)).ToArray()),
            ["completedOperations"] = new JsonArray(),
        };
        WriteDurable(journalPath, CanonicalJson.Encode(journal));

        List<OperationChange> changes = new();
        List<string> completed = new();
        string backupRoot = Path.Combine(stateRoot, "backups", candidate.ConstructionIdentity["sha256:".Length..]);
        try
        {
            journal["state"] = "publishing";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            foreach (ArtifactManifestEntry artifact in candidate.Artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal))
            {
                string source = LogicalPaths.ResolveInside(candidate.CandidateRoot, artifact.LogicalPath);
                string target = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
                if (string.Equals(Path.GetFullPath(source), Path.GetFullPath(target), StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                bool existed = File.Exists(target);
                if (File.Exists(target))
                {
                    if (artifact.Ownership != ArtifactOwnership.GeneratedOwned
                        && string.Equals(Digests.Sha256(File.ReadAllBytes(target)), artifact.Digest, StringComparison.Ordinal))
                    {
                        changes.Add(new OperationChange("unchanged", artifact.LogicalPath, EffectState.Committed));
                        continue;
                    }

                    if (mode != ConstructionMode.Repair || artifact.Ownership != ArtifactOwnership.GeneratedOwned)
                    {
                        throw new IOException($"Publication collision at {artifact.LogicalPath}.");
                    }

                    string backup = LogicalPaths.ResolveInside(backupRoot, artifact.LogicalPath);
                    Directory.CreateDirectory(Path.GetDirectoryName(backup)!);
                    File.Move(target, backup, overwrite: false);
                }

                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                string temporary = $"{target}.program-kit-{candidate.ConstructionIdentity["sha256:".Length..12]}.tmp";
                File.Copy(source, temporary, overwrite: false);
                File.Move(temporary, target, overwrite: false);
                string observed = Digests.Sha256(File.ReadAllBytes(target));
                if (!string.Equals(observed, artifact.Digest, StringComparison.Ordinal))
                {
                    throw new IOException($"Post-publication digest mismatch at {artifact.LogicalPath}.");
                }

                completed.Add(artifact.LogicalPath);
                changes.Add(new OperationChange(existed ? "replaced" : "created", artifact.LogicalPath, EffectState.Committed));
                ((JsonArray)journal["completedOperations"]!).Add(artifact.LogicalPath);
                WriteDurable(journalPath, CanonicalJson.Encode(journal));
            }

            journal["state"] = "committed";
            string liveStateDigest = Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', candidate.Artifacts.Select(static item => $"{item.LogicalPath}:{item.Digest}"))));
            journal["observedLiveState"] = liveStateDigest;
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            return new PublicationResult(changes, completed, liveStateDigest);
        }
        catch
        {
            journal["state"] = "incomplete";
            WriteDurable(journalPath, CanonicalJson.Encode(journal));
            throw;
        }
        finally
        {
            workspaceLock.Dispose();
            File.Delete(lockPath);
        }
    }

    private static void WriteDurable(string path, byte[] bytes)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using FileStream stream = new(path, FileMode.Create, FileAccess.Write, FileShare.Read);
        stream.Write(bytes);
        stream.Flush(flushToDisk: true);
    }
}
