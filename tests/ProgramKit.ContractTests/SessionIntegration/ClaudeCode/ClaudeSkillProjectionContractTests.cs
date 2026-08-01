using System;
using System.Linq;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeSkillProjectionContractTests
{
    [TestMethod]
    public void Projection_is_one_byte_stable_bounded_project_skill()
    {
        ClaudeSessionProviderAdapter adapter = new();
        SessionProjectionContext context = ClaudeTestContext.Create(adapter.Manifest);
        ProjectedSessionArtifact first = adapter.Project(context).Single();
        ProjectedSessionArtifact second = adapter.Project(context with { IncludeUserInterfaceMetadata = true }).Single();

        Assert.AreEqual(".claude/skills/program-kit/SKILL.md", first.LogicalPath);
        CollectionAssert.AreEqual(first.Content, second.Content);
        string text = Encoding.UTF8.GetString(first.Content);
        StringAssert.StartsWith(text, "---\nname: program-kit\ndescription: Use Program Kit to explain, construct, and evaluate contract-bounded software when the user asks to design or build software through Program Kit or needs help resolving Program Kit diagnostics.\n---\n");
        Assert.IsFalse(text.Contains('\r'));
        Assert.IsFalse(text.Contains("allowed-tools", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(text.Contains("disallowed-tools", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(text.Contains("CLAUDE.md", StringComparison.Ordinal));
        Assert.IsFalse(text.Contains(".claude/settings", StringComparison.Ordinal));
        StringAssert.Contains(text, "program-kit.operation-result/v1");
        StringAssert.Contains(text, "authority=request-bound");
        StringAssert.Contains(text, "disclosure=classified");
        StringAssert.Contains(text, "normalization=canonical-json");
        StringAssert.Contains(text, "fresh-session=separately-classified");
    }
}
