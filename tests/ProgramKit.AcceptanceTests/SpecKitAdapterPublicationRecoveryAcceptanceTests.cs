using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterPublicationRecoveryAcceptanceTests
{
    [TestMethod]
    public void Interrupted_set_restores_prior_bytes_and_never_publishes_the_trust_marker_early()
    {
        string workspace = CreateWorkspace();
        try
        {
            string artifactPath = LogicalPathPolicy.Resolve(workspace, "generated/artifact.json");
            string manifestPath = LogicalPathPolicy.Resolve(workspace, "generated/adapter-manifest.json");
            Directory.CreateDirectory(Path.GetDirectoryName(artifactPath)!);
            File.WriteAllText(artifactPath, "old-artifact");
            File.WriteAllText(manifestPath, "old-manifest");
            Dictionary<string, string> expected = new(StringComparer.Ordinal)
            {
                ["generated/artifact.json"] = Digest("old-artifact"),
                ["generated/adapter-manifest.json"] = Digest("old-manifest"),
            };
            RecordingInterruption observer = new("generated/adapter-manifest.json");
            AtomicArtifactPublisher publisher = new(observer);
            Assert.ThrowsExactly<InvalidOperationException>(() => publisher.Publish(
                workspace,
                new Dictionary<string, byte[]>
                {
                    ["generated/adapter-manifest.json"] = Encoding.UTF8.GetBytes("new-manifest"),
                    ["generated/artifact.json"] = Encoding.UTF8.GetBytes("new-artifact"),
                },
                expected,
                "generated/adapter-manifest.json"));
            CollectionAssert.AreEqual(new[] { "generated/artifact.json", "generated/adapter-manifest.json" }, observer.Paths.ToArray());
            Assert.AreEqual("old-artifact", File.ReadAllText(artifactPath));
            Assert.AreEqual("old-manifest", File.ReadAllText(manifestPath));
            Assert.AreEqual(0, new AdapterPublicationRecovery().Inspect(workspace).Count);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public void Recovery_rolls_back_only_proven_staged_bytes_and_refuses_later_drift()
    {
        string workspace = CreateWorkspace();
        try
        {
            CreateInterruptedTransaction(workspace, "recoverable", driftDestination: false);
            AdapterPublicationRecovery recovery = new();
            AdapterPublicationRecoveryState state = recovery.Inspect(workspace).Single();
            recovery.Rollback(workspace, state);
            Assert.AreEqual("old", File.ReadAllText(LogicalPathPolicy.Resolve(workspace, "generated/existing.json")));
            Assert.IsFalse(File.Exists(LogicalPathPolicy.Resolve(workspace, "generated/new.json")));
            Assert.AreEqual(0, recovery.Inspect(workspace).Count);

            CreateInterruptedTransaction(workspace, "drifted", driftDestination: true);
            state = recovery.Inspect(workspace).Single();
            Assert.ThrowsExactly<AdapterPublicationException>(() => recovery.Rollback(workspace, state));
            Assert.AreEqual("differently-owned", File.ReadAllText(LogicalPathPolicy.Resolve(workspace, "generated/existing.json")));
            Assert.AreEqual("new-only", File.ReadAllText(LogicalPathPolicy.Resolve(workspace, "generated/new.json")));
            Assert.AreEqual(1, recovery.Inspect(workspace).Count);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public void Publication_refuses_unproven_overwrite_case_collision_and_untrusted_staging()
    {
        string workspace = CreateWorkspace();
        try
        {
            string owned = LogicalPathPolicy.Resolve(workspace, "generated/owned.json");
            Directory.CreateDirectory(Path.GetDirectoryName(owned)!);
            File.WriteAllText(owned, "consumer-owned");
            AtomicArtifactPublisher publisher = new();
            Assert.ThrowsExactly<AdapterPublicationException>(() => publisher.Publish(
                workspace,
                new Dictionary<string, byte[]> { ["generated/owned.json"] = Encoding.UTF8.GetBytes("adapter") }));
            Assert.AreEqual("consumer-owned", File.ReadAllText(owned));
            Assert.ThrowsExactly<InvalidDataException>(() => publisher.Publish(
                workspace,
                new Dictionary<string, byte[]>
                {
                    ["generated/A.json"] = Encoding.UTF8.GetBytes("a"),
                    ["generated/a.json"] = Encoding.UTF8.GetBytes("b"),
                }));

            string unknown = Path.Combine(workspace, ".program-kit", "adapter-staging", "unknown");
            Directory.CreateDirectory(unknown);
            File.WriteAllText(Path.Combine(unknown, "foreign.txt"), "not adapter-owned");
            Assert.ThrowsExactly<AdapterPublicationException>(() => new AdapterPublicationRecovery().Inspect(workspace));
            Assert.IsTrue(File.Exists(Path.Combine(unknown, "foreign.txt")));
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    private static void CreateInterruptedTransaction(string workspace, string name, bool driftDestination)
    {
        string transaction = Path.Combine(workspace, ".program-kit", "adapter-staging", name);
        Directory.CreateDirectory(transaction);
        string existing = LogicalPathPolicy.Resolve(workspace, "generated/existing.json");
        string added = LogicalPathPolicy.Resolve(workspace, "generated/new.json");
        Directory.CreateDirectory(Path.GetDirectoryName(existing)!);
        File.WriteAllText(existing, driftDestination ? "differently-owned" : "new");
        File.WriteAllText(added, "new-only");
        File.WriteAllText(Path.Combine(transaction, "backup-0000"), "old");
        JsonObject journal = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-publication-staging/v1",
            ["ownership"] = "adapter-generated-owned",
            ["trustMarker"] = "generated/adapter-manifest.json",
            ["entries"] = new JsonArray(
                new JsonObject
                {
                    ["logicalPath"] = "generated/existing.json",
                    ["outputDigest"] = Digest("new"),
                    ["priorDigest"] = Digest("old"),
                    ["backupName"] = "backup-0000",
                },
                new JsonObject
                {
                    ["logicalPath"] = "generated/new.json",
                    ["outputDigest"] = Digest("new-only"),
                }),
        };
        File.WriteAllBytes(Path.Combine(transaction, "staging-state.json"), CanonicalDocument.Encode(journal));
    }

    private static string CreateWorkspace()
    {
        string workspace = Path.Combine(Path.GetTempPath(), $"program-kit-adapter-publication-{Guid.NewGuid():N}");
        Directory.CreateDirectory(workspace);
        return workspace;
    }

    private static string Digest(string value) => "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();

    private sealed class RecordingInterruption : IPublicationObserver
    {
        private readonly string interruptAt;

        public RecordingInterruption(string interruptAt)
        {
            this.interruptAt = interruptAt;
        }

        public List<string> Paths { get; } = new();

        public void BeforePublish(string logicalPath, int index)
        {
            Paths.Add(logicalPath);
            if (logicalPath == interruptAt) throw new InvalidOperationException("simulated interruption");
        }
    }
}
