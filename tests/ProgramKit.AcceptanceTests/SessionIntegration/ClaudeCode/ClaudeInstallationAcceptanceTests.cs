using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeInstallationAcceptanceTests
{
    [TestMethod]
    public void Rejected_upstream_dependency_blocks_lifecycle_before_any_workspace_effect()
    {
        ClaudeSessionProviderAdapter adapter = new();
        SessionProviderRegistry registry = new(new[] { adapter });
        OperationResult result = SessionFailureBoundary.Execute(
            PublicCommand.SessionExplain,
            () =>
            {
                _ = registry.Resolve(adapter.Manifest.ProviderIdentity);
                return OperationResultFactory.Success(PublicCommand.SessionExplain, OperationPhase.Completion, EffectState.None);
            });

        Assert.AreEqual(OperationOutcome.Blocked, result.Outcome);
        Assert.AreEqual(EffectState.None, result.EffectState);
        Assert.AreEqual(PrimaryDisposition.Revise, result.PrimaryDisposition);
        Assert.AreEqual("program-kit.session/PKSES0003", result.Diagnostics.Items[0].Id);
    }
}
