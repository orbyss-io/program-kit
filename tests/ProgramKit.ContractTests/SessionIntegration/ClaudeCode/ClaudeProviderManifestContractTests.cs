using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeProviderManifestContractTests
{
    [TestMethod]
    public void Manifest_closes_over_one_exact_fail_closed_project_skill_surface()
    {
        SessionProviderManifest manifest = new ClaudeProviderManifestLoader().LoadEmbedded();
        Assert.AreEqual("anthropic", manifest.ProviderIdentity.Authority);
        Assert.AreEqual("claude-code", manifest.ProviderIdentity.Name);
        Assert.AreEqual("2.1.220", manifest.ProviderIdentity.Revision);
        Assert.AreEqual("claude-code-project-skill", manifest.AdapterIdentity.Name);
        Assert.AreEqual("2.1.220", manifest.ProviderSurface.TestedVersions.Single());
        Assert.AreEqual("project-skill", manifest.ProviderSurface.SurfaceName);
        Assert.AreEqual("workspace", manifest.SupportedScopes.Single());
        Assert.AreEqual(".claude/skills/program-kit/SKILL.md", manifest.ProjectionDescriptors.Single().LogicalPath);
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, manifest.SupportClaim);
        CollectionAssert.AreEqual(
            new[] { "explain", "construct", "evaluate", "session-explain", "session-install", "session-verify", "session-remove" },
            manifest.RequiredCliOperations.ToArray());
    }
}
