using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public sealed record AdapterPublicationRecoveryState(string TransactionPath, IReadOnlyList<string> LogicalPaths);

public sealed class AdapterPublicationRecovery
{
    public IReadOnlyList<AdapterPublicationRecoveryState> Inspect(string workspaceRoot)
    {
        string root = StagingRoot(workspaceRoot);
        if (!Directory.Exists(root)) return Array.Empty<AdapterPublicationRecoveryState>();
        List<AdapterPublicationRecoveryState> states = new();
        foreach (string transaction in Directory.EnumerateDirectories(root).OrderBy(static path => path, StringComparer.Ordinal))
        {
            if ((File.GetAttributes(transaction) & FileAttributes.ReparsePoint) != 0)
                throw new AdapterPublicationException("An adapter staging transaction is a reparse point.");
            JsonObject journal = ReadJournal(transaction);
            string[] logicalPaths = journal["entries"]!.AsArray().OfType<JsonObject>()
                .Select(static entry => entry["logicalPath"]!.GetValue<string>())
                .ToArray();
            LogicalPathPolicy.ValidateDistinct(logicalPaths);
            states.Add(new AdapterPublicationRecoveryState(transaction, logicalPaths));
        }

        return states;
    }

    public void Rollback(string workspaceRoot, AdapterPublicationRecoveryState state)
    {
        string stagingRoot = StagingRoot(workspaceRoot);
        string transaction = Path.GetFullPath(state.TransactionPath);
        if (!transaction.StartsWith(stagingRoot.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, Comparison)
            || !Directory.Exists(transaction)
            || (File.GetAttributes(transaction) & FileAttributes.ReparsePoint) != 0)
            throw new AdapterPublicationException("The adapter staging recovery target is unsafe or unavailable.");
        JsonObject journal = ReadJournal(transaction);
        JsonObject[] entries = journal["entries"]!.AsArray().OfType<JsonObject>().ToArray();
        foreach (JsonObject entry in entries)
        {
            string logicalPath = entry["logicalPath"]!.GetValue<string>();
            string destination = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            string outputDigest = entry["outputDigest"]!.GetValue<string>();
            string? priorDigest = entry["priorDigest"]?.GetValue<string>();
            string? backupName = entry["backupName"]?.GetValue<string>();
            string? currentDigest = File.Exists(destination) ? Digest(File.ReadAllBytes(destination)) : null;
            string? backup = backupName is null ? null : Path.Combine(transaction, backupName);
            if (backup is not null && File.Exists(backup))
            {
                if (!string.Equals(Digest(File.ReadAllBytes(backup)), priorDigest, StringComparison.Ordinal)
                    || (currentDigest is not null && !string.Equals(currentDigest, outputDigest, StringComparison.Ordinal)))
                    throw new AdapterPublicationException("Recovery refuses changed destination or backup bytes.");
            }
            else if (priorDigest is null)
            {
                if (currentDigest is not null && !string.Equals(currentDigest, outputDigest, StringComparison.Ordinal))
                    throw new AdapterPublicationException("Recovery refuses an unowned destination.");
            }
            else if (!string.Equals(currentDigest, priorDigest, StringComparison.Ordinal))
            {
                throw new AdapterPublicationException("Recovery cannot prove the prior destination bytes.");
            }
        }

        foreach (JsonObject entry in entries.Reverse())
        {
            string logicalPath = entry["logicalPath"]!.GetValue<string>();
            string destination = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            string? priorDigest = entry["priorDigest"]?.GetValue<string>();
            string? backupName = entry["backupName"]?.GetValue<string>();
            string? backup = backupName is null ? null : Path.Combine(transaction, backupName);
            if (backup is not null && File.Exists(backup))
            {
                if (File.Exists(destination)) File.Delete(destination);
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                File.Move(backup, destination);
            }
            else if (priorDigest is null)
            {
                if (File.Exists(destination)) File.Delete(destination);
            }
        }

        Directory.Delete(transaction, recursive: true);
    }

    private static JsonObject ReadJournal(string transaction)
    {
        string path = Path.Combine(transaction, "staging-state.json");
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new AdapterPublicationException("Adapter staging has no trustworthy recovery journal.");
        JsonObject journal = CanonicalDocument.Parse(File.ReadAllBytes(path)).AsObject();
        if (journal["schema"]?.GetValue<string>() != "program-kit.spec-kit-adapter-publication-staging/v1"
            || journal["ownership"]?.GetValue<string>() != "adapter-generated-owned"
            || journal["entries"] is not JsonArray)
            throw new AdapterPublicationException("Adapter staging recovery journal is invalid.");
        return journal;
    }

    private static string StagingRoot(string workspaceRoot) => LogicalPathPolicy.Resolve(workspaceRoot, ".program-kit/adapter-staging");

    private static string Digest(byte[] bytes) => "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(bytes)).ToLowerInvariant();

    private static StringComparison Comparison => OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
}
