using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeProviderParityAcceptanceTests
{
    [TestMethod]
    public void Direct_neutral_Codex_and_Claude_observations_preserve_canonical_meaning()
    {
        SessionSemanticObservation[] observations =
        {
            Observation("direct-cli"),
            Observation("neutral-harness"),
            Observation("codex"),
            Observation("claude-code"),
        };
        SessionProviderConformanceReport report = ClaudeConformanceProfiles.Compare(observations);
        Assert.IsTrue(report.Conforms, string.Join(';', report.Failures));
    }

    private static SessionSemanticObservation Observation(string channel) => new(
        channel, PublicCommand.Construct, OperationOutcome.Succeeded, EffectState.Committed,
        PrimaryDisposition.Complete, "program-kit.operation-result/v1", true, true, true, true);
}
