using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterCleanupTests
{
    private const string Feature = "cleanup-feature";
    private const string Root = "specs/cleanup-feature/program-kit/generated";

    [TestMethod]
    public void Cleanup_removes_only_exact_manifest_proven_regenerable_candidates()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            string candidate = $"{Root}/definitions/model.json";
            string result = $"{Root}/results/prepare.json";
            string differentlyOwned = $"{Root}/definitions/consumer.json";
            Write(workspace, candidate, "candidate");
            Write(workspace, result, "retained result");
            Write(workspace, differentlyOwned, "consumer");
            Write(workspace, $"{Root}/unknown.txt", "unknown");
            Write(workspace, "specs/cleanup-feature/program-kit/handoff.yaml", "handoff");
            Write(workspace, ".program-kit/state.json", "program-kit state");
            WriteManifest(workspace,
                Output(candidate, "candidate", "adapter-generated-owned", "regenerable-candidate"),
                Output(result, "retained result", "adapter-generated-owned", "retained-evidence"),
                Output(differentlyOwned, "consumer", "consumer-owned", "regenerable-candidate"));

            JsonObject request = Request();
            JsonObject cleanup = CleanupCommand.Execute(workspace, request);
            Assert.AreEqual("succeeded", cleanup["outcome"]!.GetValue<string>());
            Assert.AreEqual("adapter-files-only", cleanup["effectState"]!.GetValue<string>());
            CollectionAssert.AreEqual(new[] { candidate }, cleanup["payload"]!["removed"]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray());
            Assert.IsFalse(File.Exists(PathOf(workspace, candidate)));
            Assert.AreEqual("retained result", File.ReadAllText(PathOf(workspace, result)));
            Assert.AreEqual("consumer", File.ReadAllText(PathOf(workspace, differentlyOwned)));
            Assert.AreEqual("unknown", File.ReadAllText(PathOf(workspace, $"{Root}/unknown.txt")));
            Assert.AreEqual("handoff", File.ReadAllText(PathOf(workspace, "specs/cleanup-feature/program-kit/handoff.yaml")));
            Assert.AreEqual("program-kit state", File.ReadAllText(PathOf(workspace, ".program-kit/state.json")));
            JsonObject manifest = ReadManifest(workspace);
            Assert.AreEqual("removed", manifest["outputs"]!.AsArray().OfType<JsonObject>().Single(output => output["logicalPath"]!.GetValue<string>() == candidate)["state"]!.GetValue<string>());
            AssertManifestDigest(manifest);

            string beforeRepeat = TestRepository.DigestTree(workspace);
            JsonObject repeated = CleanupCommand.Execute(workspace, request);
            Assert.AreEqual(false, repeated["payload"]!["changed"]!.GetValue<bool>());
            Assert.AreEqual("none", repeated["effectState"]!.GetValue<string>());
            Assert.AreEqual(beforeRepeat, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Cleanup_refuses_drift_escape_and_case_collision_before_any_change()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            string candidate = $"{Root}/definitions/model.json";
            Write(workspace, candidate, "drifted");
            WriteManifest(workspace, Output(candidate, "expected", "adapter-generated-owned", "regenerable-candidate"));
            string before = TestRepository.DigestTree(workspace);
            Assert.ThrowsExactly<AdapterPublicationException>(() => new AdapterCleanupService().Cleanup(workspace, Feature, Root));
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));

            WriteManifest(workspace, Output("src/consumer.cs", "consumer", "adapter-generated-owned", "regenerable-candidate"));
            before = TestRepository.DigestTree(workspace);
            Assert.ThrowsExactly<AdapterPublicationException>(() => new AdapterCleanupService().Cleanup(workspace, Feature, Root));
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));

            WriteManifest(workspace,
                Output($"{Root}/A.json", "a", "adapter-generated-owned", "retained-evidence"),
                Output($"{Root}/a.json", "b", "adapter-generated-owned", "retained-evidence"));
            before = TestRepository.DigestTree(workspace);
            Assert.ThrowsExactly<InvalidDataException>(() => new AdapterCleanupService().Cleanup(workspace, Feature, Root));
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static JsonObject Request() => new()
    {
        ["feature"] = new JsonObject { ["key"] = Feature },
        ["outputRoot"] = Root,
    };

    private static JsonObject Output(string logicalPath, string content, string ownership, string retention) => new()
    {
        ["logicalPath"] = logicalPath,
        ["digest"] = Digest(content),
        ["ownership"] = ownership,
        ["retention"] = retention,
        ["state"] = "current",
    };

    private static void WriteManifest(string workspace, params JsonObject[] outputs)
    {
        JsonObject manifest = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-manifest/v1",
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = new JsonObject(),
            ["feature"] = new JsonObject { ["key"] = Feature },
            ["inputs"] = new JsonArray(),
            ["outputs"] = new JsonArray(outputs),
            ["ownership"] = "adapter-generated-owned",
            ["invalidationSets"] = new JsonObject(),
        };
        manifest["digest"] = CanonicalDocument.Digest(manifest);
        Write(workspace, $"{Root}/adapter-manifest.json", Encoding.UTF8.GetString(CanonicalDocument.Encode(manifest)));
    }

    private static JsonObject ReadManifest(string workspace) => CanonicalDocument.Parse(File.ReadAllBytes(PathOf(workspace, $"{Root}/adapter-manifest.json"))).AsObject();

    private static void AssertManifestDigest(JsonObject manifest)
    {
        string digest = manifest["digest"]!.GetValue<string>();
        JsonObject material = (JsonObject)manifest.DeepClone();
        material.Remove("digest");
        Assert.AreEqual(digest, CanonicalDocument.Digest(material));
    }

    private static void Write(string workspace, string logicalPath, string content)
    {
        string path = PathOf(workspace, logicalPath);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, content);
    }

    private static string PathOf(string workspace, string logicalPath) => Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));

    private static string Digest(string value) => "sha256:" + Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();
}
