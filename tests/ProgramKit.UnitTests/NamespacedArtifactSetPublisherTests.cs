using System;
using System.IO;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Artifacts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class NamespacedArtifactSetPublisherTests
{
    [TestMethod]
    public void Publication_preserves_exact_bytes_and_rejects_collisions_and_stale_staging()
    {
        string root = TestRepository.CreateEmptyWorkspace();
        try
        {
            byte[] expected = Encoding.UTF8.GetBytes("exact\r\nbytes\n");
            NamespacedArtifactSetPublisher publisher = new();
            publisher.Publish(root, "session-integrations/codex", "tx-001", new[] { new NamespacedArtifact(".agents/skills/program-kit/SKILL.md", expected) });
            CollectionAssert.AreEqual(expected, File.ReadAllBytes(Path.Combine(root, ".agents", "skills", "program-kit", "SKILL.md")));

            Assert.ThrowsExactly<IOException>(() => publisher.Publish(root, "session-integrations/codex", "tx-002", new[] { new NamespacedArtifact(".agents/skills/program-kit/SKILL.md", Encoding.UTF8.GetBytes("changed")) }));
            Directory.CreateDirectory(Path.Combine(root, ".program-kit", "session-integrations", "other", "staging", "stale"));
            Assert.ThrowsExactly<InvalidOperationException>(() => publisher.Publish(root, "session-integrations/other", "tx-003", new[] { new NamespacedArtifact("other.txt", expected) }));
        }
        finally { TestRepository.DeleteWorkspace(root); }
    }

    [TestMethod]
    public void Interrupted_publication_rolls_back_all_new_live_artifacts()
    {
        string root = TestRepository.CreateEmptyWorkspace();
        try
        {
            NamespacedArtifactSetPublisher publisher = new(new InterruptAfterFirstArtifact());
            Assert.ThrowsExactly<InjectedPublicationException>(() => publisher.Publish(root, "session-integrations/codex", "tx-rollback", new[]
            {
                new NamespacedArtifact("one.txt", Encoding.UTF8.GetBytes("one")),
                new NamespacedArtifact("two.txt", Encoding.UTF8.GetBytes("two")),
            }));
            Assert.IsFalse(File.Exists(Path.Combine(root, "one.txt")));
            Assert.IsFalse(File.Exists(Path.Combine(root, "two.txt")));
            string journal = File.ReadAllText(Path.Combine(root, ".program-kit", "session-integrations", "codex", "publication.journal.json"));
            StringAssert.Contains(journal, "rolled-back");
        }
        finally { TestRepository.DeleteWorkspace(root); }
    }

    private sealed class InjectedPublicationException : Exception;

    private sealed class InterruptAfterFirstArtifact : IArtifactPublicationObserver
    {
        public void Published(int completedCount, string logicalPath)
        {
            if (completedCount == 1) throw new InjectedPublicationException();
        }
    }
}
