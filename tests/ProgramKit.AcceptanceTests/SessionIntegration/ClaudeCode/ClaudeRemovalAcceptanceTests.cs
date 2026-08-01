using System.IO;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeRemovalAcceptanceTests
{
    [TestMethod]
    public void Blocked_adapter_cannot_remove_consumer_Claude_state_or_independent_tools()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        workspace.Write(".claude/settings.json", Encoding.UTF8.GetBytes("{}"));
        workspace.Write(".claude/skills/other/SKILL.md", Encoding.UTF8.GetBytes("consumer skill"));
        workspace.Write(".program-kit/tools/program-kit", Encoding.UTF8.GetBytes("independent tool"));
        string before = TestRepository.DigestTree(workspace.Root);
        ClaudeSessionProviderAdapter adapter = new();

        _ = Assert.ThrowsExactly<SessionDiagnosticException>(
            () => new SessionProviderRegistry(new[] { adapter }).Resolve(adapter.Manifest.ProviderIdentity));

        Assert.AreEqual(before, TestRepository.DigestTree(workspace.Root));
        Assert.IsTrue(File.Exists(workspace.PathOf(".claude/settings.json")));
        Assert.IsTrue(File.Exists(workspace.PathOf(".claude/skills/other/SKILL.md")));
        Assert.IsTrue(File.Exists(workspace.PathOf(".program-kit/tools/program-kit")));
    }
}
