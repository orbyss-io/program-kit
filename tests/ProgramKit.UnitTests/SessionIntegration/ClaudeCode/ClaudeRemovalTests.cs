using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeRemovalTests
{
    [TestMethod]
    public void Manifest_delegates_only_the_exact_skill_file_to_neutral_removal()
    {
        ClaudeSessionProviderAdapter adapter = new();
        SessionProjectionDescriptor descriptor = adapter.Manifest.ProjectionDescriptors.Single();
        Assert.AreEqual(".claude/skills/program-kit/SKILL.md", descriptor.LogicalPath);
        Assert.AreEqual(ArtifactOwnership.GeneratedOwned, descriptor.Ownership);
        Assert.AreEqual("exact-admitted-digest-only", descriptor.RemovalPolicy);
        Assert.IsFalse(adapter.Manifest.ProjectionDescriptors.Any(static item => item.LogicalPath == ".claude" || item.LogicalPath == ".claude/skills"));
    }

    [TestMethod]
    public void Rejected_dependency_blocks_removal_before_effect_or_ownership_inference()
    {
        ClaudeSessionProviderAdapter adapter = new();
        SessionDiagnosticException exception = Assert.ThrowsExactly<SessionDiagnosticException>(
            () => new SessionProviderRegistry(new[] { adapter }).Resolve(adapter.Manifest.ProviderIdentity));
        Assert.AreEqual("program-kit.session/PKSES0003", exception.DiagnosticId);
        Assert.AreEqual(EffectState.None, exception.EffectState);
    }
}
