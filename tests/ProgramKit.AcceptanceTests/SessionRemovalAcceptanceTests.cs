using System.IO;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionRemovalAcceptanceTests
{
    [TestMethod]
    public void Removal_preserves_unrelated_workspace_and_provider_state_byte_for_byte()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        using SessionIntegrationTestWorkspace providerState = SessionIntegrationTestWorkspace.Create();
        workspace.Write(".agents/skills/other/SKILL.md", Encoding.UTF8.GetBytes("consumer skill"));
        workspace.Write("application/source.txt", Encoding.UTF8.GetBytes("consumer source"));
        providerState.Write("global-provider-state.json", Encoding.UTF8.GetBytes("provider global state"));
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        Assert.AreEqual(0, TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json").ExitCode);
        byte[] otherSkill = File.ReadAllBytes(workspace.PathOf(".agents/skills/other/SKILL.md"));
        byte[] source = File.ReadAllBytes(workspace.PathOf("application/source.txt"));
        string providerBefore = TestRepository.DigestTree(providerState.Root);
        string remove = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);

        (int exitCode, string output, _) = TestRepository.RunCli("session", "remove", "--workspace", workspace.Root, "--request", remove, "--format", "json");
        Assert.AreEqual(0, exitCode, output);
        JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException("Expected JSON removal result.");
        Assert.AreEqual("committed", result["effectState"]!.GetValue<string>());
        Assert.AreEqual("removed", result["session"]!["state"]!.GetValue<string>());
        Assert.IsFalse(File.Exists(workspace.PathOf(".agents/skills/program-kit/SKILL.md")));
        CollectionAssert.AreEqual(otherSkill, File.ReadAllBytes(workspace.PathOf(".agents/skills/other/SKILL.md")));
        CollectionAssert.AreEqual(source, File.ReadAllBytes(workspace.PathOf("application/source.txt")));
        Assert.AreEqual(providerBefore, TestRepository.DigestTree(providerState.Root));
    }

    [TestMethod]
    public void Drifted_owned_projection_is_preserved_and_removal_is_blocked()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        Assert.AreEqual(0, TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json").ExitCode);
        File.AppendAllText(workspace.PathOf(".agents/skills/program-kit/SKILL.md"), "\nconsumer change");
        string remove = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        string before = TestRepository.DigestTree(workspace.Root);

        (int exitCode, string output, _) = TestRepository.RunCli("session", "remove", "--workspace", workspace.Root, "--request", remove, "--format", "json");
        Assert.AreEqual(3, exitCode, output);
        Assert.AreEqual("program-kit.session/PKSES0004", JsonNode.Parse(output)!["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.AreEqual(before, TestRepository.DigestTree(workspace.Root));
    }
}
