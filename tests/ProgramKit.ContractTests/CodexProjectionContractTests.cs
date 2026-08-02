using System;
using System.Linq;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class CodexProjectionContractTests
{
    [TestMethod]
    public void Codex_projection_is_a_whole_generated_owned_repository_skill()
    {
        CodexSessionProviderAdapter adapter = new();
        ProjectedSessionArtifact[] artifacts = adapter.Project(SessionIntegrationFixture.ProjectionContext()).ToArray();
        ProjectedSessionArtifact skill = artifacts.Single(item => item.LogicalPath == ".agents/skills/program-kit/SKILL.md");
        string text = Encoding.UTF8.GetString(skill.Content);
        StringAssert.StartsWith(text, "---\nname: program-kit\n");
        StringAssert.Contains(text, "program-kit.operation-result/v2");
        StringAssert.Contains(text, "request-bound");
        Assert.IsFalse(text.Contains("Spec Kit", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(text.Contains("MCP", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(text.Contains("approval is granted", StringComparison.OrdinalIgnoreCase));
        Assert.AreEqual("workspace", adapter.Manifest.SupportedScopes.Single());
        Assert.AreEqual("1.0.0", adapter.Manifest.Revision);
    }
}
