using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionOperationResultContractTests
{
    [TestMethod]
    public void Session_results_reuse_the_operation_result_v1_envelope()
    {
        JsonObject payload = new() { ["state"] = "absent", ["provider"] = "codex" };
        OperationResult result = OperationResultFactory.Success(
            PublicCommand.SessionExplain,
            OperationPhase.Explanation,
            EffectState.None,
            session: payload,
            disclosure: new[] { new DisclosureEntry("workspace", DisclosureClassification.RepositoryRelative, "reported") });

        JsonObject projected = OperationResultProjector.ToJson(result);
        Assert.AreEqual("program-kit.operation-result/v1", projected["schema"]!.GetValue<string>());
        Assert.AreEqual("session-explain", projected["command"]!.GetValue<string>());
        Assert.AreEqual("absent", projected["session"]!["state"]!.GetValue<string>());
        Assert.AreEqual("repository-relative", projected["disclosure"]![0]!["classification"]!.GetValue<string>());
    }
}
