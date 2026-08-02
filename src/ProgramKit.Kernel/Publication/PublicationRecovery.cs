using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Publication;

public enum PublicationRecoveryStrategy
{
    Complete,
    Rollback,
}

public sealed record PublicationRecoveryState(string State, EffectState Effect, string ConstructionIdentity, string JournalDigest);

public sealed class PublicationRecovery
{
    public PublicationRecoveryState? Inspect(string workspaceRoot)
    {
        string journalPath = Path.Combine(workspaceRoot, ".program-kit", "publication.journal.json");
        if (!File.Exists(journalPath))
        {
            return null;
        }

        JsonObject journal = Read(journalPath);
        string rawState = Required(journal, "state");
        string journalDigest = Digests.Sha256(File.ReadAllBytes(journalPath));
        (string State, EffectState Effect) observed = rawState switch
        {
            "committed" when HasExactAdmissionReceipt(workspaceRoot, journal, journalDigest) => ("admitted", EffectState.Committed),
            "committed" => ("published-unadmitted", EffectState.Indeterminate),
            "prepared" => ("prepared", EffectState.CandidateOnly),
            "incomplete" when string.Equals(journal["interruptedFrom"]?.GetValue<string>(), "prepared", StringComparison.Ordinal)
                => ("incomplete", EffectState.CandidateOnly),
            "publishing" or "incomplete" => (rawState, EffectState.Indeterminate),
            "rolled-back" => ("rolled-back", EffectState.None),
            _ => ("unknown", EffectState.Indeterminate),
        };
        return new PublicationRecoveryState(
            observed.State,
            observed.Effect,
            Required(journal, "constructionIdentity"),
            journalDigest);
    }

    public PublicationRecoveryState Recover(string workspaceRoot, PublicationRecoveryStrategy strategy, ConstructionMode authorizedMode)
    {
        if (authorizedMode != ConstructionMode.Repair)
        {
            throw new UnauthorizedAccessException("Publication recovery requires an explicitly authorized repair construction.");
        }

        PublicationRecoveryState observed = Inspect(workspaceRoot)
            ?? throw new FileNotFoundException("The publication journal is unavailable.");
        if (observed.State is not ("prepared" or "publishing" or "incomplete" or "published-unadmitted"))
        {
            throw new InvalidOperationException("The publication journal does not require recovery.");
        }

        string journalPath = Path.Combine(workspaceRoot, ".program-kit", "publication.journal.json");
        JsonObject journal = Read(journalPath);
        JsonArray operations = journal["operations"] as JsonArray
            ?? throw new InvalidDataException("The publication journal operations are unavailable.");

        if (strategy == PublicationRecoveryStrategy.Complete)
        {
            foreach (JsonObject operation in operations.Cast<JsonObject>())
            {
                string path = LogicalPaths.ResolveInside(workspaceRoot, Required(operation, "logicalPath"));
                if (!File.Exists(path)
                    || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0
                    || !string.Equals(Digests.Sha256(File.ReadAllBytes(path)), Required(operation, "newDigest"), StringComparison.Ordinal))
                {
                    throw new IOException("Completion recovery requires every planned live byte to already be exact.");
                }
            }

            journal["state"] = "committed";
            journal["observedLiveState"] = DigestOperations(operations, useNewDigest: true);
            RecoverablePublisher.WriteDurable(journalPath, CanonicalJson.Encode(journal));
            return Inspect(workspaceRoot)!;
        }

        string constructionIdentity = Required(journal, "constructionIdentity");
        string backupRoot = Path.Combine(workspaceRoot, ".program-kit", "backups", constructionIdentity["sha256:".Length..]);
        foreach (JsonObject operation in operations.Cast<JsonObject>().Reverse())
        {
            string logicalPath = Required(operation, "logicalPath");
            string target = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
            string newDigest = Required(operation, "newDigest");
            string? current = ExactFileDigest(target);
            if (operation["expectedDigest"]?.GetValue<string>() is { } expected)
            {
                string backup = LogicalPaths.ResolveInside(backupRoot, logicalPath);
                string? backupDigest = ExactFileDigest(backup);
                if (string.Equals(current, expected, StringComparison.Ordinal))
                {
                    if (backupDigest is not null && !string.Equals(backupDigest, expected, StringComparison.Ordinal))
                    {
                        throw new IOException("Rollback refused because the retained backup is not exact.");
                    }

                    continue;
                }

                if (!string.Equals(backupDigest, expected, StringComparison.Ordinal)
                    || current is not null && !string.Equals(current, newDigest, StringComparison.Ordinal))
                {
                    throw new IOException("Rollback refused because exact prior bytes cannot be proven.");
                }

                if (File.Exists(target))
                {
                    File.Delete(target);
                }

                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                File.Move(backup, target, overwrite: false);
            }
            else
            {
                if (current is null)
                {
                    continue;
                }

                if (!string.Equals(current, newDigest, StringComparison.Ordinal))
                {
                    throw new IOException("Rollback refused because a created artifact changed after interruption.");
                }

                File.Delete(target);
            }
        }

        journal["state"] = "rolled-back";
        journal["completedOperations"] = new JsonArray();
        journal["observedLiveState"] = DigestOperations(operations, useNewDigest: false);
        RecoverablePublisher.WriteDurable(journalPath, CanonicalJson.Encode(journal));
        return Inspect(workspaceRoot)!;
    }

    private static bool HasExactAdmissionReceipt(string workspaceRoot, JsonObject journal, string journalDigest)
    {
        string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
        if (!File.Exists(receiptPath) || (File.GetAttributes(receiptPath) & FileAttributes.ReparsePoint) != 0)
        {
            return false;
        }

        try
        {
            JsonObject receipt = Read(receiptPath);
            return string.Equals(receipt["schema"]?.GetValue<string>(), "program-kit.construction-receipt/v1", StringComparison.Ordinal)
                && string.Equals(receipt["publicationState"]?.GetValue<string>(), "admitted", StringComparison.Ordinal)
                && string.Equals(receipt["constructionIdentity"]?.GetValue<string>(), Required(journal, "constructionIdentity"), StringComparison.Ordinal)
                && string.Equals(receipt["publicationJournal"]?["digest"]?.GetValue<string>(), journalDigest, StringComparison.Ordinal);
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or System.Text.Json.JsonException)
        {
            return false;
        }
    }

    private static string? ExactFileDigest(string path)
    {
        if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
        {
            return null;
        }

        return Digests.Sha256(File.ReadAllBytes(path));
    }

    private static string DigestOperations(JsonArray operations, bool useNewDigest)
    {
        var entries = operations.Cast<JsonObject>()
            .Select(operation =>
            {
                string? digest = useNewDigest ? operation["newDigest"]?.GetValue<string>() : operation["expectedDigest"]?.GetValue<string>();
                return digest is null ? null : $"{Required(operation, "logicalPath")}:{digest}";
            })
            .Where(static item => item is not null)
            .Cast<string>()
            .OrderBy(static item => item, StringComparer.Ordinal);
        return Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n', entries)));
    }

    private static JsonObject Read(string path) => File.Exists(path)
        ? CanonicalJson.Parse(File.ReadAllBytes(path)) as JsonObject
            ?? throw new InvalidDataException("The publication record must be an object.")
        : throw new FileNotFoundException("The publication record is unavailable.", path);

    private static string Required(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidDataException($"The publication journal field {name} is required.");
}
