using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterBoundaryTests
{
    [TestMethod]
    public void Logical_paths_reject_rooting_traversal_backslashes_and_case_collisions()
    {
        string root = CreateRoot();
        try
        {
            Assert.ThrowsExactly<InvalidDataException>(() => LogicalPathPolicy.Resolve(root, "../escape"));
            Assert.ThrowsExactly<InvalidDataException>(() => LogicalPathPolicy.Resolve(root, "C:/escape"));
            Assert.ThrowsExactly<InvalidDataException>(() => LogicalPathPolicy.Resolve(root, "C:escape"));
            Assert.ThrowsExactly<InvalidDataException>(() => LogicalPathPolicy.Resolve(root, "a\\b"));
            Assert.ThrowsExactly<InvalidDataException>(() => LogicalPathPolicy.ValidateDistinct(new[] { "A/file.json", "a/file.json" }));
            StringAssert.StartsWith(LogicalPathPolicy.Resolve(root, "safe/file.json"), Path.GetFullPath(root));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void Existing_reparse_path_is_rejected_when_the_platform_can_create_it()
    {
        string root = CreateRoot();
        string outside = CreateRoot();
        try
        {
            string link = Path.Combine(root, "link");
            try
            {
                Directory.CreateSymbolicLink(link, outside);
            }
            catch (UnauthorizedAccessException)
            {
                return;
            }
            catch (PlatformNotSupportedException)
            {
                return;
            }

            Assert.ThrowsExactly<InvalidDataException>(() => LogicalPathPolicy.Resolve(root, "link/file.json"));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
            if (Directory.Exists(outside)) Directory.Delete(outside, recursive: true);
        }
    }

    [TestMethod]
    public void Process_client_uses_an_exact_argument_vector_with_shell_disabled()
    {
        const string opaque = "value;$(touch should-not-run)|&secret";
        ProgramKitProcessRequest request = new("program-kit", new[] { "construct", "--request", opaque }, Environment.CurrentDirectory, TimeSpan.FromSeconds(1));
        ProcessStartInfo start = ProgramKitProcessClient.CreateStartInfo(request);
        Assert.IsFalse(start.UseShellExecute);
        Assert.IsTrue(start.RedirectStandardOutput);
        Assert.IsTrue(start.RedirectStandardError);
        Assert.AreEqual(opaque, start.ArgumentList[2]);
    }

    [TestMethod]
    public async Task Process_client_enforces_timeout_and_cancellation()
    {
        ProgramKitProcessClient client = new();
        ProgramKitProcessRequest request = new("pwsh", new[] { "-NoProfile", "-Command", "Start-Sleep -Seconds 10" }, Environment.CurrentDirectory, TimeSpan.FromMilliseconds(100));
        await Assert.ThrowsAsync<OperationCanceledException>(() => client.RunAsync(request, CancellationToken.None));
    }

    [TestMethod]
    public void Restricted_yaml_has_canonical_order_and_rejects_executable_features()
    {
        string first = CanonicalDocument.Digest(RestrictedYaml.Parse("z: 2\na: 1\n"));
        string second = CanonicalDocument.Digest(RestrictedYaml.Parse("a: 1\nz: 2\n"));
        Assert.AreEqual(first, second);
        Assert.ThrowsExactly<InvalidDataException>(() => RestrictedYaml.Parse("a: &anchor value\nb: *anchor\n"));
        Assert.ThrowsExactly<InvalidDataException>(() => RestrictedYaml.Parse("a: ${SECRET}\n"));
    }

    [TestMethod]
    public void Publication_refuses_drift_before_writes_and_rolls_back_interruption()
    {
        string root = CreateRoot();
        try
        {
            string existing = LogicalPathPolicy.Resolve(root, "generated/existing.json");
            Directory.CreateDirectory(Path.GetDirectoryName(existing)!);
            File.WriteAllText(existing, "consumer-owned");
            AtomicArtifactPublisher publisher = new();
            Assert.ThrowsExactly<AdapterPublicationException>(() => publisher.Publish(root, new Dictionary<string, byte[]> { ["generated/existing.json"] = Encoding.UTF8.GetBytes("new") }));
            Assert.AreEqual("consumer-owned", File.ReadAllText(existing));

            AtomicArtifactPublisher interrupted = new(new ThrowOnSecondPublication());
            Assert.ThrowsExactly<InvalidOperationException>(() => interrupted.Publish(root, new Dictionary<string, byte[]>
            {
                ["generated/a.json"] = Encoding.UTF8.GetBytes("a"),
                ["generated/b.json"] = Encoding.UTF8.GetBytes("b"),
            }));
            Assert.IsFalse(File.Exists(Path.Combine(root, "generated", "a.json")));
            Assert.IsFalse(File.Exists(Path.Combine(root, "generated", "b.json")));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static string CreateRoot()
    {
        string root = Path.Combine(Path.GetTempPath(), $"program-kit-adapter-boundary-{Guid.NewGuid():N}");
        Directory.CreateDirectory(root);
        return root;
    }

    private sealed class ThrowOnSecondPublication : IPublicationObserver
    {
        public void BeforePublish(string logicalPath, int index)
        {
            if (index == 1) throw new InvalidOperationException("Simulated interruption.");
        }
    }
}
