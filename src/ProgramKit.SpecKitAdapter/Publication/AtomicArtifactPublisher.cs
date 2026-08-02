using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public interface IPublicationObserver
{
    void BeforePublish(string logicalPath, int index);
}

public sealed class NullPublicationObserver : IPublicationObserver
{
    public void BeforePublish(string logicalPath, int index) { }
}

public sealed record PublicationResult(IReadOnlyDictionary<string, string> Digests, bool Changed);

public sealed class AdapterPublicationException : IOException
{
    public AdapterPublicationException(string message) : base(message) { }
}

public sealed class AtomicArtifactPublisher
{
    private readonly IPublicationObserver observer;

    public AtomicArtifactPublisher(IPublicationObserver? observer = null)
    {
        this.observer = observer ?? new NullPublicationObserver();
    }

    public PublicationResult Publish(
        string workspaceRoot,
        IReadOnlyDictionary<string, byte[]> outputs,
        IReadOnlyDictionary<string, string>? expectedCurrentDigests = null,
        string? trustMarkerLogicalPath = null)
    {
        LogicalPathPolicy.ValidateDistinct(outputs.Keys);
        if (trustMarkerLogicalPath is not null && !outputs.ContainsKey(trustMarkerLogicalPath))
            throw new ArgumentException("The trust marker must be one of the published outputs.", nameof(trustMarkerLogicalPath));
        expectedCurrentDigests ??= new Dictionary<string, string>(StringComparer.Ordinal);
        string[] paths = outputs.Keys
            .OrderBy(path => string.Equals(path, trustMarkerLogicalPath, StringComparison.Ordinal) ? 1 : 0)
            .ThenBy(static path => path, StringComparer.Ordinal)
            .ToArray();
        Dictionary<string, string> digests = outputs.ToDictionary(static item => item.Key, static item => Digest(item.Value), StringComparer.Ordinal);
        bool allExact = true;
        foreach (string logicalPath in paths)
        {
            string destination = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
            if (!File.Exists(destination) || !string.Equals(Digest(File.ReadAllBytes(destination)), digests[logicalPath], StringComparison.Ordinal)) allExact = false;
            if (File.Exists(destination) && !string.Equals(Digest(File.ReadAllBytes(destination)), digests[logicalPath], StringComparison.Ordinal))
            {
                if (!expectedCurrentDigests.TryGetValue(logicalPath, out string? expected) || !string.Equals(Digest(File.ReadAllBytes(destination)), expected, StringComparison.Ordinal))
                    throw new AdapterPublicationException($"Refusing unproven overwrite: {logicalPath}");
            }
        }

        if (allExact) return new PublicationResult(digests, Changed: false);

        string stagingRoot = Path.Combine(Path.GetFullPath(workspaceRoot), ".program-kit", "adapter-staging", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(stagingRoot);
        List<(string Destination, string? Backup)> published = new();
        try
        {
            JsonArray journalEntries = new();
            foreach (string logicalPath in paths)
            {
                string staged = Path.Combine(stagingRoot, logicalPath.Replace('/', Path.DirectorySeparatorChar));
                Directory.CreateDirectory(Path.GetDirectoryName(staged)!);
                File.WriteAllBytes(staged, outputs[logicalPath]);
                string destination = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
                JsonObject entry = new()
                {
                    ["logicalPath"] = logicalPath,
                    ["outputDigest"] = digests[logicalPath],
                };
                if (File.Exists(destination))
                {
                    entry["priorDigest"] = Digest(File.ReadAllBytes(destination));
                    entry["backupName"] = $"backup-{journalEntries.Count:D4}";
                }
                journalEntries.Add(entry);
            }
            JsonObject journal = new()
            {
                ["schema"] = "program-kit.spec-kit-adapter-publication-staging/v1",
                ["ownership"] = "adapter-generated-owned",
                ["trustMarker"] = trustMarkerLogicalPath,
                ["entries"] = journalEntries,
            };
            File.WriteAllBytes(Path.Combine(stagingRoot, "staging-state.json"), CanonicalDocument.Encode(journal));

            for (int index = 0; index < paths.Length; index++)
            {
                string logicalPath = paths[index];
                observer.BeforePublish(logicalPath, index);
                string destination = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
                if (File.Exists(destination) && string.Equals(Digest(File.ReadAllBytes(destination)), digests[logicalPath], StringComparison.Ordinal)) continue;
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                string? backup = null;
                if (File.Exists(destination))
                {
                    string backupName = journalEntries[index]!["backupName"]!.GetValue<string>();
                    backup = Path.Combine(stagingRoot, backupName);
                    File.Move(destination, backup);
                }

                string staged = Path.Combine(stagingRoot, logicalPath.Replace('/', Path.DirectorySeparatorChar));
                File.Move(staged, destination);
                published.Add((destination, backup));
            }

            return new PublicationResult(digests, Changed: true);
        }
        catch
        {
            foreach ((string destination, string? backup) in published.AsEnumerable().Reverse())
            {
                if (File.Exists(destination)) File.Delete(destination);
                if (backup is not null && File.Exists(backup)) File.Move(backup, destination);
            }

            throw;
        }
        finally
        {
            if (Directory.Exists(stagingRoot)) Directory.Delete(stagingRoot, recursive: true);
        }
    }

    private static string Digest(byte[] bytes) => "sha256:" + Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
}
